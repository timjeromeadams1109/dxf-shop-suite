from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

# Standard structural connector reference data.
# Dimensional specs based on publicly available engineering standards.
# Not affiliated with or licensed by any manufacturer.

CONNECTORS = [
    # ── JOIST HANGERS ─────────────────────────────────────────────────────
    {"id":"JH-2x4",   "family":"Joist Hanger",    "code":"JH-2x4",   "description":"Face-mount hanger for 2x4 lumber",   "width_in":1.625, "height_in":4.75,  "depth_in":2.0, "gauge":18, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"JH-2x6",   "family":"Joist Hanger",    "code":"JH-2x6",   "description":"Face-mount hanger for 2x6 lumber",   "width_in":1.625, "height_in":6.0,   "depth_in":2.0, "gauge":18, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"JH-2x8",   "family":"Joist Hanger",    "code":"JH-2x8",   "description":"Face-mount hanger for 2x8 lumber",   "width_in":1.625, "height_in":8.0,   "depth_in":2.0, "gauge":18, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"JH-2x10",  "family":"Joist Hanger",    "code":"JH-2x10",  "description":"Face-mount hanger for 2x10 lumber",  "width_in":1.625, "height_in":10.0,  "depth_in":2.0, "gauge":16, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"JH-2x12",  "family":"Joist Hanger",    "code":"JH-2x12",  "description":"Face-mount hanger for 2x12 lumber",  "width_in":1.625, "height_in":12.0,  "depth_in":2.0, "gauge":16, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"JH-4x6",   "family":"Joist Hanger",    "code":"JH-4x6",   "description":"Heavy face-mount hanger for 4x6",    "width_in":3.25,  "height_in":6.0,   "depth_in":2.5, "gauge":14, "material":"G90 galvanized steel", "machines":["punch","laser"]},
    {"id":"JH-4x10",  "family":"Joist Hanger",    "code":"JH-4x10",  "description":"Heavy face-mount hanger for 4x10",   "width_in":3.25,  "height_in":10.0,  "depth_in":2.5, "gauge":14, "material":"G90 galvanized steel", "machines":["punch","laser"]},
    {"id":"JH-4x12",  "family":"Joist Hanger",    "code":"JH-4x12",  "description":"Heavy face-mount hanger for 4x12",   "width_in":3.25,  "height_in":12.0,  "depth_in":2.5, "gauge":14, "material":"G90 galvanized steel", "machines":["punch","laser"]},
    {"id":"JH-6x10",  "family":"Joist Hanger",    "code":"JH-6x10",  "description":"Extra-heavy hanger for 6x10",        "width_in":5.5,   "height_in":10.0,  "depth_in":3.0, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","laser","plasma"]},
    {"id":"JH-6x12",  "family":"Joist Hanger",    "code":"JH-6x12",  "description":"Extra-heavy hanger for 6x12",        "width_in":5.5,   "height_in":12.0,  "depth_in":3.0, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","laser","plasma"]},
    # ── STRUCTURAL ANGLES ─────────────────────────────────────────────────
    {"id":"ANG-2x2-16","family":"Structural Angle","code":"ANG-2x2-16","description":"2×2 light angle, 16 ga",            "width_in":2.0,   "height_in":2.0,   "depth_in":1.5, "gauge":16, "material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"ANG-2x2-12","family":"Structural Angle","code":"ANG-2x2-12","description":"2×2 standard angle, 12 ga",         "width_in":2.0,   "height_in":2.0,   "depth_in":2.0, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"ANG-2x3-14","family":"Structural Angle","code":"ANG-2x3-14","description":"2×3 general framing angle, 14 ga",  "width_in":2.0,   "height_in":3.0,   "depth_in":1.5, "gauge":14, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"ANG-3x3-12","family":"Structural Angle","code":"ANG-3x3-12","description":"3×3 heavy framing angle, 12 ga",    "width_in":3.0,   "height_in":3.0,   "depth_in":3.0, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"ANG-4x4-10","family":"Structural Angle","code":"ANG-4x4-10","description":"4×4 post connection angle, 10 ga",  "width_in":4.0,   "height_in":4.0,   "depth_in":4.0, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"ANG-4x6-10","family":"Structural Angle","code":"ANG-4x6-10","description":"4×6 beam connection angle, 10 ga",  "width_in":4.0,   "height_in":6.0,   "depth_in":4.0, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"ANG-6x6-10","family":"Structural Angle","code":"ANG-6x6-10","description":"6×6 heavy beam angle, 10 ga",       "width_in":6.0,   "height_in":6.0,   "depth_in":6.0, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","brake","plasma"]},
    # ── POST BASES ────────────────────────────────────────────────────────
    {"id":"PB-3.5",   "family":"Post Base",        "code":"PB-3.5",   "description":"Post base for 3.5\" post (4×4)",    "width_in":3.5,   "height_in":3.25,  "depth_in":3.5, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"PB-5.5",   "family":"Post Base",        "code":"PB-5.5",   "description":"Post base for 5.5\" post (6×6)",    "width_in":5.5,   "height_in":3.5,   "depth_in":5.5, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"PB-7.25",  "family":"Post Base",        "code":"PB-7.25",  "description":"Post base for 7.25\" post (8×8)",   "width_in":7.25,  "height_in":4.0,   "depth_in":7.25,"gauge":10, "material":"G90 galvanized steel", "machines":["punch","brake","plasma"]},
    {"id":"PB-9.25",  "family":"Post Base",        "code":"PB-9.25",  "description":"Post base for 9.25\" post (10×10)", "width_in":9.25,  "height_in":4.5,   "depth_in":9.25,"gauge":10, "material":"G90 galvanized steel", "machines":["plasma","laser"]},
    # ── POST CAPS ─────────────────────────────────────────────────────────
    {"id":"PC-3.5",   "family":"Post Cap",         "code":"PC-3.5",   "description":"Post cap for 3.5\" post & beam",    "width_in":3.5,   "height_in":3.5,   "depth_in":5.5, "gauge":14, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"PC-5.5",   "family":"Post Cap",         "code":"PC-5.5",   "description":"Post cap for 5.5\" post & beam",    "width_in":5.5,   "height_in":5.5,   "depth_in":5.5, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","brake"]},
    {"id":"PC-7.25",  "family":"Post Cap",         "code":"PC-7.25",  "description":"Post cap for 7.25\" post & beam",   "width_in":7.25,  "height_in":7.25,  "depth_in":5.5, "gauge":12, "material":"G90 galvanized steel", "machines":["punch","brake","plasma"]},
    # ── STRAP TIES ────────────────────────────────────────────────────────
    {"id":"ST-1.25x12","family":"Strap Tie",       "code":"ST-1.25x12","description":"1.25\" strap tie, 12\" length",    "width_in":1.25,  "height_in":12.0,  "depth_in":0.06,"gauge":16, "material":"G90 galvanized steel", "machines":["punch","plasma","laser"]},
    {"id":"ST-1.25x24","family":"Strap Tie",       "code":"ST-1.25x24","description":"1.25\" strap tie, 24\" length",    "width_in":1.25,  "height_in":24.0,  "depth_in":0.06,"gauge":16, "material":"G90 galvanized steel", "machines":["punch","plasma","laser"]},
    {"id":"ST-2x12",  "family":"Strap Tie",        "code":"ST-2x12",  "description":"2\" strap tie, 12\" length",        "width_in":2.0,   "height_in":12.0,  "depth_in":0.05,"gauge":18, "material":"G90 galvanized steel", "machines":["punch","plasma","laser"]},
    {"id":"ST-2x24",  "family":"Strap Tie",        "code":"ST-2x24",  "description":"2\" strap tie, 24\" length",        "width_in":2.0,   "height_in":24.0,  "depth_in":0.05,"gauge":18, "material":"G90 galvanized steel", "machines":["punch","plasma","laser"]},
    {"id":"ST-2x48",  "family":"Strap Tie",        "code":"ST-2x48",  "description":"2\" strap tie, 48\" length",        "width_in":2.0,   "height_in":48.0,  "depth_in":0.05,"gauge":16, "material":"G90 galvanized steel", "machines":["plasma","laser"]},
    # ── HURRICANE / RAFTER TIES ───────────────────────────────────────────
    {"id":"HT-1.75",  "family":"Hurricane Tie",    "code":"HT-1.75",  "description":"Rafter-to-plate tie, 1.75\" wide",  "width_in":1.75,  "height_in":4.5,   "depth_in":1.625,"gauge":18,"material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"HT-2.0",   "family":"Hurricane Tie",    "code":"HT-2.0",   "description":"Rafter-to-plate tie, 2\" wide",     "width_in":2.0,   "height_in":5.0,   "depth_in":1.75, "gauge":18,"material":"G90 galvanized steel", "machines":["punch"]},
    {"id":"HT-LTP4",  "family":"Hurricane Tie",    "code":"HT-LTP4",  "description":"Lateral tie plate, 4\" wide",       "width_in":4.0,   "height_in":2.75,  "depth_in":2.0,  "gauge":20,"material":"G90 galvanized steel", "machines":["punch"]},
    # ── HOLD-DOWNS ────────────────────────────────────────────────────────
    {"id":"HD-5",     "family":"Hold-Down",        "code":"HD-5",     "description":"Hold-down, 5/8\" bolt, light",      "width_in":2.5,   "height_in":8.5,   "depth_in":2.5, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","laser"]},
    {"id":"HD-7",     "family":"Hold-Down",        "code":"HD-7",     "description":"Hold-down, 3/4\" bolt, medium",     "width_in":3.0,   "height_in":11.0,  "depth_in":3.0, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","laser"]},
    {"id":"HD-10",    "family":"Hold-Down",        "code":"HD-10",    "description":"Hold-down, 1\" bolt, heavy",        "width_in":3.5,   "height_in":13.5,  "depth_in":3.5, "gauge":10, "material":"G90 galvanized steel", "machines":["punch","laser","plasma"]},
]

FAMILIES = sorted(set(c['family'] for c in CONNECTORS))
MACHINES  = sorted(set(m for c in CONNECTORS for m in c.get('machines',[])))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        family  = params.get('family', [''])[0].lower()
        machine = params.get('machine', [''])[0].lower()
        q       = params.get('q',      [''])[0].lower()

        results = CONNECTORS
        if family:  results = [c for c in results if c['family'].lower() == family]
        if machine: results = [c for c in results if machine in c.get('machines',[])]
        if q:       results = [c for c in results if q in c['code'].lower() or q in c['description'].lower()]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            'connectors': results,
            'families': FAMILIES,
            'machines': MACHINES,
            'total': len(results),
        }).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
