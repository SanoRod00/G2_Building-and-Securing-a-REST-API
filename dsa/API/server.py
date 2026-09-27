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
    """HTTP Request Handler managing HTTP requests, Authentication, and CRUD endpoints."""

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

    def parse_json_body(self):
        """Extract and parse JSON request body."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return None
            body = self.rfile.read(content_length)
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    def clean_request_path(self):
        """Normalize URL path by stripping whitespace and trailing slashes."""
        clean_path = self.path.strip().rstrip("/")
        return clean_path if clean_path else "/"

    # --- HTTP READ METHODS ---

    def do_GET(self):
        """Handles GET requests for health check, listing records, and individual lookup."""
        if not self.check_authentication():
            return self._send_unauthorized()

        clean_path = self.clean_request_path()

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

    # --- HTTP WRITE METHODS ---

    def do_POST(self):
        """Handles POST /transactions to create a new transaction record."""
        if not self.check_authentication():
            return self._send_unauthorized()

        clean_path = self.clean_request_path()

        if clean_path == "/transactions":
            payload = self.parse_json_body()
            if not payload or not isinstance(payload, dict):
                return self._send_json_response(400, {"error": "Invalid or missing JSON payload."})

            tx_id = payload.get("transaction_id")
            if not tx_id:
                return self._send_json_response(400, {"error": "Field 'transaction_id' is required."})

            str_tx_id = str(tx_id)
            if str_tx_id in TRANSACTIONS_BY_ID:
                return self._send_json_response(
                    409, {"error": f"Transaction ID '{str_tx_id}' already exists."}
                )

            # Construct standardized record structure matching XML parsing format
            new_record = {
                "transaction_id": str_tx_id,
                "transaction_type": payload.get("transaction_type", "unparsed"),
                "amount_rwf": payload.get("amount_rwf"),
                "counterparty": payload.get("counterparty"),
                "body": payload.get("body", ""),
            }

            TRANSACTIONS.append(new_record)
            TRANSACTIONS_BY_ID[str_tx_id] = new_record

            return self._send_json_response(201, new_record)

        return self._send_json_response(404, {"error": f"Endpoint '{self.path}' not found"})

    def do_PUT(self):
        """Handles PUT /transactions/{id} to update an existing record."""
        if not self.check_authentication():
            return self._send_unauthorized()

        clean_path = self.clean_request_path()
        match = re.match(r"^/transactions/([^/]+)$", clean_path)

        if match:
            tx_id = match.group(1)
            transaction = TRANSACTIONS_BY_ID.get(tx_id)

            if not transaction:
                return self._send_json_response(404, {"error": f"Transaction '{tx_id}' not found."})

            payload = self.parse_json_body()
            if not payload or not isinstance(payload, dict):
                return self._send_json_response(400, {"error": "Invalid or missing JSON payload."})

            # Update present fields
            for key in ["transaction_type", "amount_rwf", "counterparty", "body"]:
                if key in payload:
                    transaction[key] = payload[key]

            return self._send_json_response(200, transaction)

        return self._send_json_response(404, {"error": f"Endpoint '{self.path}' not found"})

    def do_DELETE(self):
        """Handles DELETE /transactions/{id} to remove a transaction record."""
        if not self.check_authentication():
            return self._send_unauthorized()

        clean_path = self.clean_request_path()
        match = re.match(r"^/transactions/([^/]+)$", clean_path)

        if match:
            tx_id = match.group(1)
            transaction = TRANSACTIONS_BY_ID.get(tx_id)

            if not transaction:
                return self._send_json_response(404, {"error": f"Transaction '{tx_id}' not found."})

            TRANSACTIONS.remove(transaction)
            del TRANSACTIONS_BY_ID[tx_id]

            return self._send_json_response(
                200, {"message": f"Transaction '{tx_id}' deleted successfully."}
            )

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