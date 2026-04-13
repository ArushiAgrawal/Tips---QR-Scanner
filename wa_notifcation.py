
import urllib.parse
import requests
import urllib.parse
from dotenv import load_dotenv
import os

load_dotenv()

'''
pi://pay?pa=<UPI_ID>&pn=<NAME>&am=<AMOUNT>&tn=<NOTE>&cu=INR

Parameters:
    pa → Payee UPI ID (receiver)
    pn → Payee name
    am → Amount (optional but usually needed)
    tn → Transaction note
    cu → Currency (always INR)
'''

def send_upi_whatsapp(recipient_upi_id: str, recipient_name: str, amount: 'str'):
    
    upi_url = (
        f"upi://pay?pa={recipient_upi_id}"
        f"&pn={urllib.parse.quote(recipient_name)}"
        f"&am={amount}"
        f"&tn={urllib.parse.quote('Tip Request')}"
        f"&cu=INR"
    )

    YOUR_WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    YOUR_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")

    # Example: Send WhatsApp message via API
    response = requests.post(
        f"https://graph.facebook.com/v25.0/{YOUR_PHONE_NUMBER_ID}/messages",
        headers={
            "Authorization": f"Bearer {YOUR_WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "messaging_product": "whatsapp",
            "to": "917753058577",
            "type": "text",
            "text": {
                "body": f"Hi Arushi! 👋\n\nPlease tip ₹{20}.\n\nTap to pay: {upi_url}"
            }
        }
    )
    print(response.json())

    return response.json()

# # Usage per customer
# recipient_upi_id = "merchant@ybl"
# recipient_name = "Rahul Sharma"
# amount = "20"
# send_upi_whatsapp(recipient_upi_id, recipient_name, amount)