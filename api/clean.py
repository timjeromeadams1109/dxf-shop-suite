from http.server import BaseHTTPRequestHandler
import io
import json
import base64
import ezdxf
from api._dxf_utils import parse_form_data, read_dxf, get_dxf_stats, json_response, cors_preflight


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            fields, files = parse_form_data(self)
            file_info = files.get("file")
            if not file_info:
                json_response(self, {"error": "No file uploaded"}, 400)
                return

            doc = read_dxf(file_info["data"])
            stats_before = get_dxf_stats(doc)
            fixes = []

            msp = doc.modelspace()

            # Fix 1: Explode block references
            inserts = [e for e in msp if e.dxftype() == "INSERT"]
            for insert in inserts:
                try:
                    insert.explode()
                    fixes.append(f"Exploded block reference: {insert.dxf.name}")
                except Exception:
                    pass

            # Fix 2: Convert splines to polylines (approximate)
            splines = [e for e in msp if e.dxftype() == "SPLINE"]
            for spline in splines:
                try:
                    pts = list(spline.flattening(0.01))
                    if len(pts) >= 2:
                        msp.add_lwpolyline(
                            [(p.x, p.y) for p in pts],
                            dxfattribs={"layer": spline.dxf.layer},
                        )
                    msp.delete_entity(spline)
                    fixes.append("Converted spline to polyline approximation")
                except Exception:
                    pass

            # Fix 3: Remove duplicate entities (same type, same coords)
            seen = set()
            duplicates = []
            for e in msp:
                try:
                    if e.dxftype() == "LINE":
                        key = ("LINE", round(e.dxf.start.x, 4), round(e.dxf.start.y, 4), round(e.dxf.end.x, 4), round(e.dxf.end.y, 4))
                    elif e.dxftype() == "CIRCLE":
                        key = ("CIRCLE", round(e.dxf.center.x, 4), round(e.dxf.center.y, 4), round(e.dxf.radius, 4))
                    else:
                        continue
                    if key in seen:
                        duplicates.append(e)
                    else:
                        seen.add(key)
                except Exception:
                    pass
            for d in duplicates:
                msp.delete_entity(d)
                fixes.append("Removed duplicate entity")

            # Fix 4: Upgrade version if needed
            if doc.dxfversion != "AC1015":
                fixes.append(f"Version noted: {doc.dxfversion} (file saved as AC1015)")

            stats_after = get_dxf_stats(doc)

            # Save cleaned file to bytes
            stream = io.BytesIO()
            doc.saveas(stream)
            cleaned_bytes = stream.getvalue()
            cleaned_b64 = base64.b64encode(cleaned_bytes).decode("ascii")

            json_response(self, {
                "stats_before": stats_before,
                "stats_after": stats_after,
                "fixes_applied": fixes,
                "cleaned_file_b64": cleaned_b64,
                "filename": file_info["filename"].replace(".dxf", "_cleaned.dxf"),
            })
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_OPTIONS(self):
        cors_preflight(self)
