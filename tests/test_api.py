import pytest

pytestmark = pytest.mark.asyncio


async def _login(client, role):
    r = await client.post("/api/auth/oauth/google", json={"role": role})
    assert r.status_code == 200, r.text
    return r.json()


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_session_null_then_user(client):
    r = await client.get("/api/auth/session")
    assert r.status_code == 200
    assert r.json() is None

    user = await _login(client, "advertiser")
    assert user["role"] == "advertiser"

    r = await client.get("/api/auth/session")
    assert r.json()["id"] == user["id"]


async def test_create_and_list_campaign(client):
    await _login(client, "advertiser")
    payload = {
        "title": "Осенняя распродажа",
        "budget": 15000,
        "creative": {
            "type": "image",
            "headline": "Скидки до 50%",
            "description": "Только до конца недели, успейте купить",
            "cta": "Купить",
            "link": "https://example.com/sale",
            "previewUrl": None,
            "fileName": "sale.jpg",
        },
        "targeting": {"geo": "Россия", "audience": "25–34, мода", "devices": "Все"},
    }
    r = await client.post("/api/campaigns", json=payload)
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["status"] == "pending"
    assert c["ai"]["verdict"] in ("approve", "review", "reject")
    cid = c["id"]

    r = await client.get("/api/campaigns")
    assert r.status_code == 200
    assert any(x["id"] == cid for x in r.json())

    r = await client.get(f"/api/campaigns/{cid}")
    assert r.status_code == 200
    assert r.json()["title"] == "Осенняя распродажа"


async def test_validation_short_description(client):
    await _login(client, "advertiser")
    payload = {
        "title": "X",
        "budget": 1000,
        "creative": {
            "type": "image",
            "headline": "H",
            "description": "short",
            "cta": "C",
            "link": "https://ex.com",
        },
        "targeting": {"audience": "A"},
    }
    r = await client.post("/api/campaigns", json=payload)
    assert r.status_code == 422


async def test_moderation_flow(client):
    await _login(client, "advertiser")
    payload = {
        "title": "Кампания для модерации",
        "budget": 5000,
        "creative": {
            "type": "image",
            "headline": "Заголовок",
            "description": "Достаточно длинное описание",
            "cta": "Купить",
            "link": "https://example.com",
        },
        "targeting": {"audience": "Москва"},
    }
    cid = (await client.post("/api/campaigns", json=payload)).json()["id"]

    # выходим и логинимся модератором
    await client.post("/api/auth/logout")
    await _login(client, "moderator")

    r = await client.post(
        f"/api/campaigns/{cid}/moderation",
        json={"action": "approve", "comment": "OK"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


async def test_moderation_requires_comment_for_reject(client):
    await _login(client, "advertiser")
    payload = {
        "title": "X",
        "budget": 1000,
        "creative": {
            "type": "image",
            "headline": "H",
            "description": "Достаточно длинное описание",
            "cta": "C",
            "link": "https://example.com",
        },
        "targeting": {"audience": "A"},
    }
    cid = (await client.post("/api/campaigns", json=payload)).json()["id"]
    await client.post("/api/auth/logout")
    await _login(client, "moderator")
    r = await client.post(
        f"/api/campaigns/{cid}/moderation", json={"action": "reject", "comment": ""}
    )
    assert r.status_code == 422


async def test_topup_and_transactions(client):
    await _login(client, "advertiser")
    before = (await client.get("/api/auth/session")).json()["balance"]
    r = await client.post("/api/billing/topup", json={"amount": 500, "method": "СБП"})
    assert r.status_code == 200
    assert r.json()["balance"] == before + 500
    r = await client.get("/api/billing/transactions")
    assert r.status_code == 200
    assert any(t["amount"] == 500 for t in r.json())
