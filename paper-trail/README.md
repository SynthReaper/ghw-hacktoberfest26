# Paper Trail: Offline Walk Generator & Analog Field Card

> **DEV Hacktoberfest Open-Source AI Challenge (Theme: Touch Grass)**  
> *Generate an algorithmic walking card from OpenStreetMap and local open models. Print it out, leave the smartphone at home, and explore physical reality.*

---

## The Vision & Invariant
Most "AI outdoors" apps paradoxically chain users to their glowing screens with camera viewfinders and digital notifications. **Paper Trail** reverses this:
- **Zero Screens Outside:** The software executes locally on your machine, generates a printable, pocket-sized vector PDF field card with an ink-friendly topological loop map, sensory clues, and blank field-note boxes.
- **The LLM Never Owns Facts:** Code extracts true OpenStreetMap POIs (parks, trees, water, shrines, amenities) and computes a closed-loop route. The open model (Gemma / local fallback) only supplies language and multi-sensory observation prompts (`look`, `listen`, `count`, `touch`, `sketch`).
- **Strict Anti-Hallucination Validator:** An automated rule validator rejects and logs any clue inventing proper nouns, unverified species, or numbers absent from the map.
- **100% Offline & Private:** Zero location data or coordinates leave your laptop. Cached extracts allow total operation without internet access.

---

## Project Architecture

```
d:\Competition\Hackathons\MLH x Hacktober\
├── ingest.py            # Overpass API fetcher + offline caching + POI extractor
├── route.py             # NetworkX walkable graph + loop solver + calibrated distance scaling
├── facts.py             # Strictly typed, isolated FactRecord generator
├── clues.py             # Multi-sensory clue generator + Anti-Hallucination Validator + fallback
├── render.py            # ReportLab vector monochrome A4/A5 PDF field card renderer
├── cli.py               # Unified CLI runner
├── cache/               # Bundled OpenStreetMap extracts (e.g. Bangalore Cubbon Park)
├── examples/            # Production generated field cards (PDF)
├── runs/                # Structured telemetry & validation JSONL logs
├── tests/               # Pytest suite for validator and routing
└── web/index.html       # Zero-build lightweight visual preview UI
```

---

## Quickstart

### 1. Installation
Ensure Python 3.11+ is installed:
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate a Walk (100% Offline)
Run against the bundled Cubbon Park dataset:
```bash
python cli.py --lat 12.9716 --lon 77.5946 --minutes 30 --offline --out examples/my_walk_card.pdf
```

### 3. Generate a Live Walk
Query any geographic coordinates worldwide (will automatically cache locally):
```bash
python cli.py --lat 12.9716 --lon 77.5946 --minutes 45 --out my_walk.pdf
```

### 4. Running the Test Suite
Validate the anti-hallucination engine and closed loop routing:
```bash
pytest -v
```

---

## Anti-Hallucination Validator Specs

The validator enforces four non-negotiable invariants before any prompt makes it onto the physical card:
1. **Proper Noun Containment:** No unverified capitalized tokens beyond the OSM entity name and standard navigational stop words.
2. **Species Guard:** Zero invented botanical species (e.g., "oak", "banyan", "pine") unless explicitly recorded in the OSM feature tags.
3. **Numerical Restraint:** Prohibits fabricated counts or metrics.
4. **Strict Fallback:** If an open model hallucinates across 3 retries (or local model daemon is offline), deterministically grounded sensory templates take over, logging telemetry to `runs/<id>_clues.jsonl`.

---

## License & Attribution
- Code licensed under MIT.
- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL).
