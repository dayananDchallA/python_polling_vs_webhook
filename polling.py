from fastapi import FastAPI, BackgroundTasks, HTTPException
import httpx
import asyncio

app = FastAPI()

# In-memory store to keep track of payment statuses
payment_status_store = {}

async def check_payment_status(payment_id: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/payments/{payment_id}/status")
        payment_status = response.json().get("status", "unknown")
        return payment_status

async def poll_payment_status(payment_id: str):
    interval = 10  # seconds between checks
    retries = 5    # max attempts
    for _ in range(retries):
        payment_status = await check_payment_status(payment_id)
        
        # Update the status in the store
        payment_status_store[payment_id] = payment_status

        if payment_status in ["paid", "failed"]:
            return
        await asyncio.sleep(interval)
    
    # If status doesn't change after retries, mark as "timeout"
    payment_status_store[payment_id] = "timeout"

@app.post("/poll-payment/{payment_id}")
async def poll_payment(payment_id: str, background_tasks: BackgroundTasks):
    # Check if payment_id already exists in the store
    if payment_id in payment_status_store:
        return {"message": "Polling already in progress or completed", "payment_id": payment_id}
    
    # Initialize status in the store
    payment_status_store[payment_id] = "pending"
    
    # Start polling in the background
    background_tasks.add_task(poll_payment_status, payment_id)
    return {"message": "Polling started", "payment_id": payment_id}

@app.get("/payment-status/{payment_id}")
async def get_payment_status(payment_id: str):
    # Retrieve the payment status from the store
    payment_status = payment_status_store.get(payment_id)
    
    if payment_status is None:
        raise HTTPException(status_code=404, detail="Payment ID not found")

    return {"payment_id": payment_id, "status": payment_status}
