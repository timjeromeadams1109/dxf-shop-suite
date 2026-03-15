"""Shared DXF utilities for serverless functions."""
import ezdxf
import io
import math
import json
from cgi import parse_header, parse_multipart


def parse_form_data(handler):
    """Parse multipart form data from a BaseHTTPRequestHandler."""
    content_type = handler.headers.get("Content-Type", "")
    content_length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(content_length)

    if "multipart/form-data" in content_type:
        _, params = parse_header(content_type)
        boundary = params.get("boundary", "")
        if isinstance(boundary, str):
            boundary = boundary.encode()
        environ = {
            "REQUEST_METHOD": "POST",
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(content_length),
        }
        # Use email parser approach
        from email.parser import BytesParser
        from email.policy import default as default_policy
        import re

        fields = {}
        files = {}

        # Manual multipart parse
        parts = body.split(b"--" + boundary)
        for part in parts:
            if part in (b"", b"--\r\n", b"--", b"\r\n"):
                continue
            part = part.strip(b"\r\n")
            if part == b"--":
                continue

            # Split headers from body
            if b"\r\n\r\n" in part:
                header_data, file_data = part.split(b"\r\n\r\n", 1)
            else:
                continue

            # Remove trailing boundary marker
            if file_data.endswith(b"\r\n"):
                file_data = file_data[:-2]

            headers_str = header_data.decode("utf-8", errors="replace")
            # Extract field name and filename
            name_match = re.search(r'name="([^"]*)"', headers_str)
            filename_match = re.search(r'filename="([^"]*)"', headers_str)

            if not name_match:
                continue

            field_name = name_match.group(1)

            if filename_match:
                fname = filename_match.group(1)
                if field_name in files:
                    if not isinstance(files[field_name], list):
                        files[field_name] = [files[field_name]]
                    files[field_name].append({"filename": fname, "data": file_data})
                else:
                    files[field_name] = {"filename": fname, "data": file_data}
            else:
                fields[field_name] = file_data.decode("utf-8", errors="replace")

        return fields, files

    return {}, {}


def read_dxf(file_data):
    """Read a DXF file from bytes, return ezdxf document."""
    stream = io.BytesIO(file_data)
    try:
        doc = ezdxf.read(stream)
    except Exception:
        stream.seek(0)
        doc = ezdxf.recover.readfile(stream)[0]
    return doc


def get_dxf_stats(doc):
    """Extract stats from a DXF document."""
    msp = doc.modelspace()
    entities = list(msp)
    entity_count = len(entities)

    # Count entity types
    spline_count = sum(1 for e in entities if e.dxftype() == "SPLINE")
    block_refs = sum(1 for e in entities if e.dxftype() == "INSERT")

    # Check for open contours (LWPOLYLINE/POLYLINE that aren't closed)
    open_contours = 0
    for e in entities:
        if e.dxftype() == "LWPOLYLINE":
            if not e.closed:
                open_contours += 1
        elif e.dxftype() == "POLYLINE":
            if not e.is_closed:
                open_contours += 1

    # DXF version
    dxf_version = doc.dxfversion

    # Estimate cut length
    cut_length = 0.0
    for e in entities:
        try:
            if e.dxftype() == "LINE":
                p1 = e.dxf.start
                p2 = e.dxf.end
                cut_length += math.dist((p1.x, p1.y), (p2.x, p2.y))
            elif e.dxftype() == "CIRCLE":
                cut_length += 2 * math.pi * e.dxf.radius
            elif e.dxftype() == "ARC":
                angle = abs(e.dxf.end_angle - e.dxf.start_angle)
                if angle < 0:
                    angle += 360
                cut_length += (angle / 360) * 2 * math.pi * e.dxf.radius
            elif e.dxftype() == "LWPOLYLINE":
                pts = list(e.get_points(format="xy"))
                for i in range(len(pts) - 1):
                    cut_length += math.dist(pts[i], pts[i + 1])
                if e.closed and len(pts) > 1:
                    cut_length += math.dist(pts[-1], pts[0])
        except Exception:
            pass

    return {
        "entity_count": entity_count,
        "open_contours": open_contours,
        "spline_count": spline_count,
        "block_refs": block_refs,
        "dxf_version": dxf_version,
        "estimated_cut_length": round(cut_length, 2),
    }


def get_bounding_box(doc):
    """Get bounding box of all entities."""
    msp = doc.modelspace()
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for e in msp:
        try:
            if e.dxftype() == "LINE":
                for p in [e.dxf.start, e.dxf.end]:
                    min_x = min(min_x, p.x)
                    min_y = min(min_y, p.y)
                    max_x = max(max_x, p.x)
                    max_y = max(max_y, p.y)
            elif e.dxftype() == "CIRCLE":
                cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                min_x = min(min_x, cx - r)
                min_y = min(min_y, cy - r)
                max_x = max(max_x, cx + r)
                max_y = max(max_y, cy + r)
            elif e.dxftype() == "LWPOLYLINE":
                for x, y in e.get_points(format="xy"):
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)
            elif e.dxftype() == "ARC":
                cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                min_x = min(min_x, cx - r)
                min_y = min(min_y, cy - r)
                max_x = max(max_x, cx + r)
                max_y = max(max_y, cy + r)
        except Exception:
            pass

    if min_x == float("inf"):
        return None

    return {
        "width": round(max_x - min_x, 3),
        "height": round(max_y - min_y, 3),
        "min_x": round(min_x, 3),
        "min_y": round(min_y, 3),
        "max_x": round(max_x, 3),
        "max_y": round(max_y, 3),
    }


def json_response(handler, data, status=200):
    """Send a JSON response."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())


def cors_preflight(handler):
    """Handle CORS preflight."""
    handler.send_response(204)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
