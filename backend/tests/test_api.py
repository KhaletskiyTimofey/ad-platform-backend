import pytest

pytestmark = pytest.mark.asyncio


async def _login(client, role):
    r = await client.post("/api/auth/login", json={"role": role})
    assert r.status_code == 200
    return r.json()["token"]


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_login_and_me(client):
    token = await _login(client, "advertiser")
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "advertiser"


async def test_create_campaign_and_list(client):
    token = await _login(client, "advertiser")
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.post(
        "/api/campaigns",
        data={"title": "Test", "description": "d", "url": "https://ex.com", "budget": 1000},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    cid = r.json()["id"]

    r = await client.get("/api/campaigns", headers=headers)
    assert r.status_code == 200
    assert any(c["id"] == cid for c in r.json())

    r = await client.get(f"/api/campaigns/{cid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["title"] == "Test"


async def test_moderation_flow(client):
    adv = await _login(client, "advertiser")
    mod = await _login(client, "moderator")
    r = await client.post(
        "/api/campaigns",
        data={"title": "Mod", "description": "", "url": "https://ex.com", "budget": 500},
        headers={"Authorization": f"Bearer {adv}"},
    )
    cid = r.json()["id"]

    r = await client.post(
        f"/api/campaigns/{cid}/moderate",
        json={"status": "approved", "comment": "ok"},
        headers={"Authorization": f"Bearer {mod}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    r = await client.get("/api/campaigns", params={"status": "approved"}, headers={"Authorization": f"Bearer {mod}"})
    assert any(c["id"] == cid for c in r.json())


async def test_topup(client):
    token = await _login(client, "advertiser")
    headers = {"Authorization": f"Bearer {token}"}
    before = (await client.get("/api/auth/me", headers=headers)).json()["balance"]
    r = await client.post("/api/balance/topup", json={"amount": 500}, headers=headers)
    assert r.status_code == 200
    assert r.json()["balance"] == before + 500


async def test_impression_click_stats(client):
    adv = await _login(client, "advertiser")
    mod = await _login(client, "moderator")
    r = await client.post(
        "/api/campaigns",
        data={"title": "S", "description": "", "url": "https://ex.com", "budget": 100},
        headers={"Authorization": f"Bearer {adv}"},
    )
    cid = r.json()["id"]
    await client.post(
        f"/api/campaigns/{cid}/moderate",
        json={"status": "approved", "comment": ""},
        headers={"Authorization": f"Bearer {mod}"},
    )
    assert (await client.post(f"/api/impression/{cid}")).status_code == 200
    assert (await client.post(f"/api/click/{cid}")).status_code == 200
    stats = (await client.get("/api/stats")).json()
    assert stats["impressions"] >= 1
    assert stats["clicks"] >= 1