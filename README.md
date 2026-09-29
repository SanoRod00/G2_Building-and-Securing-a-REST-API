# MoMo SMS Transactions API

This project parses MoMo SMS messages into transaction records and provides a Python REST API for reading and managing those records. The dataset is generated from `modified_sms_v2-1.xml` and stored in `dsa/output.json`.

## Start the server

From the repository root, run:

```bash
python3 api/server.py
```

The API listens on `http://localhost:8000`. Keep the server running in its terminal while using the API or running the tests.

## Run the tests

In a second terminal, from the repository root, run:

```bash
python3 Tests/test_api.py
```

The tests expect the API server to be running on port 8000.

## Project report

The complete API security and DSA report is available as a [PDF](docs/report_security_and_dsa.pdf).

Transaction data is stored in memory and resets when the server restarts.
