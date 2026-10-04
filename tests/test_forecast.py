from fastapi.testclient import TestClient
from demand.main import app

client = TestClient(app)


def test_moving_average():
    payload = client.post("/forecast", json={"series": [8, 10, 12, 14, 16]}).json()
    assert payload["next"] == 13.0


def test_short_series_is_refused():
    assert client.post("/forecast", json={"series": [1]}).status_code == 422
