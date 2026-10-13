import os, time, httpx

BASE = os.getenv("PAYPAL_BASE_URL", "https://api-m.sandbox.paypal.com")
_tok = {"v": None, "exp": 0}

async def _token():
    if _tok["v"] and time.time() < _tok["exp"] - 60:
        return _tok["v"]
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(f"{BASE}/v1/oauth2/token",
            auth=(os.getenv("PAYPAL_CLIENT_ID", ""), os.getenv("PAYPAL_CLIENT_SECRET", "")),
            data={"grant_type": "client_credentials"})
        r.raise_for_status()
        d = r.json()
    _tok.update(v=d["access_token"], exp=time.time() + d["expires_in"])
    return _tok["v"]

async def _req(method, path, json=None):
    h = {"Authorization": f"Bearer {await _token()}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as c:
        return await c.request(method, f"{BASE}{path}", headers=h, json=json)

def summarize(o: dict) -> dict:
    pu = (o.get("purchase_units") or [{}])[0]
    amt = pu.get("amount", {})
    caps = (pu.get("payments") or {}).get("captures", [])
    return {
        "order_id": o.get("id"), "status": o.get("status"), "intent": o.get("intent"),
        "currency": amt.get("currency_code"), "amount": amt.get("value"),
        "capture_id": caps[0]["id"] if caps else None,
        "capture_status": caps[0]["status"] if caps else None,
        "payer_email": (o.get("payer") or {}).get("email_address"),
        "create_time": o.get("create_time"), "update_time": o.get("update_time"),
        "approve_url": next((l["href"] for l in o.get("links", []) if l["rel"] in ("approve", "payer-action")), None),
    }

async def get_order(order_id: str):
    """Returns summary dict, or None if PayPal can't find the order."""
    r = await _req("GET", f"/v2/checkout/orders/{order_id}")
    if r.status_code in (404, 400):
        return None
    r.raise_for_status()
    return summarize(r.json())

async def create_order(amount="25.00", currency="USD"):
    r = await _req("POST", "/v2/checkout/orders", {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": currency, "value": amount}}],
        "payment_source": {"paypal": {"experience_context": {
            "return_url": "https://example.com/return", "cancel_url": "https://example.com/cancel"}}},
    })
    r.raise_for_status()
    return summarize(r.json())

async def capture_order(order_id: str):
    r = await _req("POST", f"/v2/checkout/orders/{order_id}/capture")
    r.raise_for_status()
    return summarize(r.json())
