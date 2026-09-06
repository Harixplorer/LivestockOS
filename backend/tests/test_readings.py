import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_normal_reading(client: AsyncClient, auth_headers):
    # Register animal
    a_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-NORM", "name": "Normal Cow", "breed": "Gir", "age": 3, "gender": "FEMALE", "weight": 380},
        headers=auth_headers
    )
    animal_id = a_res.json()["id"]

    reading_payload = {
        "animal_id": animal_id,
        "temperature": 38.6,
        "activity_score": 75,
        "behavior": "Grazing",
        "rumination_mins": 25
    }
    res = await client.post("/api/v1/readings", json=reading_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["alert_generated"] is False
    assert data["alert_type"] is None
    assert data["health_score"] >= 80

    # Verify animal vitals updated
    animal_check = await client.get(f"/api/v1/animals/{animal_id}", headers=auth_headers)
    assert animal_check.status_code == 200
    a_data = animal_check.json()
    assert a_data["temperature"] == 38.6
    assert a_data["activity_level"] == 75
    assert a_data["rumination"] == 25
    assert a_data["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_submit_fever_reading_generates_alert(client: AsyncClient, auth_headers):
    a_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-FEVER", "name": "Sick Cow", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 340},
        headers=auth_headers
    )
    animal_id = a_res.json()["id"]

    fever_payload = {
        "animal_id": animal_id,
        "temperature": 40.8,
        "activity_score": 12,
        "behavior": "Idle",
        "rumination_mins": 5
    }
    res = await client.post("/api/v1/readings", json=fever_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["alert_generated"] is True
    assert data["alert_type"] == "HIGH_FEVER"
    assert data["health_score"] < 50

    # Verify alert exists in /alerts
    alerts_res = await client.get("/api/v1/alerts", headers=auth_headers)
    assert alerts_res.status_code == 200
    alerts_data = alerts_res.json()
    assert alerts_data["total"] >= 1
    assert any(a["alert_type"] == "HIGH_FEVER" for a in alerts_data["items"])


@pytest.mark.asyncio
async def test_get_reading_history(client: AsyncClient, auth_headers):
    a_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-HIST", "name": "History Cow", "breed": "Gir", "age": 3, "gender": "FEMALE", "weight": 380},
        headers=auth_headers
    )
    animal_id = a_res.json()["id"]

    for temp in [38.5, 38.6, 38.7]:
        await client.post(
            "/api/v1/readings",
            json={"animal_id": animal_id, "temperature": temp, "activity_score": 60, "behavior": "Idle", "rumination_mins": 20},
            headers=auth_headers
        )

    hist_res = await client.get(f"/api/v1/readings/{animal_id}?limit=2", headers=auth_headers)
    assert hist_res.status_code == 200
    readings = hist_res.json()
    assert len(readings) == 2
