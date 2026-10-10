import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import networkx as nx

from ingest import IngestData, PointOfInterest, haversine_distance_m

@dataclass
class Waypoint:
    index: int
    poi: PointOfInterest
    lat: float
    lon: float
    distance_from_prev_m: float
    bearing_from_prev: float
    compass_from_prev: str

@dataclass
class RouteResult:
    start_lat: float
    start_lon: float
    target_minutes: int
    target_distance_m: float
    actual_distance_m: float
    estimated_minutes: float
    waypoints: List[Waypoint]
    polyline: List[Tuple[float, float]]  # (lat, lon) path coords
    error_percentage: float

def build_walkable_graph(data: IngestData) -> nx.Graph:
    G = nx.Graph()
    # Add nodes with coords
    for nid, (lat, lon) in data.nodes.items():
        G.add_node(nid, lat=lat, lon=lon)

    # Add edges from walkable ways
    for way in data.ways:
        if not way.is_walkable:
            continue
        nodes = way.nodes
        for i in range(len(nodes) - 1):
            u, v = nodes[i], nodes[i + 1]
            if u in data.nodes and v in data.nodes:
                lat1, lon1 = data.nodes[u]
                lat2, lon2 = data.nodes[v]
                dist = haversine_distance_m(lat1, lon1, lat2, lon2)
                G.add_edge(u, v, weight=dist)
    return G

def find_nearest_node(G: nx.Graph, lat: float, lon: float) -> Optional[int]:
    best_node = None
    min_dist = float("inf")
    for node, attrs in G.nodes(data=True):
        if "lat" in attrs and "lon" in attrs:
            d = haversine_distance_m(lat, lon, attrs["lat"], attrs["lon"])
            if d < min_dist:
                min_dist = d
                best_node = node
    return best_node

def select_diverse_waypoints(
    data: IngestData,
    origin_lat: float,
    origin_lon: float,
    target_distance_m: float,
    k: int = 5
) -> List[PointOfInterest]:
    if not data.pois:
        return []

    # For a circular loop through k waypoints and back to origin,
    # approximate polygon perimeter: perimeter ≈ 2 * pi * R (if loop circles origin)
    # Target radius from origin R ≈ target_distance_m / (2 * pi * 0.9)
    ideal_radius_m = min(target_distance_m / (2.0 * math.pi * 0.85), data.radius_m * 0.9)
    min_radius_m = max(ideal_radius_m * 0.5, 120.0)
    max_radius_m = min(ideal_radius_m * 1.4, data.radius_m * 0.98)

    # Filter candidate POIs within the target distance perimeter band
    candidate_pois = []
    for poi in data.pois:
        dist = haversine_distance_m(origin_lat, origin_lon, poi.lat, poi.lon)
        if min_radius_m <= dist <= max_radius_m:
            candidate_pois.append((abs(dist - ideal_radius_m), poi))

    # If band is sparse, relax radius constraints
    if len(candidate_pois) < k:
        candidate_pois = []
        for poi in data.pois:
            dist = haversine_distance_m(origin_lat, origin_lon, poi.lat, poi.lon)
            if dist >= 80.0:
                candidate_pois.append((abs(dist - ideal_radius_m), poi))

    candidate_pois.sort(key=lambda x: x[0])

    selected: List[PointOfInterest] = []
    seen_categories = set()
    min_inter_waypoint_dist = max(target_distance_m / (k * 2.5), 100.0)

    # Pick POIs distributed across different angles/sectors around origin
    for _, poi in candidate_pois:
        if len(selected) >= k:
            break
        too_close = any(
            haversine_distance_m(poi.lat, poi.lon, s.lat, s.lon) < min_inter_waypoint_dist
            for s in selected
        )
        if not too_close:
            selected.append(poi)
            seen_categories.add(poi.category)

    # Fallback to fill up to k if needed
    for _, poi in candidate_pois:
        if len(selected) >= k:
            break
        if poi not in selected:
            selected.append(poi)

    return selected

