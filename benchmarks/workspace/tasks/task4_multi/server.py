"""server.py — 小型 Web 项目入口（Task 4: 新增 /health 接口）"""
import json

from http.server import BaseHTTPRequestHandler, HTTPServer

from db import get_items
from api import list_api, create_api


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send(200, {"service": "demo-api", "items": get_items()})
        elif self.path == "/api/items":
            self._send(200, list_api())
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/items":
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length)) if length else {}
            self._send(201, create_api(data))
        else:
            self._send(404, {"error": "not found"})


def run(port=8080):
    print(f"starting server on :{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    import sys
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 8080)