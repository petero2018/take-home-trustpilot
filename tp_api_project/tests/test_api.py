import pytest
from app import queries
from app.exceptions import DataAccessError, RecordNotFoundError
from app.main import app
from fastapi.testclient import TestClient
from mockito import unstub, when


@pytest.fixture(autouse=True)
def _reset_mocks():
    try:
        yield
    finally:
        unstub()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as client:
        yield client


def test_healthcheck(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reviews_by_business_success(client: TestClient) -> None:
    rows = [("foo", "bar")]
    header = ["col_a", "col_b"]
    when(queries).get_reviews_by_business("biz-1", 100, 0).thenReturn((rows, header))

    response = client.get(
        "/reviews/by-business",
        params={"business_id": "biz-1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text == "col_a,col_b\r\nfoo,bar\r\n"


def test_reviews_by_user_success(client: TestClient) -> None:
    rows = [("foo", "bar")]
    header = ["col_a", "col_b"]
    when(queries).get_reviews_by_user("user-1", 100, 0).thenReturn((rows, header))

    response = client.get(
        "/reviews/by-user",
        params={"user_id": "user-1"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text == "col_a,col_b\r\nfoo,bar\r\n"


def test_reviews_by_business_not_found(client: TestClient) -> None:
    when(queries).get_reviews_by_business("missing", 100, 0).thenRaise(
        RecordNotFoundError(
            "No reviews were found for the requested business.",
            context={"business_id": "missing"},
        )
    )

    response = client.get(
        "/reviews/by-business",
        params={"business_id": "missing"},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["detail"] == "No reviews were found for the requested business."
    assert payload["context"]["business_id"] == "missing"


def test_reviews_by_business_error(client: TestClient) -> None:
    when(queries).get_reviews_by_business("fail", 100, 0).thenRaise(
        DataAccessError(
            "Unable to retrieve reviews for the requested business.",
            context={"business_id": "fail"},
        )
    )

    response = client.get(
        "/reviews/by-business",
        params={"business_id": "fail"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Unable to retrieve reviews for the requested business."
    assert payload["context"]["business_id"] == "fail"


def test_reviews_by_user_not_found(client: TestClient) -> None:
    when(queries).get_reviews_by_user("missing", 100, 0).thenRaise(
        RecordNotFoundError(
            "No reviews were found for the requested user.",
            context={"user_id": "missing"},
        )
    )

    response = client.get(
        "/reviews/by-user",
        params={"user_id": "missing"},
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["detail"] == "No reviews were found for the requested user."
    assert payload["context"]["user_id"] == "missing"


def test_reviews_by_user_error(client: TestClient) -> None:
    when(queries).get_reviews_by_user("fail", 100, 0).thenRaise(
        DataAccessError(
            "Unable to retrieve reviews for the requested user.",
            context={"user_id": "fail"},
        )
    )

    response = client.get(
        "/reviews/by-user",
        params={"user_id": "fail"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Unable to retrieve reviews for the requested user."
    assert payload["context"]["user_id"] == "fail"


def test_user_info_success(client: TestClient) -> None:
    rows = [("user-1", "Alice", "alice@example.com", "UK")]
    header = ["reviewer_id", "reviewer_name", "email_address", "reviewer_country"]
    when(queries).get_user_info("user-1").thenReturn((rows, header))

    response = client.get("/users/user-1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text == (
        "reviewer_id,reviewer_name,email_address,reviewer_country\r\n"
        "user-1,Alice,alice@example.com,UK\r\n"
    )


def test_reviews_by_business_validation_error(client: TestClient) -> None:
    response = client.get(
        "/reviews/by-business",
        params={"business_id": "biz-1", "limit": 0},
    )

    assert response.status_code == 422


def test_user_info_not_found(client: TestClient) -> None:
    when(queries).get_user_info("missing").thenRaise(
        RecordNotFoundError(
            "No user information was found for the requested user.",
            context={"user_id": "missing"},
        )
    )

    response = client.get("/users/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["detail"] == "No user information was found for the requested user."
    assert payload["context"]["user_id"] == "missing"


def test_user_info_error(client: TestClient) -> None:
    when(queries).get_user_info("fail").thenRaise(
        DataAccessError(
            "Unable to retrieve user information.",
            context={"user_id": "fail"},
        )
    )

    response = client.get("/users/fail")

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Unable to retrieve user information."
    assert payload["context"]["user_id"] == "fail"
