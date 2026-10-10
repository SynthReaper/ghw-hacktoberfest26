from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from route import Waypoint

@dataclass
class FactRecord:
    waypoint_index: int
    poi_id: str
    poi_type: str
    category: str
    name: str
    key_tags: Dict[str, str]
    distance_from_prev_m: int
    bearing_from_prev: int
    compass: str

    def to_prompt_context(self) -> Dict[str, Any]:
        """Strictly isolated context block passed to the LLM."""
        return {
            "stop_number": self.waypoint_index,
            "category": self.category,
            "name": self.name if self.name else "unnamed feature",
            "tags": self.key_tags,
            "distance_m": self.distance_from_prev_m,
            "direction": self.compass
        }

def extract_fact_records(waypoints: List[Waypoint]) -> List[FactRecord]:
    records: List[FactRecord] = []
    for wp in waypoints:
        poi = wp.poi
        # Extract only verified, whitelist tags
        safe_tags = {}
        for k, v in poi.tags.items():
            if k in ["natural", "amenity", "historic", "species", "tourism", "leisure", "religion"]:
                safe_tags[k] = str(v)

        records.append(FactRecord(
            waypoint_index=wp.index,
            poi_id=poi.id,
            poi_type=poi.osm_type,
            category=poi.category,
            name=poi.name if poi.name else "",
            key_tags=safe_tags,
            distance_from_prev_m=int(round(wp.distance_from_prev_m)),
            bearing_from_prev=int(round(wp.bearing_from_prev)),
            compass=wp.compass_from_prev
        ))
    return records
