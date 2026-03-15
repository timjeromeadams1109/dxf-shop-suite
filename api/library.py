from http.server import BaseHTTPRequestHandler
import json
import uuid
import os
from urllib.parse import urlparse, parse_qs
from api._dxf_utils import parse_form_data, read_dxf, get_dxf_stats, get_bounding_box, json_response, cors_preflight

# In-memory library (resets on cold start — serverless limitation)
# For persistence, this would need a database (Supabase, etc.)
_library = {}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        name_filter = params.get("name", [""])[0].lower()
        machine_filter = params.get("machine", [""])[0].lower()

        parts = []
        for part_id, part in _library.items():
            if name_filter and name_filter not in part["name"].lower():
                continue
            if machine_filter and machine_filter != part["machine"].lower():
                continue
            parts.append({**part, "id": part_id})

        json_response(self, {"parts": parts})

    def do_POST(self):
        try:
            fields, files = parse_form_data(self)
            file_info = files.get("file")

            part_id = str(uuid.uuid4())[:8]
            stats = None
            bb = None

            if file_info:
                doc = read_dxf(file_info["data"])
                stats = get_dxf_stats(doc)
                bb = get_bounding_box(doc)

            _library[part_id] = {
                "name": fields.get("name", "Unnamed"),
                "machine": fields.get("machine", ""),
                "material": fields.get("material", ""),
                "thickness": fields.get("thickness", ""),
                "notes": fields.get("notes", ""),
                "stats": {**(stats or {}), "bounding_box": bb},
            }

            json_response(self, {"id": part_id, "message": "Part added"})
        except Exception as e:
            json_response(self, {"error": str(e)}, 500)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        # Path will be /api/library/PART_ID
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 3:
            part_id = path_parts[-1]
            if part_id in _library:
                del _library[part_id]
                json_response(self, {"message": "Part deleted"})
            else:
                json_response(self, {"error": "Part not found"}, 404)
        else:
            json_response(self, {"error": "No part ID provided"}, 400)

    def do_OPTIONS(self):
        cors_preflight(self)
