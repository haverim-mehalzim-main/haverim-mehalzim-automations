import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}

        # Monday sends a challenge on webhook creation — must echo it back
        if "challenge" in data:
            self._respond(200, {"challenge": data["challenge"]})
            return

        item_id = str(data.get("event", {}).get("pulseId", ""))
        if not item_id:
            self._respond(400, {"error": "no pulseId in payload"})
            return

        self._trigger_github(item_id)
        self._respond(200, {"ok": True})

    def _trigger_github(self, item_id):
        token = os.environ["GITHUB_PAT"]
        repo  = os.environ["GITHUB_REPO"]

        payload = json.dumps({
            "event_type": "volunteer-registration",
            "client_payload": {"item_id": item_id},
        }).encode()

        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/dispatches",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        urllib.request.urlopen(req)

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, format, *args):
        pass
