"""
Pytest configuration and fixtures for RailFleet Manager tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.core.database import Base, get_db
from src.app import app
from src.models.railfleet import User
import os


# Test database URL (use separate test database)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://railfleet:railfleet@localhost:5432/railfleet_test"
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # Override get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # Rollback and close
    session.rollback()
    session.close()

    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db):
    """Create test user."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email="test@railfleet.com",
        username="testuser",
        hashed_password=pwd_context.hash("test123"),
        full_name="Test User",
        role="MANAGER",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(client, test_user):
    """Get authentication token."""
    response = client.post("/api/v1/auth/login", data={
        "username": "test@railfleet.com",
        "password": "test123"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


# ===== Sample Data Fixtures =====

@pytest.fixture
def sample_part(test_db, auth_headers, client):
    """Create sample part for testing."""
    part_data = {
        "part_no": "TEST-PART-001",
        "name": "Test Part",
        "railway_class": "STANDARD",
        "unit": "pc",
        "min_stock": 5,
        "current_stock": 10,
        "unit_price": 50.00,
        "is_active": True
    }
    response = client.post("/api/v1/parts", json=part_data, headers=auth_headers)
    if response.status_code == 201:
        return response.json()
    return None


@pytest.fixture
def sample_location(test_db, auth_headers, client):
    """Create sample stock location for testing."""
    location_data = {
        "location_code": "TEST-LOC-001",
        "name": "Test Location",
        "location_type": "WORKSHOP",
        "is_active": True
    }
    response = client.post("/api/v1/stock/locations", json=location_data, headers=auth_headers)
    if response.status_code == 201:
        return response.json()
    return None


@pytest.fixture
def sample_supplier(test_db, auth_headers, client):
    """Create sample supplier for testing."""
    supplier_data = {
        "supplier_code": "TEST-SUP-001",
        "name": "Test Supplier",
        "email": "test@supplier.com",
        "payment_terms": "NET30",
        "is_active": True
    }
    response = client.post("/api/v1/suppliers", json=supplier_data, headers=auth_headers)
    if response.status_code == 201:
        return response.json()
    return None


# ===== Performance Test Helpers =====

@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests."""
    metrics = {
        "timings": [],
        "queries": [],
        "memory": []
    }
    return metrics


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
