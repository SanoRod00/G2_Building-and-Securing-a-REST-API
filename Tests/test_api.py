"""Tests for REST API (server.py).

Start the server first in another terminal:
    python3 dsa/API/server.py
Then run these tests from the project root:
    python3 Tests/test_api.py
    """

import base64
from email.policy import HTTP
import http.client
import json
import unittest

from requests import request

HOST = "127.0.0.1"
PORT = 8000
USERNAME = "admin"
PASSWORD = "password123"


# A record that exists in output.json, and an ID that does not exist anywhere
EXISTING_ID = "76662021700"
MISSING_ID = "000000000"


# The record the tests create, change and delete
TEST_ID ="999000111"


def basic_auth_header(username, password):
    """Build the Authorization header value for basic Authentication."""
    credentials = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(credentials).decode("ascii")



def send_request(method, path, body=None, username=USERNAME, password=PASSWORD, send_auth=True, raw_body=None):
    """Send one HTTP request and return (status, headers, parsed JSON body)."""
    headers ={}
    if send_auth:
        headers["Authorization"]= basic_auth_header(username, password)



    payload = None
    if raw_body is not None:
        payload = raw_body.encode("utf-8")
        headers["Content_Type"] = "application/json"
    elif body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content_Type"] = "application/json"

    connection = http.client.HTTPConnection(HOST, PORT, timeout=5)
    connection.request(method, path, body=payload, headers=headers)
    response = connection.getresponse()
    text = response.read().decode("utf-8")
    connection.close()

    try:
        data = json.loads(text)
    except ValueError:
        data = None
    return response.status, response, data


class MoMoApiTests(unittest.TestCase):
    """Tests run in name order because some depend on each other."""

    @classmethod
    def setUpClass(cls):
        #Remove the test record if an earlier failed run left it behind.

        send_request("DELETE", f"/transactions/{TEST_ID}")

    # Authentication 

    def test_01_no_credentials_returns_401(self):
        for method in ["GET", "POST", "PUT", "DELETE"]:
            status, response, data = send_request(method, f"/transactions/{EXISTING_ID}", send_auth=False)
            self.assertEqual(status, 401, f"{method} without credentials")
            self.assertIn("error", data)


    def test_02_wrong_credentials_returns_401(self):
        status, response, data = send_request("GET", "/transactions", username="admin", password="wrong")
        self.assertEqual(status, 401)
        self.assertIn("Basic", response.getheader("WWW-Authenticate"))

    # GET 

    def test_03_get_all_transactions(self):
        status, response, data = send_request("GET", "/transactions")
        self.assertEqual(status, 200)
        self. assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


    def test_04_get_one_transaction(self):
        status, response, data = send_request("GET", f"/transactions/{EXISTING_ID}")
        self.assertEqual(status, 200)
        self.assertEqual(data["transaction_id"], EXISTING_ID)
        self.assertEqual(data["transaction_type"], "received")
        self.assertEqual(data["amount_rwf"], 2000)  



    def test_05_get_missing_transaction_returns_404(self):
        status, response, data = send_request("GET", f"/transanctions?{MISSING_ID}")
        self.assertEqual(status, 404)
        self.assertIn("error", data)

    # POST 

    def test_06_post_without_transaction_id_returns_400(self):
        status, response, data = send_request("POST", "/transactions", body={"amount_rwf": 500})
        self.assertEqual(status, 400)


    def test_07_post_invalid_json_returns_400(self):
        status, response, data = send_request("POST", "/transactions", body={"amount_rwf": 500})
        self.assertEqual(status, 400)


    def test_08_post_creates_transaction(self):
        new_record = {
            "transaction_id": TEST_ID,
            "transaction_type": "received", 
            "amount_rwf": 1500,
            "counterparty": "Test Person", 
            "body": "Created by the test script."
        } 
        status, response, data = send_request("POST", "/transactions", body=new_record)
        self.assertEqual(status, 201)
        self.assertEqual(data["transaction_id"], TEST_ID)
        self.assertEqual(data["amount_rwf"], 1500)

        status, reponse, data = send_request("GET", f"/transactions/{TEST_ID}")
        self.assertEqual(status, 200)


    def test_09_post_duplicate_id_returns_409(self):
        status, response, data = send_request("POST", "/transactions", body={"transaction_id": TEST_ID})
        self.assertEqual(status,409)

    # PUT 

    def test_10_put_updates_transaction(self):
        status, response, data = send_request("PUT", f"/transactions/{TEST_ID}", body={"amount_rwf": 9999})
        self.assertEqual(status, 200)
        self.assertEqual(data["amount_rwf"], 9999)
        self.assertEqual(data["counterparty"], "Test Person")


    def test_11_put_missing_transaction_returns_404(self):
        status, response, data = send_request("PUT", f"/transactions/{MISSING_ID}", body={"amount_rwf": 1})
        self.assertEqual(status, 404)


    # DELETE
     
    def test_12_delete_removes_transaction(self):
        status, response, data = send_request("DELETE", f"/transactions/{TEST_ID}")
        self.assertEqual(status, 200)
        self.assertIn("delete", data["message"])

    
        status, response, data = send_request("GET", f"/transactions/{TEST_ID}")
        self.assertEqual(status, 404)

    def test_13_delete_missing_transaction_returns_404(self):
        status, response, data = send_request("DELETE", f"/transactions/{MISSING_ID}")
        self.assertEqual(status, 404)



if __name__ == "__main__":
    unittest.main(verbosity=2)

   

