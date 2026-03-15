from http.server import BaseHTTPRequestHandler
import json

MACHINES = {
    "amada_coma": {"name": "AMADA Coma", "type": "punch", "controller": "Unknown", "checklist": ["All hole sizes match available tool stations", "No splines in geometry", "All block references exploded", "Grain direction indicated if material requires it", "DXF version saved as AC1015", "Verify tool library is loaded and current"]},
    "amada_vella": {"name": "AMADA Vella", "type": "punch", "controller": "Unknown", "checklist": ["All hole sizes match available tool stations", "No splines in geometry", "All block references exploded", "Grain direction indicated if material requires it", "DXF version saved as AC1015", "Verify tool library is loaded and current"]},
    "amada_vipros": {"name": "AMADA Vipros", "type": "punch", "controller": "Unknown", "checklist": ["All hole sizes match available tool stations", "No splines in geometry", "All block references exploded", "Turret tool layout verified", "Grain direction indicated if material requires it", "DXF version saved as AC1015"]},
    "amada_apelio": {"name": "AMADA Apelio", "type": "punch", "controller": "Unknown", "checklist": ["All hole sizes match available tool stations", "No splines in geometry", "All block references exploded", "Laser/punch mode layers separated correctly", "Grain direction indicated if material requires it", "DXF version saved as AC1015"]},
    "vortman_631": {"name": "Vortman 631", "type": "plasma", "controller": "Unknown", "checklist": ["All geometry on layer 0 or named cut layers", "No splines — arcs and lines only", "All block references exploded", "All contours verified closed", "Part origin set to lower-left corner", "DXF version saved as AC1015", "Cut parameter profile selected by material and thickness"]},
    "vortman_325": {"name": "Vortman 325", "type": "plasma", "controller": "Unknown", "checklist": ["All geometry on layer 0 or named cut layers", "No splines — arcs and lines only", "All block references exploded", "All contours verified closed", "Part origin set to lower-left corner", "DXF version saved as AC1015", "Cut parameter profile selected by material and thickness"]},
    "lincoln_plasma": {"name": "Lincoln Plasma Tables", "type": "plasma", "controller": "Unknown", "checklist": ["All geometry on layer 0 or named cut layers", "No splines — arcs and lines only", "All block references exploded", "All contours verified closed", "DXF version saved as AC1015", "Cut parameter profile selected by material and thickness"]},
    "amada_12k_laser": {"name": "AMADA 12K Fiber Laser", "type": "laser", "controller": "Unknown", "checklist": ["All geometry on proper cut layers", "No splines — arcs and lines only", "All block references exploded", "All contours verified closed", "DXF version saved as AC1015", "Laser power and speed profile set by material and thickness", "Focus height verified for material"]},
    "amada_hr_brake": {"name": "AMADA HR Bend Press", "type": "brake", "controller": "Unknown", "checklist": ["Bend lines placed on separate non-cutting layer", "Bend sequence specified", "Tooling (punch/die) selection verified", "Material grain direction noted", "DXF version saved as AC1015", "Back gauge positions verified"]},
    "cincinnati_brake": {"name": "Cincinnati Bend Press", "type": "brake", "controller": "Unknown", "checklist": ["Bend lines placed on separate non-cutting layer", "Bend sequence specified", "Tooling (punch/die) selection verified", "Material grain direction noted", "DXF version saved as AC1015", "Back gauge positions verified"]},
    "acushear_brake": {"name": "ACUSHEAR Bend Press", "type": "brake", "controller": "Unknown", "checklist": ["Bend lines placed on separate non-cutting layer", "Bend sequence specified", "Tooling selection verified", "DXF version saved as AC1015", "Back gauge positions verified"]},
    "acushear_shear": {"name": "ACUSHEAR Shear", "type": "shear", "controller": "Unknown", "checklist": ["Cut lines clearly defined on proper layer", "Material dimensions within shear capacity", "DXF version saved as AC1015", "Blade clearance set for material thickness"]},
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(MACHINES).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
