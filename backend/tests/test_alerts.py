import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_resolve_and_reopen_alert(client: AsyncClient, auth_headers):
    # 1. Create animal and trigger alert via fever
    a_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-ALERT-1", "name": "Alert Cow", "breed": "Gir", "age": 3, "gender": "FEMALE", "weight": 350},
        headers=auth_headers
    )
    animal_id = a_res.json()["id"]

    await client.post(
        "/api/v1/readings",
        json={"animal_id": animal_id, "temperature": 40.9, "activity_score": 10, "behavior": "Idle", "rumination_mins": 4},
        headers=auth_headers
    )

    # 2. Get alerts
    list_res = await client.get("/api/v1/alerts", headers=auth_headers)
    assert list_res.status_code == 200
    alert_item = list_res.json()["items"][0]
    alert_id = alert_item["id"]
    assert alert_item["is_resolved"] is False

    # 3. Resolve alert
    res_alert = await client.post(f"/api/v1/alerts/{alert_id}/resolve", headers=auth_headers)
    assert res_alert.status_code == 200
    assert res_alert.json()["is_resolved"] is True
    assert res_alert.json()["resolved_at"] is not None

    # 4. Filter by resolved=true
    resolved_list = await client.get("/api/v1/alerts?is_resolved=true", headers=auth_headers)
    assert resolved_list.status_code == 200
    assert len(resolved_list.json()["items"]) == 1

    # 5. Reopen alert
    reopen_alert = await client.post(f"/api/v1/alerts/{alert_id}/reopen", headers=auth_headers)
    assert reopen_alert.status_code == 200
    assert reopen_alert.json()["is_resolved"] is False


@pytest.mark.asyncio
async def test_filter_alerts_by_severity(client: AsyncClient, auth_headers):
    a_res = await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-CRIT", "name": "Critical Cow", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 320},
        headers=auth_headers
    )
    animal_id = a_res.json()["id"]

    # Trigger Critical High Fever
    await client.post(
        "/api/v1/readings",
        json={"animal_id": animal_id, "temperature": 41.2, "activity_score": 10, "behavior": "Idle", "rumination_mins": 2},
        headers=auth_headers
    )

    crit_res = await client.get("/api/v1/alerts?severity=CRITICAL", headers=auth_headers)
    assert crit_res.status_code == 200
    assert crit_res.json()["total"] >= 1
    assert all(a["severity"] == "CRITICAL" for a in crit_res.json()["items"])
