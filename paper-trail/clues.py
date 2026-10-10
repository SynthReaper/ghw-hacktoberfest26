import json
import re
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

from facts import FactRecord

RUNS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
os.makedirs(RUNS_DIR, exist_ok=True)

SENSORY_MODALITIES = ["look", "listen", "count", "touch", "sketch"]

@dataclass
class ClueResult:
    waypoint_index: int
    modality: str
    direction_line: str
    observation_prompt: str
    is_valid: bool
    rejection_reasons: List[str]
    retries_used: int
    used_fallback: bool
    raw_response: str
    latency_ms: int

class ClueValidator:
    """
    Validates that the observation prompt and walking directions
    do NOT hallucinate unverified proper nouns, numbers, or species
    beyond the ground-truth fact record.
    """
    def __init__(self):
        # Known common english words and directional tokens that are capitalized at sentence start or in navigation
        self.common_stop_words = {
            "The", "Look", "Walk", "Find", "Notice", "Count", "Listen", "Feel",
            "Sketch", "Touch", "Stand", "Head", "Stop", "Observe", "Check", "Take",
            "Follow", "Near", "Toward", "Past", "At", "In", "On", "Here", "Around",
            "North", "South", "East", "West", "Meters", "Steps", "A", "An", "You",
            "N", "S", "E", "W", "NE", "NW", "SE", "SW", "NNE", "NNW", "SSE", "SSW",
            "ENE", "ESE", "WNW", "WSW"
        }

    def validate(self, prompt_text: str, direction_text: str, fact: FactRecord) -> Tuple[bool, List[str]]:
        reasons = []

        combined_text = f"{direction_text} {prompt_text}"

        # 1. Check for unverified proper nouns (capitalized words that aren't in stop words or fact name/tags)
        allowed_proper_nouns = set(self.common_stop_words)
        if fact.name:
            for token in re.findall(r"\b[A-Za-z]+\b", fact.name):
                allowed_proper_nouns.add(token.capitalize())
        for tag_val in fact.key_tags.values():
            for token in re.findall(r"\b[A-Za-z]+\b", str(tag_val)):
                allowed_proper_nouns.add(token.capitalize())

        # Find capitalized words inside sentences (not the very first word of each sentence)
        sentences = re.split(r"[.!?]\s+", combined_text)
        for s in sentences:
            words = re.findall(r"\b[A-Za-z]+\b", s)
            for w in words[1:]:  # skip initial word
                if w[0].isupper() and w not in allowed_proper_nouns:
                    reasons.append(f"Unverified proper noun hallucination: '{w}'")

        # 2. Check for invented numbers in observation prompt
        # Numbers are only allowed in direction_text (meters/compass) unless verified in tags
        prompt_numbers = re.findall(r"\b\d+\b", prompt_text)
        allowed_numbers = set()
        for tag_val in fact.key_tags.values():
            allowed_numbers.update(re.findall(r"\b\d+\b", str(tag_val)))

        for num in prompt_numbers:
            # Small counting numbers for count prompts are allowed if <= 10 (e.g. "count 3 benches")
            if int(num) > 10 and num not in allowed_numbers:
                reasons.append(f"Invented numerical claim in observation: '{num}'")

        # 3. Check for invented biological species if not in tags
        species_keywords = ["oak", "banyan", "pine", "neem", "peepal", "gulmohar", "maple", "birch", "willow"]
        fact_text_lower = (fact.name + " " + " ".join(fact.key_tags.values())).lower()
        for sp in species_keywords:
            if re.search(r"\b" + sp + r"\b", combined_text, re.IGNORECASE):
                if sp not in fact_text_lower:
                    reasons.append(f"Invented botanical species: '{sp}' not found in OSM tags")

        # 4. Length constraint check
        word_count = len(prompt_text.split())
        if word_count > 30:
            reasons.append(f"Observation prompt exceeded maximum length ({word_count} words > 30)")

        is_valid = len(reasons) == 0
        return is_valid, reasons

def build_fallback_clue(fact: FactRecord, modality: str) -> Dict[str, str]:
    """Deterministically grounded fallback template if LLM fails or is unavailable."""
    dir_line = f"Head {fact.compass} approximately {fact.distance_from_prev_m}m."
    feat = fact.name if fact.name else f"the {fact.category.replace('_', ' ')}"

    templates = {
        "look": f"Look toward {feat}. Notice the patterns, contrast, and materials shaping its boundary.",
        "listen": f"Pause near {feat}. Close your eyes for 30 seconds and separate natural sounds from vehicle hum.",
        "count": f"At {feat}, count how many distinct textures or structural segments you can distinguish.",
        "touch": f"Approach {feat}. Notice the surface temperature and roughness compared to the surrounding pavement.",
        "sketch": f"Stop before {feat}. In the field box below, draw a 30-second continuous line contour of its silhouette."
    }
    return {
        "direction_line": dir_line,
        "observation_prompt": templates.get(modality, templates["look"])
    }

