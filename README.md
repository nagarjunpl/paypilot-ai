# PayPilot AI

An AI payment-support agent that investigates PayPal Sandbox orders and explains what happened.

**Demo video:** [\[YouTube link\]](https://youtu.be/GK8QfA3-VOI)
**Live demo:** [\[Hosted Render link\]](https://paypilot-ai-8d8n.onrender.com)

## Problem
Customers say "I paid but my order isn't confirmed," and typical chatbots just reply "contact support."

## Solution
PayPilot looks up the real PayPal order, reasons over its status, explains the situation, recommends a next step, and escalates to a human when needed.

## How PayPal is used
- PayPal Sandbox (free test environment)
- REST API OAuth 2.0 (`/v1/oauth2/token`) for server-side authentication
- Orders v2 API: create, capture, and `GET /v2/checkout/orders/{id}` for investigation
- Order data (status, intent, amount, currency, capture details) is the AI's core input

## How AI is used
Google Gemini API (`gemini-2.5-flash`) receives the customer's message plus structured PayPal order data and returns a diagnosis, recommended action, confidence, priority, and an escalation decision. A rule-based fallback runs if Gemini is unavailable.

## Tech stack
FastAPI (Python), HTML/JavaScript frontend, PayPal Sandbox Orders v2, Google Gemini API, httpx. Hosting: Render (hosting only).

## Sponsor integrations
None.

## Setup
1. Create a PayPal Developer account, then a Sandbox app (Apps & Credentials > Sandbox). Use US-based Sandbox business and personal accounts.
2. Get a Gemini API key at aistudio.google.com/apikey.
3. Run:
   cd backend
   pip install -r requirements.txt
   cp .env.example .env    # fill in your keys
   uvicorn main:app --reload
4. Open http://localhost:8000

## Environment variables
PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_BASE_URL, GEMINI_API_KEY, GEMINI_MODEL

## Using the app
Create a $25 order, approve it with a Sandbox buyer, capture it, then investigate the order ID.

## Security
Secrets stay on the server in `.env`, which is git-ignored.

## License
MIT