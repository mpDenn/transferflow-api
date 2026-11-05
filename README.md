# TransferFlow API

**A banking-inspired REST API built with Python, FastAPI, PostgreSQL, and SQLAlchemy.**

TransferFlow is a backend portfolio project designed to explore the engineering challenges behind reliable money transfers, transactional consistency, concurrency control, and idempotent API operations.

The application supports user authentication, bank accounts, account-to-account transfers, and a double-entry ledger that records the movement of funds.

> **Disclaimer:** TransferFlow is an educational project. It is not a production-ready banking platform or payment processing service.

---

## Key Features

- **JWT Authentication** — secure user authentication with hashed passwords and protected endpoints.
- **Account Management** — create and retrieve user-owned accounts with unique 12-digit account numbers.
- **Atomic Transfers** — update account balances, persist transfers, and create ledger entries within a single database transaction.
- **Concurrency Control** — PostgreSQL row-level locking using `SELECT ... FOR UPDATE`.
- **Deadlock Risk Reduction** — accounts are locked in a consistent order based on account IDs.
- **Idempotency** — prevent duplicate transfers using the `Idempotency-Key` header.
- **Double-Entry Ledger** — create matching DEBIT and CREDIT records for completed transfers.
- **Financial Precision** — use `Decimal` and PostgreSQL `NUMERIC(18,2)` instead of floating-point arithmetic.
- **Transfer History** — retrieve accessible transfers with pagination.
- **Database Migrations** — manage schema changes with Alembic.
- **Interactive Documentation** — automatically generated Swagger UI.

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python |
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Authentication | JWT, PyJWT |
| Password Security | pwdlib |
| Migrations | Alembic |
| Database Driver | psycopg 3 |
| ASGI Server | Uvicorn |

## Architecture

TransferFlow follows a layered architecture that separates HTTP handling, business logic, and database persistence.

```text
transferflow-api/
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── account.py
│   │   ├── transfer.py
│   │   └── ledger_entry.py
│   ├── routers/
│   │   ├── users.py
│   │   ├── auth.py
│   │   ├── accounts.py
│   │   └── transfers.py
│   ├── schemas/
│   ├── services/
│   │   ├── user_service.py
│   │   ├── auth_service.py
│   │   ├── account_service.py
│   │   └── transfer_service.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── security.py
│   └── main.py
├── alembic/
├── requirements.txt
├── .env.example
└── README.md
```

### Request Flow

```text
Client
  |
  v
FastAPI Router
  |
  v
Authentication & Validation
  |
  v
Service Layer
  |
  v
SQLAlchemy ORM
  |
  v
PostgreSQL
```

**Routers** handle HTTP requests, authentication dependencies, and response mapping.

**Services** implement business rules, transfer processing, idempotency, and transaction handling.

**Models** define database entities and relationships.

**Schemas** validate incoming requests and serialize API responses.

## Transfer Processing

The transfer service is designed around transactional consistency.

### Transfer Lifecycle

1. Identify and lock the source and destination accounts.
2. Verify that the authenticated user owns the source account.
3. Check whether the idempotency key has already been used.
4. Validate account status, currencies, and available funds.
5. Deduct the amount from the source account.
6. Credit the destination account.
7. Persist the transfer and create two ledger entries.
8. Commit all changes within a single transaction.

If a persistence error occurs, the transaction is rolled back.

### Concurrency Control

Account rows are locked using PostgreSQL:

```python
select(Account)
    .where(...)
    .order_by(Account.id)
    .with_for_update()
```

The consistent lock order reduces the risk of deadlocks during concurrent transfers.

This is important when multiple requests attempt to modify the same account balances.

### Atomicity

A successful transfer updates all related records together:

```text
BEGIN TRANSACTION
    |
    |-- Lock accounts
    |-- Validate transfer
    |-- Update sender balance
    |-- Update recipient balance
    |-- Insert transfer record
    |-- Insert DEBIT ledger entry
    |-- Insert CREDIT ledger entry
    |
COMMIT
```

If the operation fails before the transaction is committed, its database changes can be rolled back.

## Double-Entry Ledger

Each completed transfer generates two ledger entries.

Example: transferring **£100** from Account A to Account B.

| Account | Entry Type | Amount |
|---|---|---|
| Account A | DEBIT | £100.00 |
| Account B | CREDIT | £100.00 |

Both entries reference the same transfer.

