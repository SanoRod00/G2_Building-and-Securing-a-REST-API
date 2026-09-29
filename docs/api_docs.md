# MoMo SMS Transactions API Documentation

AREST API built with Python's `http.server` that exposes MoMo SMS transactions parsed from `modified_sms_v2-1.xml`. Data is held in memory and is reloaded from `output.json`each time the server starts, so changes made through the API are lost on restart.

## Base URL

```
http://localhost:8000
```

Start the server from the `api/` folder with `python3 server.py`.

## Authentication 

Every endpoint is protected with **HTTP Basic Authentication***. Each request must include an `Authorization` header containing `Basic` followed by the Base64 encoding of `username:password`.

| Setting  | Value         |
|----------|---------------|
| Username | `admin`       |
| password | `password123` |

With curl thr `-u admin:password123` option builds the header automatically. A missing or invalid header returns `401 Unauthorized` (see [Error codes] (#error-codes)).

## Transaction object

| Field              | Type           | Description
|--------------------|----------------|-------------------------------------------------------------------------------|
| `transaction_id`   | String or null | Transaction ID stated in the SMS. `null`for messages that do not state one.   |
| `transaction_type` | String         | One of `received`, `payment`, `transfer`, `bank_deposit`, `direct_payment`, `bundle_purchase`, `withdrawal`, `authentication_code`, `unparsed` |                                                                            
| `amount_rwf`       | Integer or null| Amount in Rwandan francs, when the message states one    |                              
| `counterparty`     | String or null | Person or business named in the SMS, when there is one.                        |                                                                
| `body`             | String         | Original SMS text

The dataset holds 1,691 records. Of these, 823 have a `transaction_id` and can be read, updated or deleted individually. The other 868 appear only in the `GET /transactions` list.
 
## Endpoints
 
| Method | Path                     | Description                   | Success code |
|--------|--------------------------|-------------------------------|--------------|
| GET    | `/transactions`          | List all transactions         | 200          |
| GET    | `/transactions/{id}`     | Get one transaction           | 200          |
| POST   | `/transactions`          | Create a transaction          | 201          |
| PUT    | `/transactions/{id}`     | Update an existing transaction| 200          |
| DELETE | `/transactions/{id}`     | Delete a transaction          | 200          |
| GET    | `/health`                | Check that the server is up   | 200          |
 
---
 
### GET /transactions
 
Returns every transaction as a JSON array. There is no pagination, so the response is large (1,691 records at startup).
 
**Request**
 
```bash
curl -u admin:password123 http://localhost:8000/transactions
```
 
**Response** `200 OK` (first element shown)
 
```json
[
  {
    "transaction_id": "76662021700",
    "transaction_type": "received",
    "amount_rwf": 2000,
    "counterparty": "Jane Smith",
    "body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700."
  }
]
```
 
**Errors:** `401`
 
---
 
### GET /transactions/{id}
 
Returns the single transaction whose `transaction_id` matches `{id}`.
 
**Request**
 
```bash
curl -u admin:password123 http://localhost:8000/transactions/76662021700
```
 
**Response** `200 OK`
 
```json
{
  "transaction_id": "76662021700",
  "transaction_type": "received",
  "amount_rwf": 2000,
  "counterparty": "Jane Smith",
  "body": "You have received 2000 RWF from Jane Smith (*********013) on your mobile money account at 2024-05-10 16:30:51. Message from sender: . Your new balance:2000 RWF. Financial Transaction Id: 76662021700."
}
```
 
**Error response** `404 Not Found` (unknown ID)
 
```json
{
  "error": "Transaction '000000000' not found."
}
```
 
**Errors:** `401`, `404`
 
---
 
### POST /transactions
 
Creates a new transaction. The request body must be JSON and must contain `transaction_id`. Missing optional fields default to `"unparsed"` for `transaction_type`, `null` for `amount_rwf` and `counterparty`, and an empty string for `body`. The `transaction_id` is stored as a string.
 
**Request**
 
```bash
curl -u admin:password123 -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"999000111","transaction_type":"received","amount_rwf":1500,"counterparty":"Test Person","body":"Demo"}'
```
 
**Response** `201 Created`
 
```json
{
  "transaction_id": "999000111",
  "transaction_type": "received",
  "amount_rwf": 1500,
  "counterparty": "Test Person",
  "body": "Demo"
}
```
 
**Error response** `400 Bad Request` (no `transaction_id`)
 
```json
{
  "error": "Field 'transaction_id' is required."
}
```
 
**Error response** `409 Conflict` (ID already exists)
 
```json
{
  "error": "Transaction ID '999000111' already exists."
}
```
 
**Errors:** `400`, `401`, `409`
 
---
 
### PUT /transactions/{id}
 
Updates an existing transaction. Only the fields sent in the body are changed, and the other fields keep their values. The fields that can be updated are `transaction_type`, `amount_rwf`, `counterparty` and `body`. The `transaction_id` cannot be changed.
 
**Request**
 
```bash
curl -u admin:password123 -X PUT http://localhost:8000/transactions/999000111 \
  -H "Content-Type: application/json" \
  -d '{"amount_rwf":9999}'
```
 
**Response** `200 OK`
 
```json
{
  "transaction_id": "999000111",
  "transaction_type": "received",
  "amount_rwf": 9999,
  "counterparty": "Test Person",
  "body": "Demo"
}
```
 
**Error response** `404 Not Found` (unknown ID)
 
```json
{
  "error": "Transaction '000000000' not found."
}
```
 
**Errors:** `400` (missing or invalid JSON body), `401`, `404`
 
---
 
### DELETE /transactions/{id}
 
Removes the transaction with the given ID.
 
**Request**
 
```bash
curl -u admin:password123 -X DELETE http://localhost:8000/transactions/999000111
```
 
**Response** `200 OK`
 
```json
{
  "message": "Transaction '999000111' deleted successfully."
}
```
 
**Error response** `404 Not Found` (unknown ID)
 
```json
{
  "error": "Transaction '000000000' not found."
}
```
 
**Errors:** `401`, `404`
 
---
 
### GET /health
 
Confirms the server is running and the credentials are accepted.
 
**Request**
 
```bash
curl -u admin:password123 http://localhost:8000/health
```
 
**Response** `200 OK`
 
```json
{
  "status": "healthy",
  "authenticated": true
}
```
 
---
 
## Error codes
 
Error responses are JSON objects with a single `error` field, as in the examples above.
 
| Code | Meaning              | When it happens                                                                                                  |
|------|----------------------|------------------------------------------------------------------------------------------------------------------|
| 400  | Bad Request          | POST or PUT body is missing, is not valid JSON, or is not a JSON object; POST body has no `transaction_id`.      |
| 401  | Unauthorized         | The `Authorization` header is missing or the username or password is wrong. The response includes a `WWW-Authenticate: Basic realm="MoMo Rest API"` header. |
| 404  | Not Found            | The transaction ID does not exist, or the path is not a known endpoint.                                          |
| 409  | Conflict             | POST used a `transaction_id` that already exists.                                                                |
| 501  | Not Implemented      | An HTTP method the server does not handle, such as PATCH.                                                        |
 
**401 example**
 
```bash
curl -i -u admin:wrong http://localhost:8000/transactions
```
 
```
HTTP/1.0 401 Unauthorized
WWW-Authenticate: Basic realm="MoMo Rest API"
 
{
  "error": "Unauthorized. Missing or invalid Basic Authentication credentials."
}
```
 
Authentication is checked before anything else, so an unauthenticated request receives `401` even when the path or the body would also be invalid.
 
## Testing
 
The automated tests in `Tests/test_api.py` cover all endpoints and the error codes above. Start the server, then run `python3 Tests/test_api.py` from the project root. Screenshots of manual curl requests are in the `screenshots/` folder.
