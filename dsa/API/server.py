# Step 1: HTTP Server Base Setup & Dataset Ingestion
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# Server Configuration
PORT = 8000

# In-memory primary storage (list) and indexed lookup (dict)
TRANSACTIONS = []
TRANSACTIONS_BY_ID = {}

def load_initial_data():
    """Load parsed transactions from JSON output into memory and build dictionary index."""
    global TRANSACTIONS, TRANSACTIONS_BY_ID

    # Resolve paths to locate output.json regardless of execution context
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

            # Build Hash Map index: mapping string transaction_id -> record dictionary
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
    """HTTP Request Handler managing HTTP requests."""

    def _send_json_response(self, status_code, data):
        """Helper to format and output JSON HTTP responses."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        """Basic test route for Step 1 verification."""
        if self.path == "/health":
            return self._send_json_response(200, {"status": "healthy", "records_loaded": len(TRANSACTIONS)})
        return self._send_json_response(404, {"error": "Endpoint not found"})


def main():
    load_initial_data()
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, MoMoAPIHandler)
    print(f"[*] MoMo API Server running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped cleanly.")


if __name__ == "__main__":
    main()

# Step 2: Basic Authentication Middleware

