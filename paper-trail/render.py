import os
import math
from typing import List, Tuple
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, PolyLine, Circle, String, Rect, Line

from route import RouteResult
from clues import ClueResult

def render_field_card(
    route: RouteResult,
    clues: List[ClueResult],
    output_path: str,
    title: str = "PAPER TRAIL: FIELD EXPLORATION CARD"
) -> str:
    """
    Renders an ink-friendly, high-contrast monochrome A4 landscape field card.
    Left side: Topological Route Map & Navigation Telemetry
    Right side: Sensory Clues & Field-Notes Observation Grid
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=landscape(A4))
    width, height = landscape(A4)  # ~842 x 595 points

    # Frame & Margins
    margin = 25
    c.setLineWidth(1.5)
    c.setStrokeColor(colors.black)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Header Banner
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin + 15, height - margin - 25, title)
    c.setFont("Helvetica", 9)
    meta_line = (
        f"Target: {route.target_minutes} min | "
        f"Est. Distance: {route.actual_distance_m / 1000.0:.2f} km | "
        f"Waypoints: {len(route.waypoints)} | "
        f"Generated Offline: OpenStreetMap ODbL"
    )
    c.drawRightString(width - margin - 15, height - margin - 25, meta_line)

    # Dividing Line between Map (Left) and Clues (Right)
    mid_x = margin + 350
    c.setLineWidth(1.0)
    c.line(mid_x, margin, mid_x, height - margin - 35)

    # ------------------ LEFT SIDE: ROUTE MAP ------------------
    map_x0 = margin + 15
    map_y0 = margin + 45
    map_w = mid_x - map_x0 - 20
    map_h = height - margin - 90

    # Bounding Box of Polyline
    all_lats = [p[0] for p in route.polyline]
    all_lons = [p[1] for p in route.polyline]

    if all_lats and all_lons:
        min_lat, max_lat = min(all_lats), max(all_lats)
        min_lon, max_lon = min(all_lons), max(all_lons)
        d_lat = max(max_lat - min_lat, 0.001)
        d_lon = max(max_lon - min_lon, 0.001)

        scale_lat = (map_h - 40) / d_lat
        scale_lon = (map_w - 40) / d_lon
        scale = min(scale_lat, scale_lon)

        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0
        center_x = map_x0 + map_w / 2.0
        center_y = map_y0 + map_h / 2.0

        def to_canvas_pt(lat: float, lon: float) -> Tuple[float, float]:
            px = center_x + (lon - center_lon) * scale
            py = center_y + (lat - center_lat) * scale
            return px, py

        # Draw Route Path
        c.setLineWidth(2.5)
        c.setStrokeColor(colors.black)
        poly_pts = [to_canvas_pt(lat, lon) for lat, lon in route.polyline]
        for i in range(len(poly_pts) - 1):
            c.line(poly_pts[i][0], poly_pts[i][1], poly_pts[i+1][0], poly_pts[i+1][1])

        # Draw Start / End Marker
        s_px, s_py = to_canvas_pt(route.start_lat, route.start_lon)
        c.setFillColor(colors.black)
        c.rect(s_px - 5, s_py - 5, 10, 10, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(s_px + 7, s_py - 3, "START / FINISH")

        # Draw Numbered Waypoints
        for wp in route.waypoints:
            w_px, w_py = to_canvas_pt(wp.lat, wp.lon)
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.black)
            c.setLineWidth(1.5)
            c.circle(w_px, w_py, 8, fill=1, stroke=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(w_px, w_py - 3, str(wp.index))

        # North Arrow
        na_x = map_x0 + 25
        na_y = map_y0 + map_h - 25
        c.setLineWidth(1.2)
        c.line(na_x, na_y - 15, na_x, na_y + 15)
        c.line(na_x, na_y + 15, na_x - 4, na_y + 5)
        c.line(na_x, na_y + 15, na_x + 4, na_y + 5)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(na_x, na_y + 18, "N")

    # Map Footnote & ODbL notice
    c.setFont("Helvetica-Oblique", 7)
    c.setFillColor(colors.black)
    c.drawString(map_x0, margin + 12, "Data © OpenStreetMap contributors | Rendered for phone-free navigation")

    # ------------------ RIGHT SIDE: SENSORY CLUES & FIELD NOTES ------------------
    clue_x0 = mid_x + 20
    clue_w = width - margin - clue_x0 - 10
    total_slots = max(len(clues), 1)
    slot_h = (height - margin - 50 - margin) / total_slots

    for idx, clue in enumerate(clues):
        slot_y0 = height - margin - 45 - (idx + 1) * slot_h
        
        # Waypoint Header Badge
        c.setFillColor(colors.black)
        c.rect(clue_x0, slot_y0 + slot_h - 20, 22, 16, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(clue_x0 + 11, slot_y0 + slot_h - 16, str(clue.waypoint_index))

        # Modality Tag & Direction
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        modality_label = f"[{clue.modality.upper()}]  {clue.direction_line}"
        c.drawString(clue_x0 + 30, slot_y0 + slot_h - 15, modality_label[:75])

        # Observation prompt
        c.setFont("Helvetica", 8.5)
        prompt_lines = []
        words = clue.observation_prompt.split()
        curr_line = ""
        for w in words:
            if len(curr_line + " " + w) > 55:
                prompt_lines.append(curr_line)
                curr_line = w
            else:
                curr_line = (curr_line + " " + w).strip()
        if curr_line:
            prompt_lines.append(curr_line)

        p_y = slot_y0 + slot_h - 32
        for pl in prompt_lines[:2]:
            c.drawString(clue_x0 + 30, p_y, pl)
            p_y -= 11

        # Field-Notes Box for Physical Pencil Notes
        box_y = slot_y0 + 5
        box_h = max(slot_h - 52, 18)
        c.setLineWidth(0.7)
        c.setStrokeColor(colors.Color(0.4, 0.4, 0.4))
        c.rect(clue_x0 + 30, box_y, clue_w - 35, box_h, fill=0, stroke=1)

        # Field Note Prompt Label
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.Color(0.5, 0.5, 0.5))
        c.drawString(clue_x0 + 35, box_y + box_h - 9, "[Field notes / pencil sketch / counts]:")

    c.showPage()
    c.save()
    return output_path
