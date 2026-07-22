import os
import requests
import uuid
from dotenv import load_dotenv

load_dotenv()

PAYCHANGU_SECRET_KEY = os.getenv("PAYCHANGU_SECRET_KEY")
PAYCHANGU_URL = "https://api.paychangu.com/payment"
VERIFY_URL = "https://api.paychangu.com/verify-payment/"

def create_checkout_session(amount=500, user_email="student@phunziro.mw", first_name="Student", last_name="User"):
    """
    Generates a PayChangu checkout URL for MWK payments.
    """
    tx_ref = f"phunziro-{uuid.uuid4().hex[:8]}"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {PAYCHANGU_SECRET_KEY}"
    }

    LOCAL_URL = "https://9ade-102-70-101-204.ngrok-free.app/"
    payload = {
        "amount": amount,
        "currency": "MWK",
        "tx_ref": tx_ref,
        "first_name": first_name,
        "last_name": last_name,
        "email": user_email,
        "callback_url": LOCAL_URL,  # This should be your actual callback URL
        "return_url": LOCAL_URL,
        "customization": {
            "title": "PhunziroAI - Daily Pass",
            "description": "Unlock PDF Exam Quiz Generator"
        }
    }
    
    try:
        response = requests.post(PAYCHANGU_URL, json=payload, headers=headers)
        data = response.json()
        
        # FIX: Check if status is success regardless of whether status_code is 200 or 201
        if response.status_code in [200, 201] and data.get("status") == "success":
            # Extract checkout_url safely
            checkout_url = data.get("data", {}).get("checkout_url")
            return {"status": True, "checkout_url": checkout_url, "tx_ref": tx_ref}
        else:
            return {"status": False, "message": data.get("message", "Payment initiation failed")}
            
    except Exception as e:
        return {"status": False, "message": str(e)}

def verify_payment(tx_ref):
    """
    Verifies if a given transaction reference was completed successfully.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {PAYCHANGU_SECRET_KEY}"
    }
    
    try:
        response = requests.get(f"{VERIFY_URL}{tx_ref}", headers=headers)
        data = response.json()
        if response.status_code == 200 and data.get("status") == "success":
            payment_data = data.get("data", {})
            if payment_data.get("status") == "success":
                return True
        return False
    except Exception:
        return False