def call_ollama(prompt: str, model: str = "gemma:2b", timeout: int = 15) -> Optional[str]:
    """Attempts to call local Ollama server if running."""
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 120}
            },
            timeout=timeout
        )
        if resp.status_code == 200:
            return resp.json().get("response")
    except Exception:
        return None
    return None

def generate_clue_for_waypoint(
    fact: FactRecord,
    modality_idx: int,
    ollama_model: Optional[str] = "gemma:2b",
    validator: Optional[ClueValidator] = None
) -> ClueResult:
    if validator is None:
        validator = ClueValidator()

    modality = SENSORY_MODALITIES[modality_idx % len(SENSORY_MODALITIES)]
    context = fact.to_prompt_context()

    prompt_instruction = f"""
You are Paper Trail's field naturalist generator. Write one walking observation clue.
Strict rules:
1. ONLY reference facts in this record: {json.dumps(context)}
2. Modality: '{modality.upper()}'.
3. Do NOT invent proper names, species, or numbers not present.
4. Keep observation prompt under 25 words.
Return strictly valid JSON:
{{"direction_line": "...", "observation_prompt": "..."}}
"""

    max_retries = 3
    rejection_reasons = []
    used_fallback = False
    raw_response = ""
    start_time = time.time()

    for attempt in range(max_retries):
        raw_response = call_ollama(prompt_instruction, model=ollama_model or "gemma:2b")
        if not raw_response:
            # Ollama not running or timed out -> use grounded deterministic generation
            used_fallback = True
            fallback = build_fallback_clue(fact, modality)
            dir_line = fallback["direction_line"]
            obs_prompt = fallback["observation_prompt"]
            break

        # Parse JSON
        try:
            parsed = json.loads(raw_response)
            dir_line = parsed.get("direction_line", "").strip()
            obs_prompt = parsed.get("observation_prompt", "").strip()
        except Exception:
            rejection_reasons.append(f"Attempt {attempt + 1}: Malformed JSON output")
            continue

        # Run strict validator
        valid, reasons = validator.validate(obs_prompt, dir_line, fact)
        if valid:
            latency = int((time.time() - start_time) * 1000)
            return ClueResult(
                waypoint_index=fact.waypoint_index,
                modality=modality,
                direction_line=dir_line,
                observation_prompt=obs_prompt,
                is_valid=True,
                rejection_reasons=[],
                retries_used=attempt,
                used_fallback=False,
                raw_response=raw_response,
                latency_ms=latency
            )
        else:
            rejection_reasons.extend([f"Attempt {attempt + 1}: {r}" for r in reasons])

    # If all attempts failed or Ollama absent, enforce fallback
    fallback = build_fallback_clue(fact, modality)
    dir_line = fallback["direction_line"]
    obs_prompt = fallback["observation_prompt"]
    latency = int((time.time() - start_time) * 1000)

    return ClueResult(
        waypoint_index=fact.waypoint_index,
        modality=modality,
        direction_line=dir_line,
        observation_prompt=obs_prompt,
        is_valid=True,
        rejection_reasons=rejection_reasons,
        retries_used=max_retries if not used_fallback else 0,
        used_fallback=True,
        raw_response=raw_response or "OLLAMA_OFFLINE_FALLBACK",
        latency_ms=latency
    )

def generate_all_clues(facts: List[FactRecord], run_id: str, ollama_model: Optional[str] = "gemma:2b") -> List[ClueResult]:
    validator = ClueValidator()
    results = []
    run_log_path = os.path.join(RUNS_DIR, f"{run_id}_clues.jsonl")

    with open(run_log_path, "w", encoding="utf-8") as log_file:
        for idx, fact in enumerate(facts):
            res = generate_clue_for_waypoint(fact, idx, ollama_model=ollama_model, validator=validator)
            results.append(res)
            log_entry = {
                "run_id": run_id,
                "timestamp": time.time(),
                "fact": asdict(fact),
                "clue": asdict(res)
            }
            log_file.write(json.dumps(log_entry) + "\n")

    return results
