import json
import math
import hashlib
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import requests

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

@dataclass
class PointOfInterest:
    id: str
    osm_type: str  # node or way
    name: Optional[str]
    category: str  # tree, park, water, worship, amenity, historic, art, bench, landmark
    lat: float
    lon: float
    tags: Dict[str, str]

@dataclass
class OSMWay:
    id: str
    nodes: List[int]
    tags: Dict[str, str]
    is_walkable: bool

@dataclass
class IngestData:
    center_lat: float
    center_lon: float
    radius_m: float
    pois: List[PointOfInterest]
    nodes: Dict[int, Tuple[float, float]]  # node_id -> (lat, lon)
    ways: List[OSMWay]

def get_cache_key(lat: float, lon: float, radius_m: float) -> str:
    key_str = f"{round(lat, 4)}_{round(lon, 4)}_{int(radius_m)}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    return 2.0 * R * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

def bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0

def bearing_to_compass(bearing: float) -> str:
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((bearing + 11.25) / 22.5) % 16
    return directions[idx]

def classify_poi(tags: Dict[str, str]) -> Optional[str]:
    if "natural" in tags and tags["natural"] in ["tree", "wood"]:
        return "tree"
    if "natural" in tags and tags["natural"] in ["water", "spring", "fountain"]:
        return "water"
    if tags.get("amenity") == "fountain":
        return "water"
    if "leisure" in tags and tags["leisure"] in ["park", "garden", "nature_reserve"]:
        return "park"
    if "amenity" in tags and tags["amenity"] in ["place_of_worship", "temple", "church", "mosque"]:
        return "worship"
    if "amenity" in tags and tags["amenity"] in ["bench", "drinking_water"]:
        return "amenity"
    if "historic" in tags or "heritage" in tags:
        return "historic"
    if "tourism" in tags and tags["tourism"] in ["artwork", "viewpoint", "attraction"]:
        return "art"
    if "wikipedia" in tags or "wikidata" in tags:
        return "landmark"
    if "amenity" in tags and tags["amenity"] in ["cafe", "library", "clock"]:
        return "landmark"
    return None

def fetch_overpass_data(lat: float, lon: float, radius_m: float = 1200.0) -> Dict[str, Any]:
    # Streamlined Overpass QL query with bounding box around center
    delta_lat = radius_m / 111000.0
    delta_lon = radius_m / (111000.0 * math.cos(math.radians(lat)))
    s, n = lat - delta_lat, lat + delta_lat
    w, e = lon - delta_lon, lon + delta_lon

    query = f"""
    [out:json][timeout:30];
    (
      way({s},{w},{n},{e})["highway"~"footway|pedestrian|path|residential|living_street|track|service|steps"];
      node({s},{w},{n},{e})["natural"~"tree|water|wood"];
      node({s},{w},{n},{e})["amenity"~"bench|drinking_water|fountain|place_of_worship|cafe|library"];
      node({s},{w},{n},{e})["historic"];
      node({s},{w},{n},{e})["tourism"~"artwork|viewpoint|attraction"];
      way({s},{w},{n},{e})["leisure"~"park|garden"];
      way({s},{w},{n},{e})["natural"~"water"];
    );
    out body;
    >;
    out skel qt;
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]
    headers = {
        "User-Agent": "PaperTrail-OfflineWalk/1.0 (Hacktoberfest touch-grass challenge; contact@devchallenge.local)"
    }
    for url in endpoints:
        try:
            resp = requests.post(url, data={"data": query}, headers=headers, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if "elements" in data and len(data["elements"]) > 0:
                    return data
        except Exception:
            continue
    raise RuntimeError(f"Failed to fetch OSM data from Overpass for {lat}, {lon}")

def parse_osm_elements(data: Dict[str, Any], center_lat: float, center_lon: float, radius_m: float) -> IngestData:
    nodes: Dict[int, Tuple[float, float]] = {}
    raw_ways: List[Dict[str, Any]] = []
    pois: List[PointOfInterest] = []

    # First pass: index nodes
    for el in data.get("elements", []):
        if el["type"] == "node":
            nid = el["id"]
            lat, lon = el["lat"], el["lon"]
            nodes[nid] = (lat, lon)
            tags = el.get("tags", {})
            cat = classify_poi(tags)
            if cat:
                name = tags.get("name") or tags.get("name:en")
                pois.append(PointOfInterest(
                    id=f"node/{nid}",
                    osm_type="node",
                    name=name,
                    category=cat,
                    lat=lat,
                    lon=lon,
                    tags={k: v for k, v in tags.items() if k in ["name", "natural", "amenity", "historic", "species", "tourism", "leisure", "religion"]}
                ))
        elif el["type"] == "way":
            raw_ways.append(el)

    # Second pass: index ways and way-based POIs (parks, water polygons)
    parsed_ways: List[OSMWay] = []
    for w in raw_ways:
        tags = w.get("tags", {})
        highway = tags.get("highway")
        is_walkable = highway in [
            "footway", "pedestrian", "path", "residential", "living_street",
            "service", "track", "unclassified", "steps", "cycleway", "tertiary"
        ]
        parsed_ways.append(OSMWay(
            id=f"way/{w['id']}",
            nodes=w.get("nodes", []),
            tags=tags,
            is_walkable=is_walkable
        ))

        # Check if way itself is a POI (park, water)
        cat = classify_poi(tags)
        if cat and w.get("nodes"):
            # Compute centroid from member nodes
            coords = [nodes[n] for n in w["nodes"] if n in nodes]
            if coords:
                avg_lat = sum(c[0] for c in coords) / len(coords)
                avg_lon = sum(c[1] for c in coords) / len(coords)
                name = tags.get("name") or tags.get("name:en")
                pois.append(PointOfInterest(
                    id=f"way/{w['id']}",
                    osm_type="way",
                    name=name,
                    category=cat,
                    lat=avg_lat,
                    lon=avg_lon,
                    tags={k: v for k, v in tags.items() if k in ["name", "natural", "amenity", "historic", "tourism", "leisure"]}
                ))

    return IngestData(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_m=radius_m,
        pois=pois,
        nodes=nodes,
        ways=parsed_ways
    )

def ingest(lat: float, lon: float, radius_m: float = 1200.0, offline: bool = False, cache_name: Optional[str] = None) -> IngestData:
    cache_id = cache_name or get_cache_key(lat, lon, radius_m)
    cache_path = os.path.join(CACHE_DIR, f"{cache_id}.json")

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            return parse_osm_elements(raw_data, lat, lon, radius_m)

    if offline:
        # Check if any cache is available to fall back to
        all_caches = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
        if all_caches:
            fallback = os.path.join(CACHE_DIR, all_caches[0])
            with open(fallback, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                return parse_osm_elements(raw_data, lat, lon, radius_m)
        raise FileNotFoundError(f"Offline mode requested but no cache exists at {cache_path}")

    # Fetch live
    raw_data = fetch_overpass_data(lat, lon, radius_m)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    return parse_osm_elements(raw_data, lat, lon, radius_m)