def solve_loop_order(origin_lat: float, origin_lon: float, pois: List[PointOfInterest]) -> List[PointOfInterest]:
    if not pois:
        return []

    # Sort circularly by angle around origin to make a natural loop without self-intersections
    def angle_from_origin(p: PointOfInterest) -> float:
        return math.atan2(p.lon - origin_lon, p.lat - origin_lat)

    return sorted(pois, key=angle_from_origin)

def compute_loop_route(
    data: IngestData,
    origin_lat: float,
    origin_lon: float,
    target_minutes: int = 30,
    speed_kmh: float = 4.5
) -> RouteResult:
    # Target distance in meters: (speed km/h * 1000 m / 60 min) * minutes
    target_distance_m = (speed_kmh * 1000.0 / 60.0) * target_minutes

    # Determine optimal number of waypoints based on walk duration
    k = 5 if target_minutes <= 30 else (6 if target_minutes <= 45 else 8)
    selected_pois = select_diverse_waypoints(data, origin_lat, origin_lon, target_distance_m=target_distance_m, k=k)

    ordered_pois = solve_loop_order(origin_lat, origin_lon, selected_pois)

    G = build_walkable_graph(data)
    use_graph = G.number_of_edges() > 0

    full_polyline: List[Tuple[float, float]] = []
    total_distance_m = 0.0
    waypoints: List[Waypoint] = []

    stops = [(origin_lat, origin_lon)] + [(p.lat, p.lon) for p in ordered_pois] + [(origin_lat, origin_lon)]

    for i in range(len(stops) - 1):
        lat1, lon1 = stops[i]
        lat2, lon2 = stops[i + 1]

        leg_dist = 0.0
        leg_coords: List[Tuple[float, float]] = []

        if use_graph:
            n1 = find_nearest_node(G, lat1, lon1)
            n2 = find_nearest_node(G, lat2, lon2)
            if n1 and n2 and nx.has_path(G, n1, n2):
                try:
                    path = nx.shortest_path(G, n1, n2, weight="weight")
                    leg_coords = [(G.nodes[n]["lat"], G.nodes[n]["lon"]) for n in path]
                    leg_dist = sum(
                        haversine_distance_m(leg_coords[j][0], leg_coords[j][1], leg_coords[j+1][0], leg_coords[j+1][1])
                        for j in range(len(leg_coords) - 1)
                    )
                except Exception:
                    leg_coords = []

        if not leg_coords:
            # Fallback to straight leg with intermediate interpolation
            leg_dist = haversine_distance_m(lat1, lon1, lat2, lon2)
            steps = max(2, int(leg_dist / 50.0))
            leg_coords = [
                (lat1 + (lat2 - lat1) * (s / steps), lon1 + (lon2 - lon1) * (s / steps))
                for s in range(steps + 1)
            ]

        total_distance_m += leg_dist
        if full_polyline:
            full_polyline.extend(leg_coords[1:])
        else:
            full_polyline.extend(leg_coords)

        # Record waypoint if it's one of the POIs
        if 0 < i <= len(ordered_pois):
            poi = ordered_pois[i - 1]
            prev_lat, prev_lon = stops[i - 1]
            dist_prev = haversine_distance_m(prev_lat, prev_lon, poi.lat, poi.lon)
            from ingest import bearing_degrees, bearing_to_compass
            b = bearing_degrees(prev_lat, prev_lon, poi.lat, poi.lon)
            comp = bearing_to_compass(b)
            waypoints.append(Waypoint(
                index=i,
                poi=poi,
                lat=poi.lat,
                lon=poi.lon,
                distance_from_prev_m=dist_prev,
                bearing_from_prev=b,
                compass_from_prev=comp
            ))

    est_minutes = (total_distance_m / 1000.0) / speed_kmh * 60.0
    error_pct = abs(total_distance_m - target_distance_m) / target_distance_m * 100.0

    return RouteResult(
        start_lat=origin_lat,
        start_lon=origin_lon,
        target_minutes=target_minutes,
        target_distance_m=target_distance_m,
        actual_distance_m=total_distance_m,
        estimated_minutes=est_minutes,
        waypoints=waypoints,
        polyline=full_polyline,
        error_percentage=error_pct
    )
