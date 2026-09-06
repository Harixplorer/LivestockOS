import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_list_sensors(client: AsyncClient, auth_headers):
    payload = {
        "sensor_id": "LOS-9901",
        "name": "LivestockOS_Sensor",
        "mac_address": "AA:BB:CC:DD:EE:01",
        "battery_level": 98
    }
    res = await client.post("/api/v1/sensors", json=payload, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["sensor_id"] == "LOS-9901"

    avail = await client.get("/api/v1/sensors/available", headers=auth_headers)
    assert avail.status_code == 200
    assert any(s["sensor_id"] == "LOS-9901" for s in avail.json())


@pytest.mark.asyncio
async def test_pair_and_unpair_sensor(client: AsyncClient, auth_headers):
    # Create animal
    animal_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-PAIR-1", "name": "Pair Cow", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )
    animal_id = animal_res.json()["id"]

    # Pair sensor
    pair_res = await client.post(
        f"/api/v1/animals/{animal_id}/pair-sensor",
        json={"sensor_id": "LOS-1001", "sensor_name": "Collar-1"},
        headers=auth_headers
    )
    assert pair_res.status_code == 200
    data = pair_res.json()
    assert data["paired_sensor_id"] == "LOS-1001"
    assert data["sensor_status"] == "ONLINE"

    # Unpair sensor
    unpair_res = await client.post(
        f"/api/v1/animals/{animal_id}/unpair-sensor",
        headers=auth_headers
    )
    assert unpair_res.status_code == 200
    unpaired_data = unpair_res.json()
    assert unpaired_data["paired_sensor_id"] is None
    assert unpaired_data["sensor_status"] == "NOT_PAIRED"


@pytest.mark.asyncio
async def test_cannot_pair_already_paired_sensor(client: AsyncClient, auth_headers):
    a1 = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-P1", "name": "Cow 1", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )
    a2 = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-P2", "name": "Cow 2", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )

    # Pair LOS-8888 to Cow 1
    p1 = await client.post(
        f"/api/v1/animals/{a1.json()['id']}/pair-sensor",
        json={"sensor_id": "LOS-8888"},
        headers=auth_headers
    )
    assert p1.status_code == 200

    # Attempt to pair LOS-8888 to Cow 2 -> should fail with 400
    p2 = await client.post(
        f"/api/v1/animals/{a2.json()['id']}/pair-sensor",
        json={"sensor_id": "LOS-8888"},
        headers=auth_headers
    )
    assert p2.status_code == 400
    assert "already paired" in p2.json()["message"].lower()
