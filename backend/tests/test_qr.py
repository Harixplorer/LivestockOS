import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_qr_lookup_by_tag_and_payload(client: AsyncClient, auth_headers):
    # Add animal
    create_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-QR-TEST", "name": "QR Cow", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )
    animal = create_res.json()
    tag_id = animal["tag_id"]
    qr_payload = animal["qr_code_payload"]

    # 1. Lookup by Tag ID
    res1 = await client.get(f"/api/v1/qr/lookup?query={tag_id}", headers=auth_headers)
    assert res1.status_code == 200
    assert res1.json()["found"] is True
    assert res1.json()["animal"]["id"] == animal["id"]

    # 2. Lookup by QR payload string
    res2 = await client.get(f"/api/v1/qr/lookup?query={qr_payload}", headers=auth_headers)
    assert res2.status_code == 200
    assert res2.json()["found"] is True
    assert res2.json()["animal"]["name"] == "QR Cow"

    # 3. Lookup non-existent
    res3 = await client.get("/api/v1/qr/lookup?query=NON-EXISTENT", headers=auth_headers)
    assert res3.status_code == 200
    assert res3.json()["found"] is False
    assert res3.json()["animal"] is None
