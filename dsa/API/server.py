# Step 1: HTTP Server Base Setup & Dataset Ingestion
import base64
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

# Server Configuration & Auth Credentials
PORT = 8000
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "password123"

# In-memory primary storage (list) and indexed lookup (dict)
TRANSACTIONS = []
TRANSACTIONS_BY_ID = {}


def load_initial_data():
    """Load parsed transactions from JSON output into memory and build dictionary index."""
    global TRANSACTIONS, TRANSACTIONS_BY_ID

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)

    possible_paths = [
        os.path.join(script_dir, "output.json"),
        os.path.join(project_dir, "dsa", "output.json"),
        os.path.join(os.getcwd(), "output.json"),
        os.path.join(os.getcwd(), "dsa", "output.json"),
    ]

    json_path = None
    for path in possible_paths:
        if os.path.exists(path):
            json_path = path
            break

    if json_path:
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                TRANSACTIONS = json.load(file)

            TRANSACTIONS_BY_ID = {
                str(record["transaction_id"]): record
                for record in TRANSACTIONS
                if record.get("transaction_id") is not None
            }
            print(
                f"[+] Dataset loaded successfully: {len(TRANSACTIONS)} records "
                f"({len(TRANSACTIONS_BY_ID)} indexed by transaction ID)."
            )
        except Exception as error:
            print(f"[-] Error loading JSON file: {error}")
            TRANSACTIONS = []
            TRANSACTIONS_BY_ID = {}
    else:
        print("[-] Warning: output.json not found. Starting with empty dataset.")


class MoMoAPIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler managing HTTP requests and Authentication."""

    def _send_json_response(self, status_code, data):
        """Helper to format and output JSON HTTP responses."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def _send_unauthorized(self):
        """Helper to return a standard 401 Unauthorized response with WWW-Authenticate header."""
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="MoMo Rest API"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        response = {"error": "Unauthorized. Missing or invalid Basic Authentication credentials."}
        self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

    def check_authentication(self):
        """Validate Basic Authentication header credentials."""
        auth_header = self.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return False

        try:
            encoded_credentials = auth_header.split(" ", 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
            return username == AUTH_USERNAME and password == AUTH_PASSWORD
        except Exception:
            return False

    def do_GET(self):
        """Handles GET requests for health check, listing records, and individual lookup."""
        if not self.check_authentication():
            return self._send_unauthorized()

        # Clean raw path (strips trailing slashes/spaces)
        clean_path = self.path.strip().rstrip("/")
        if not clean_path:
            clean_path = "/"

        # Debug print in server console
        print(f"[*] Incoming GET request path: '{self.path}' -> cleaned: '{clean_path}'")

        # Route: GET /health
        if clean_path == "/health":
            return self._send_json_response(200, {"status": "healthy", "authenticated": True})

        # Route: GET /transactions
        if clean_path == "/transactions":
            return self._send_json_response(200, TRANSACTIONS)

        # Route: GET /transactions/{id}
        match = re.match(r"^/transactions/([^/]+)$", clean_path)
        if match:
            tx_id = match.group(1)
            transaction = TRANSACTIONS_BY_ID.get(tx_id)
            if transaction:
                return self._send_json_response(200, transaction)
            return self._send_json_response(404, {"error": f"Transaction '{tx_id}' not found."})

        return self._send_json_response(404, {"error": f"Endpoint '{self.path}' not found"})


def main():
    load_initial_data()
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, MoMoAPIHandler)
    print(f"[*] MoMo API Server running on http://localhost:{PORT}")
    print(f"[*] Basic Auth Credentials -> Username: '{AUTH_USERNAME}', Password: '{AUTH_PASSWORD}'")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped cleanly.")


if __name__ == "__main__":
    main()