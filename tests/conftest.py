import pytest

from fastapi.testclient import TestClient
from app.main import app

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from sqlalchemy import text

from app.models.account import Account
from app.models.user import User
from app.models.transfer import Transfer
from app.models.ledger_entry import LedgerEntry

from uuid import uuid4

TEST_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database="transferflow_test",
)

if TEST_DATABASE_URL.database != "transferflow_test":
    raise RuntimeError("Refusing to use non_test database")

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(bind=test_engine)

with test_engine.connect() as connection:
    database_name = connection.execute(
        text("select current_database()")
    ).scalar_one()

    if database_name != "transferflow_test":
        raise RuntimeError(
            f"Unsafe database connection: {database_name}"
        )

def get_test_db():
    test_db = TestingSessionLocal()
    try:
        yield test_db
    finally:
        test_db.close()

@pytest.fixture(scope="session")
def db_engine():
    return test_engine

@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    Base.metadata.create_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_connection():
    connection = test_engine.connect()
    transaction = connection.begin()

    try:
        yield connection
    finally:
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def db_session(db_connection):

    sesion = TestingSessionLocal(
        bind=db_connection,
        join_transaction_mode ="create_savepoint"
        )

    try:
        yield sesion
    finally:
        sesion.close()

@pytest.fixture(scope="function")
def client(db_session):

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)

@pytest.fixture(scope="function")
def user_factory(client):

    def create_user():
        email = f"test_{uuid4().hex}@example.com"

        response = client.post(
            "/users/",
                json = {
                    "full_name": "Test User",
                    "email": email,
                    "password": "Testpassword123!"
                }
            )

        assert response.status_code == 201
        return {
            "email": email,
            "password": "Testpassword123!"
        }

    return create_user

@pytest.fixture(scope="function")
def auth_headers(client, user_factory):

    def create_auth_headers():
        user = user_factory()

        response = client.post(
            "/auth/login",
            json={
                "email": user["email"],
                "password": user["password"]
            }
        )

        assert response.status_code == 200, response.text

        token = response.json()["access_token"]

        return {
            "Authorization": f"Bearer {token}"
            }

    return create_auth_headers















