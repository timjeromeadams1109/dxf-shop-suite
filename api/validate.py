from http.server import BaseHTTPRequestHandler
from api._dxf_utils import parse_form_data, read_dxf, get_dxf_stats, json_response, cors_preflight
from api.machines import MACHINES


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            fields, files = parse_form_data(self)
            file_info = files.get("file")
            if not file_info:
                json_response(self, {"error": "No file uploaded"}, 400)
                return

            doc = read_dxf(file_info["data"])
            stats = get_dxf_stats(doc)

            issues = []
            # Check for problems
            if stats["open_contours"] > 0:
                issues.append({"severity": "error", "code": "OPEN_CONTOUR", "message": f"{stats['open_contours']} open contour(s) found — all cut paths must be closed"})
            if stats["spline_count"] > 0:
                issues.append({"severity": "warning", "code": "SPLINES", "message": f"{stats['spline_count']} spline(s) found — most CNC machines require arcs and lines only"})
            if stats["block_refs"] > 0:
                issues.append({"severity": "warning", "code": "BLOCKS", "message": f"{stats['block_refs']} block reference(s) found — should be exploded before CAM"})
            if stats["dxf_version"] != "AC1015":
                issues.append({"severity": "warning", "code": "VERSION", "message": f"DXF version is {stats['dxf_version']} — AC1015 (R2000) recommended"})

            # Machine-specific checklist
            machine_key = fields.get("machine", "")
            machine_checklist = []
            if machine_key and machine_key in MACHINES:
                machine_checklist = MACHINES[machine_key]["checklist"]

            ready = len([i for i in issues if i["severity"] == "error"]) == 0

            json_response(self, {
                "ready_for_cam": ready,
                "stats": stats,
                "issues": issues,
                "machine_checklist": machine_checklist,
            })
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_OPTIONS(self):
        cors_preflight(self)
