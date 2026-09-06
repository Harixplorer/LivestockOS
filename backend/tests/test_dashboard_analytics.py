import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_endpoint(client: AsyncClient, auth_headers):
    # Add animal
    await client.post(
        "/api/v1/animals",
        json={"tag_id": "TAG-D1", "name": "Dash Cow", "breed": "Gir", "age": 2, "gender": "FEMALE", "weight": 300},
        headers=auth_headers
    )

    res = await client.get("/api/v1/dashboard", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "farmer_name" in data
    assert "summary" in data
    assert data["summary"]["total_animals"] == 1
    assert data["summary"]["not_monitored_count"] == 1
    assert len(data["quick_actions"]) == 4
    assert len(data["weekly_trend"]) == 7


@pytest.mark.asyncio
async def test_analytics_endpoints(client: AsyncClient, auth_headers):
    # Summary
    sum_res = await client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert sum_res.status_code == 200
    assert "total_animals" in sum_res.json()

    # Distribution
    dist_res = await client.get("/api/v1/analytics/distribution", headers=auth_headers)
    assert dist_res.status_code == 200
    dist_data = dist_res.json()
    assert "total" in dist_data
    assert "healthy" in dist_data
    assert "pending" in dist_data

    # Sensors coverage
    sens_res = await client.get("/api/v1/analytics/sensors", headers=auth_headers)
    assert sens_res.status_code == 200
    sens_data = sens_res.json()
    assert "total_animals" in sens_data
    assert "paired" in sens_data

    # Trends
    trend_res = await client.get("/api/v1/analytics/trends", headers=auth_headers)
    assert trend_res.status_code == 200
    assert len(trend_res.json()) == 24

    # Comparison
    comp_res = await client.get("/api/v1/analytics/comparison", headers=auth_headers)
    assert comp_res.status_code == 200
    assert isinstance(comp_res.json(), list)
