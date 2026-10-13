import os, json, httpx

PROMPT = """You are PayPilot AI, a payment-support agent. Using ONLY the PayPal data provided, explain the
customer's situation. Never invent facts. Respond with JSON only:
{"summary": str, "diagnosis": str, "recommended_action": str,
 "confidence": number 0-100, "escalate": bool, "priority": "Low"|"Medium"|"High"}"""

def rule_based(order):
    if order is None:
        return dict(summary="No matching PayPal Sandbox order found.",
            diagnosis="The Order ID may be mistyped or from another environment.",
            recommended_action="Verify the Order ID (Sandbox IDs are 17 characters) and try again.",
            confidence=90, escalate=False, priority="Low")
    s = order["status"]
    t = {
     "COMPLETED": ("Payment completed successfully.",
        "PayPal shows the payment as captured. If the merchant app says unconfirmed, the issue is likely merchant-side sync/webhook handling.",
        "Check merchant order-processing and webhook logs; share the Order ID with merchant support.", 92, True, "Medium"),
     "CREATED": ("Order created, but payment not completed.",
        "The buyer has not approved the payment yet.",
        "Return to PayPal checkout and approve the payment.", 90, False, "Low"),
     "PAYER_ACTION_REQUIRED": ("Buyer action required.",
        "PayPal is waiting for the buyer to take an action to proceed.",
        "Complete the pending step in PayPal.", 85, False, "Low"),
     "APPROVED": ("Buyer approved, but not captured yet.",
        "Funds have not been captured; the merchant must capture the order.",
        "Merchant should capture the order.", 88, True, "Medium"),
     "VOIDED": ("Order was cancelled/voided.",
        "No completed payment is shown for this order.",
        "Start a new checkout if you still wish to pay.", 90, False, "Low"),
    }.get(s, (f"Order status: {s}.", "Status is not covered by standard rules.",
              "Escalate to a human agent.", 40, True, "High"))
    return dict(zip(["summary","diagnosis","recommended_action","confidence","escalate","priority"], t))

async def analyze(message: str, order):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {**rule_based(order), "engine": "rules"}
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    body = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"parts": [{"text": f"Customer message: {message}\nPayPal order data: {json.dumps(order)}"}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2},
    }
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                             params={"key": key}, json=body)
            r.raise_for_status()
        out = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
        return {**out, "engine": f"gemini:{model}"}
    except Exception as e:
        return {**rule_based(order), "engine": f"rules (gemini failed: {type(e).__name__})"}
