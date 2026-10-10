import pytest
from facts import FactRecord
from clues import ClueValidator, build_fallback_clue

def test_validator_passes_strictly_grounded_clue():
    validator = ClueValidator()
    fact = FactRecord(
        waypoint_index=1,
        poi_id="node/123",
        poi_type="node",
        category="tree",
        name="Cubbon Park Banyan",
        key_tags={"natural": "tree", "species": "banyan"},
        distance_from_prev_m=150,
        bearing_from_prev=45,
        compass="NE"
    )

    valid_direction = "Head NE approximately 150m."
    valid_prompt = "Look toward Cubbon Park Banyan. Notice the hanging aerial roots and leaf density."

    is_valid, reasons = validator.validate(valid_prompt, valid_direction, fact)
    assert is_valid is True, f"Expected valid but failed with reasons: {reasons}"

def test_validator_rejects_hallucinated_proper_nouns():
    validator = ClueValidator()
    fact = FactRecord(
        waypoint_index=2,
        poi_id="node/456",
        poi_type="node",
        category="bench",
        name="",
        key_tags={"amenity": "bench"},
        distance_from_prev_m=80,
        bearing_from_prev=90,
        compass="E"
    )

    # Hallucinating 'Starbucks' and 'Alexander'
    hallucinated_prompt = "Sit near the bench by Starbucks and look for Alexander."
    is_valid, reasons = validator.validate(hallucinated_prompt, "Head E approximately 80m.", fact)

    assert is_valid is False
    assert any("Starbucks" in r for r in reasons)
    assert any("Alexander" in r for r in reasons)

def test_validator_rejects_hallucinated_species():
    validator = ClueValidator()
    fact = FactRecord(
        waypoint_index=3,
        poi_id="node/789",
        poi_type="node",
        category="tree",
        name="",
        key_tags={"natural": "tree"},  # No species in OSM tags
        distance_from_prev_m=120,
        bearing_from_prev=180,
        compass="S"
    )

    # Hallucinating 'oak' species
    hallucinated_prompt = "Examine the old oak bark and notice its deep ridges."
    is_valid, reasons = validator.validate(hallucinated_prompt, "Head S approximately 120m.", fact)

    assert is_valid is False
    assert any("oak" in r.lower() for r in reasons)

def test_validator_rejects_excessive_length():
    validator = ClueValidator()
    fact = FactRecord(
        waypoint_index=4,
        poi_id="node/999",
        poi_type="node",
        category="water",
        name="Lotus Pond",
        key_tags={"natural": "water"},
        distance_from_prev_m=200,
        bearing_from_prev=270,
        compass="W"
    )

    long_prompt = " ".join(["notice"] * 35)
    is_valid, reasons = validator.validate(long_prompt, "Head W approximately 200m.", fact)
    assert is_valid is False
    assert any("exceeded maximum length" in r for r in reasons)

def test_deterministic_fallback_modalities():
    fact = FactRecord(
        waypoint_index=1,
        poi_id="node/101",
        poi_type="node",
        category="water",
        name="Quiet Fountain",
        key_tags={"amenity": "fountain"},
        distance_from_prev_m=90,
        bearing_from_prev=0,
        compass="N"
    )

    for mod in ["look", "listen", "count", "touch", "sketch"]:
        fb = build_fallback_clue(fact, mod)
        assert "Head N approximately 90m." in fb["direction_line"]
        assert len(fb["observation_prompt"].split()) < 30
