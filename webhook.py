import hmac
import hashlib
from fastapi import FastAPI, Headers, HttpException, Request
import json

app = FastAPI()

WEBHOOK_SECRET = "your_webhook_secret"

def verify_signature(payload: bytes, signature: str, secret:str):
    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HttpException(status_code=400, detail="Invalid signature")
    
@app.post("/webhook")
async def recieve_webhook(request: Request, x_signature: str=Headers(None)):
    if x_signature is None:
        raise HttpException(status_code=400, detail="X-Signature header is missing")

    payload = await request.body()

    try:
        verify_signature(payload, x_signature, WEBHOOK_SECRET)
    except HttpException as e:
        raise {"errror": str(e)}
    
    event_data = json.loads(payload)

    event_type = event_data.get("event_type")
    if event_type == "payment_success":
        return {"message": "Payment processed successfully", "data": event_data}
    elif event_type == "payment_failed":
        return {"message": "Payment failed", "data": event_data}
    else:
        return {"message": "Unknown event type", "data": event_data}
    
