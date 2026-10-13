import re, itertools, pathlib
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from services import paypal_service as pp, ai_service as ai

app = FastAPI(title="PayPilot AI")
CASES, _ids = [], itertools.count(1024)
FRONT = pathlib.Path(__file__).parent.parent / "frontend"

class Investigate(BaseModel):
    message: str
    order_id: str | None = None

class Case(BaseModel):
    order_id: str | None
    customer_query: str
    paypal_status: str | None
    analysis: dict

@app.post("/api/investigate")
async def investigate(req: Investigate):
    oid = req.order_id or (m.group(0) if (m := re.search(r"\b[0-9A-Z]{17}\b", req.message)) else None)
    if not oid:
        return {"needs_order_id": True, "reply": "Please provide your PayPal Order ID."}
    try:
        order = await pp.get_order(oid.strip())
    except httpx.HTTPError as e:
        raise HTTPException(502, f"PayPal error: {e}")
    return {"order_id": oid, "order": order, "analysis": await ai.analyze(req.message, order)}

@app.get("/api/paypal/order/{order_id}")
async def get_order(order_id: str):
    return await pp.get_order(order_id) or {"error": "not found"}

@app.post("/api/paypal/create-order")
async def create_order(amount: str = "25.00"):
    return await pp.create_order(amount)

@app.post("/api/paypal/capture-order/{order_id}")
async def capture(order_id: str):
    try:
        return await pp.capture_order(order_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(400, f"Capture failed (has the buyer approved it?): {e.response.text[:200]}")

@app.post("/api/cases")
async def create_case(c: Case):
    case = {"case_id": f"PP-{next(_ids)}", **c.model_dump()}
    CASES.append(case)
    return case

@app.get("/api/cases")
async def list_cases():
    return CASES

@app.get("/")
async def index():
    return FileResponse(FRONT / "index.html")
