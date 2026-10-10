import argparse
import sys
import uuid
import os

from ingest import ingest
from route import compute_loop_route
from facts import extract_fact_records
from clues import generate_all_clues
from render import render_field_card

def main():
    parser = argparse.ArgumentParser(
        description="Paper Trail: Offline Walk Generator & Field Pocket Card Creator"
    )
    parser.add_argument("--lat", type=float, default=12.9716, help="Starting latitude (default: Bangalore Cubbon Park)")
    parser.add_argument("--lon", type=float, default=77.5946, help="Starting longitude (default: Bangalore Cubbon Park)")
    parser.add_argument("--minutes", type=int, default=30, help="Walk time budget in minutes (30, 45, 60)")
    parser.add_argument("--radius", type=float, default=1200.0, help="OSM exploration radius in meters")
    parser.add_argument("--speed", type=float, default=4.5, help="Walking speed in km/h")
    parser.add_argument("--out", type=str, default="walk_card.pdf", help="Output PDF filepath")
    parser.add_argument("--offline", action="store_true", help="Force offline mode using local cached OSM data")
    parser.add_argument("--cache-name", type=str, default=None, help="Specific cache filename to load")
    parser.add_argument("--ollama-model", type=str, default="gemma:2b", help="Local Ollama model tag")

    args = parser.parse_args()
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    print("=" * 65)
    print("[*] PAPER TRAIL - OFFLINE LOCAL WALK GENERATOR")
    print("=" * 65)
    print(f"Origin Coordinates : {args.lat:.4f}, {args.lon:.4f}")
    print(f"Duration Target    : {args.minutes} minutes")
    print(f"Offline Mode       : {args.offline}")
    print(f"Output Card Target : {args.out}")
    print("-" * 65)

    # 1. Ingest OSM data
    print("Step 1/5: Loading spatial graph & POIs...")
    data = ingest(args.lat, args.lon, radius_m=args.radius, offline=args.offline, cache_name=args.cache_name)
    print(f"  [+] Indexed {len(data.pois)} candidate POIs and {len(data.nodes)} graph nodes.")

    # 2. Compute Loop Route
    print("Step 2/5: Solving loop route & waypoints...")
    route_res = compute_loop_route(data, args.lat, args.lon, target_minutes=args.minutes, speed_kmh=args.speed)
    print(f"  [+] Route distance: {route_res.actual_distance_m:.0f}m (Target: {route_res.target_distance_m:.0f}m)")
    print(f"  [+] Estimated time: {route_res.estimated_minutes:.1f} min (Error: {route_res.error_percentage:.1f}%)")
    print(f"  [+] Selected {len(route_res.waypoints)} distinct waypoints.")

    # 3. Extract Fact Records
    print("Step 3/5: Isolating verifiable fact records...")
    facts = extract_fact_records(route_res.waypoints)
    for f in facts:
        print(f"    - Stop {f.waypoint_index}: [{f.category}] {f.name or 'Feature'} ({f.distance_from_prev_m}m {f.compass})")

    # 4. Generate Clues & Validate
    print("Step 4/5: Generating sensory observation clues & validating against facts...")
    clues = generate_all_clues(facts, run_id=run_id, ollama_model=args.ollama_model)
    validated_count = sum(1 for c in clues if c.is_valid)
    fallbacks = sum(1 for c in clues if c.used_fallback)
    print(f"  [+] Generated {len(clues)} clues ({validated_count} verified, {fallbacks} fallback templates)")

    # 5. Render Monochrome Field Card PDF
    print("Step 5/5: Compiling monochrome vector field card...")
    out_pdf = render_field_card(route_res, clues, output_path=args.out)
    print(f"  [+] Field card successfully generated: {out_pdf}")
    print("=" * 65)
    print("[SUCCESS] Print this PDF, leave your phone behind, and touch grass.")
    print("=" * 65)

if __name__ == "__main__":
    main()
