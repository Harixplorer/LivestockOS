import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_animal_pending_state(client: AsyncClient, auth_headers):
    payload = {
        "tag_id": "TAG-DAISY",
        "name": "Daisy",
        "breed": "Gir",
        "age": 2,
        "gender": "FEMALE",
        "weight": 310.0
    }
    response = await client.post("/api/v1/animals", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Daisy"
    assert data["tag_id"] == "TAG-DAISY"
    assert data["status"] == "NOT_MONITORED"
    assert data["sensor_status"] == "NOT_PAIRED"
    assert data["temperature"] is None
    assert data["health_score"] is None
    assert data["activity_level"] is None
    assert data["rumination"] is None
    assert data["qr_code_payload"] is not None


@pytest.mark.asyncio
async def test_list_animals_search_and_gender_sort(client: AsyncClient, auth_headers):
    # Add male
    await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-M1", "name": "Nandi", "breed": "Murrah", "age": 4, "gender": "MALE", "weight": 550},
        headers=auth_headers
    )
    # Add female
    await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-F1", "name": "Gauri", "breed": "Gir", "age": 3, "gender": "FEMALE", "weight": 380},
        headers=auth_headers
    )
    # Add female
    await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-F2", "name": "Bella", "breed": "Holstein", "age": 3, "gender": "FEMALE", "weight": 490},
        headers=auth_headers
    )

    # Search for Gir
    search_res = await client.get("/api/v1/animals?search=gauri", headers=auth_headers)
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert search_res.json()["items"][0]["name"] == "Gauri"

    # Sort by gender (females first alphabetically: Bella, Gauri, then Nandi)
    sort_res = await client.get("/api/v1/animals?sort=gender", headers=auth_headers)
    assert sort_res.status_code == 200
    items = sort_res.json()["items"]
    assert len(items) == 3
    assert items[0]["gender"] == "FEMALE"
    assert items[1]["gender"] == "FEMALE"
    assert items[2]["gender"] == "MALE"


@pytest.mark.asyncio
async def test_update_animal(client: AsyncClient, auth_headers):
    create_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-UP", "name": "Original Name", "breed": "Sahiwal", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )
    animal_id = create_res.json()["id"]

    update_res = await client.put(
        f"/api/v1/animals/{animal_id}",
        json={"name": "Renamed Cow", "weight": 320.0},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Renamed Cow"
    assert update_res.json()["weight"] == 320.0


@pytest.mark.asyncio
async def test_delete_animal(client: AsyncClient, auth_headers):
    create_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-DEL", "name": "Delete Me", "breed": "Gir", "age": 1, "gender": "FEMALE", "weight": 200},
        headers=auth_headers
    )
    animal_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/animals/{animal_id}", headers=auth_headers)
    assert del_res.status_code == 200

    get_res = await client.get(f"/api/v1/animals/{animal_id}", headers=auth_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient, auth_headers, second_auth_headers):
    # Farmer 1 creates animal
    res1 = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-ISO-1", "name": "Farmer 1 Cow", "breed": "Gir", "age": 3, "gender": "FEMALE", "weight": 350},
        headers=auth_headers
    )
    animal_id = res1.json()["id"]

    # Farmer 2 cannot access it
    res2 = await client.get(f"/api/v1/animals/{animal_id}", headers=second_auth_headers)
    assert res2.status_code == 404

    # Farmer 2 animal list does not show Farmer 1's cow
    list_res = await client.get("/api/v1/animals", headers=second_auth_headers)
    assert list_res.json()["total"] == 0
