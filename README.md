# PayPilot AI
AI payment-support agent that investigates PayPal Sandbox orders (Orders v2) and explains/escalates with Google Gemini.

## Run
```
cd backend
pip install -r requirements.txt
cp .env.example .env   # add PayPal Sandbox + Gemini keys
uvicorn main:app --reload
```
Open http://localhost:8000

## How PayPal is used
OAuth 2.0 token -> create / get / capture orders via Orders v2 on the Sandbox. The AI's tool is `get_order`.

## How AI is used
Gemini receives the customer message + structured PayPal order data and returns diagnosis, next step, confidence, escalation flag. Falls back to rules if no key.

## License
MIT