The ledger records the direction of fund movement using the entry type rather than negative amounts.

The current ledger implementation provides transfer-level accounting records. Additional reconciliation and integrity constraints are planned.

## Idempotency

TransferFlow uses an `Idempotency-Key` request header to identify repeated transfer requests.

Example:

```http
Idempotency-Key: payment-001
```

### Expected Behavior

**First request:** Process the transfer and save its idempotency key.

**Repeated request with matching details:** Return the existing transfer without moving funds again.

**Repeated key with different transfer details:** Reject the request with `409 Conflict`.

A unique database constraint on the idempotency key provides an additional safeguard against duplicate records.

The current implementation uses globally unique keys within the transfer table.

## API Endpoints

### Users & Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/users/` | Register a user |
| POST | `/auth/login` | Authenticate and receive JWT |
| GET | `/users/me` | Retrieve the authenticated user |

### Accounts

| Method | Endpoint | Description |
|---|---|---|
| POST | `/accounts/` | Create a new bank account |
| GET | `/accounts/` | Retrieve the user's accounts |

### Transfers

| Method | Endpoint | Description |
|---|---|---|
| POST | `/transfers/` | Create a transfer |
| GET | `/transfers/` | Retrieve transfer history |
| GET | `/transfers/{transfer_id}` | Retrieve a specific accessible transfer |

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Application health response |

### Pagination

Transfer history supports `limit` and `offset` query parameters.

```http
GET /transfers/?limit=20&offset=0
```

The maximum supported `limit` is 100.

## Example API Usage

### 1. Register a User

`POST /users/`

```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

### 2. Authenticate

`POST /auth/login`

```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

Example response:

```json
{
  "access_token": "<jwt_access_token>",
  "token_type": "bearer"
}
```

Protected endpoints require:

```http
Authorization: Bearer <jwt_access_token>
```

### 3. Create an Account

`POST /accounts/`

```json
{
  "currency": "GBP"
}
```

New accounts start with a zero balance and receive a generated 12-digit account number.

### 4. Create a Transfer

`POST /transfers/`

Headers:

```http
Authorization: Bearer <jwt_access_token>
Idempotency-Key: transfer-demo-001
Content-Type: application/json
```

Request body:

```json
{
  "from_account_id": 1,
  "to_account_number": "012345678901",
  "amount": "25.00"
}
```

The destination is identified by its 12-digit account number, not its internal database ID.

### Transfer Validation

The API handles common business errors such as:

| Scenario | HTTP Status |
|---|---|
| Source or destination account not found | 404 |
| Transfer to the same account | 400 |
| Currency mismatch | 400 |
| Insufficient funds | 409 |
| Inactive account | 409 |
| Idempotency conflict | 409 |
| Invalid request data | 422 |

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/mpDenn/transferflow-api.git
cd transferflow-api
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Activate on Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and configure your local environment:

```dotenv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=transferflow

JWT_SECRET_KEY=replace_with_a_secure_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Create the `transferflow` database in PostgreSQL before running migrations.

Never commit real secrets or passwords.

### 5. Run Database Migrations

```bash
python -m alembic upgrade head
```

### 6. Start the Application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

**Note:** New accounts start at zero balance. The project does not yet include a deposit endpoint. Successful transfer scenarios require funded accounts in a controlled local development environment.

## Development Status

The core transfer workflow, JWT authentication, row-level locking, idempotency, ledger entries, and database migrations are implemented.

Manual integration checks have been performed using Swagger UI and PostgreSQL.

### Planned Improvements

- Automated integration tests with pytest.
- Dedicated test database and isolated fixtures.
- Concurrent transfer and rollback tests.
- Stronger ledger integrity checks and reconciliation.
- Controlled account funding workflows.
- Docker and Docker Compose support.
- GitHub Actions CI pipeline.
- Deployment configuration and production hardening.

## Engineering Focus

This project demonstrates practical backend engineering concepts:

- REST API development and request validation.
- Transaction management and atomic database operations.
- Concurrency control and deadlock risk reduction.
- Idempotent operations and duplicate prevention.
- Financial data precision.
- Authentication and ownership-based authorization.
- Layered backend architecture.
- Database schema evolution with Alembic.

## Author

Developed by **[mpDenn](https://github.com/mpDenn)** as a Python backend portfolio project.

Repository: [TransferFlow API](https://github.com/mpDenn/transferflow-api)