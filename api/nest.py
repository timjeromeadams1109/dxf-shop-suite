from http.server import BaseHTTPRequestHandler
import math
from api._dxf_utils import parse_form_data, read_dxf, get_dxf_stats, get_bounding_box, json_response, cors_preflight


def parse_sheet_size(sheet_str):
    """Parse sheet size like '48\"x96\"' or '48x96' into (width, height) in inches."""
    s = sheet_str.replace('"', "").replace("'", "").replace(" ", "").lower()
    parts = s.split("x")
    if len(parts) != 2:
        return 48, 96  # default
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return 48, 96


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            fields, files = parse_form_data(self)

            # Handle multiple files
            file_list = files.get("files[]", [])
            if isinstance(file_list, dict):
                file_list = [file_list]
            if not file_list:
                json_response(self, {"error": "No files uploaded"}, 400)
                return

            quantity = int(fields.get("quantity", "1"))
            sheet_w, sheet_h = parse_sheet_size(fields.get("sheet", "48x96"))
            sheet_area = sheet_w * sheet_h

            parts = []
            total_part_area = 0

            for f in file_list:
                doc = read_dxf(f["data"])
                bb = get_bounding_box(doc)
                stats = get_dxf_stats(doc)

                if bb:
                    part_area = bb["width"] * bb["height"]
                    total_part_area += part_area * quantity
                    parts.append({
                        "file": f["filename"],
                        "width": round(bb["width"], 3),
                        "height": round(bb["height"], 3),
                        "area": round(part_area, 3),
                        "cut_length": stats["estimated_cut_length"],
                    })

            # Calculate nesting estimate
            sheets_needed = max(1, math.ceil(total_part_area / (sheet_area * 0.85)))  # 85% practical max
            utilization = min(99, round((total_part_area / (sheets_needed * sheet_area)) * 100))

            recommendations = []
            if utilization < 60:
                recommendations.append("Low utilization — consider grouping with other parts or using a smaller sheet")
            if utilization > 90:
                recommendations.append("Tight fit — verify parts don't overlap in CAM nesting software")
            if any(p["width"] > sheet_w or p["height"] > sheet_h for p in parts):
                recommendations.append("Warning: one or more parts exceed sheet dimensions — check orientation or use larger sheet")
            if quantity > 10:
                recommendations.append(f"High quantity ({quantity}) — consider batch nesting with remnant tracking")

            json_response(self, {
                "estimated_utilization_pct": utilization,
                "sheets_needed": sheets_needed,
                "sheet_size": f'{sheet_w}"x{sheet_h}"',
                "quantity": quantity,
                "parts": parts,
                "recommendations": recommendations,
            })
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_OPTIONS(self):
        cors_preflight(self)
