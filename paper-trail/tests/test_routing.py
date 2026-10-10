import os
import pytest
from ingest import ingest
from route import compute_loop_route

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache")

def test_offline_route_generation_and_loop_closure():
    # Test using Cubbon Park cached extract
    lat, lon = 12.9716, 77.5946
    data = ingest(lat, lon, radius_m=1200.0, offline=True)
    assert len(data.pois) > 0
    assert len(data.nodes) > 0

    route_res = compute_loop_route(data, lat, lon, target_minutes=30, speed_kmh=4.5)
    
    # 1. Polyline must start and end at origin
    assert len(route_res.polyline) >= 2
    start_pt = route_res.polyline[0]
    end_pt = route_res.polyline[-1]
    assert abs(start_pt[0] - lat) < 1e-4
    assert abs(start_pt[1] - lon) < 1e-4
    assert abs(end_pt[0] - lat) < 1e-4
    assert abs(end_pt[1] - lon) < 1e-4

    # 2. Waypoints count
    assert 4 <= len(route_res.waypoints) <= 8

    # 3. Target distance calibration (within reasonable walking range)
    assert route_res.actual_distance_m > 1200.0
