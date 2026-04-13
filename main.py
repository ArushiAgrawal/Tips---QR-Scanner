from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database import engine, SessionLocal
from models import Base, User, Ledger, TipRequest
from wa_notifcation import send_upi_whatsapp

from datetime import datetime, timedelta
import re

app = FastAPI()

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="./templates")

# DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# UI
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    rendered = templates.env.get_template("index.html").render({"request": request})
    return HTMLResponse(content=rendered)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    rendered = templates.env.get_template("admin.html").render({"request": request})
    return HTMLResponse(content=rendered)


def validate_phone(phone_number: str) -> bool:
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone_number) is not None


def validate_upi(upi_id: str) -> bool:
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z]+$'
    return upi_id.count('@') == 1 and len(upi_id) > 5


# CHECK USER ELIGIBILITY
@app.post("/check-user")
def check_user(phone_number: str, db: Session = Depends(get_db)):

    if not validate_phone(phone_number):
        return {"error": "Invalid phone number format. Please enter a 10-digit Indian mobile number."}

    user = db.query(User).filter(User.phone_number == phone_number).first()

    if not user:
        # Create new user
        new_user = User(phone_number=phone_number)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "status": "ELIGIBLE",
            "user_id": new_user.id,
            "message": "New user - eligible for tip"
        }

    # Check last tip received
    last_tip = db.query(Ledger).filter(
        Ledger.to_user_id == user.id,
        Ledger.type == "TIP"
    ).order_by(Ledger.created_at.desc()).first()

    if last_tip:
        if last_tip.created_at > datetime.utcnow() - timedelta(days=90):
            return {
                "status": "NOT_ELIGIBLE",
                "last_tip_date": last_tip.created_at.strftime("%B %d, %Y"),
                "user_id": user.id,
                "message": f"Not eligible for tip. You were already tipped on {last_tip.created_at.strftime('%B %d, %Y')}"
            }

    return {
        "status": "ELIGIBLE",
        "user_id": user.id,
        "message": "Eligible for tip"
    }


# Save UPI ID to user profile
@app.post("/save-upi")
def save_upi(user_id: int, upi_id: str, db: Session = Depends(get_db)):
    
    if not validate_upi(upi_id):
        return {"error": "Invalid UPI ID format. Example: yourname@paytm"}
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return {"error": "User not found"}
    
    user.upi_id = upi_id
    db.commit()
    
    return {"message": "UPI ID saved successfully", "upi_id": upi_id}


# Get user details for admin dashboard
@app.get("/get-user")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return {"error": "User not found"}
    
    return {
        "id": user.id,
        "phone_number": user.phone_number,
        "upi_id": user.upi_id
    }


# REQUEST TIP
@app.post("/request-tip")
def request_tip(user_id: int, db: Session = Depends(get_db)):

    req = TipRequest(requester_id=user_id)
    db.add(req)
    db.commit()
    
    # Get user details and send WhatsApp notification
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.upi_id:
        try:
            send_upi_whatsapp(
                recipient_upi_id=user.upi_id,
                recipient_name=user.phone_number,
                amount="20"
            )
        except Exception as e:
            print(f"WhatsApp notification failed: {str(e)}")

    return {"message": "Tip request sent"}


# VIEW REQUESTS
@app.get("/requests")
def view_requests(db: Session = Depends(get_db)):
    requests = db.query(TipRequest).all()

    return [
        {
            "id": r.id,
            "user_id": r.requester_id,
            "status": r.status,
            "created_at": r.created_at.isoformat()
        }
        for r in requests
    ]


# APPROVE REQUEST
@app.post("/approve")
def approve_request(request_id: int, db: Session = Depends(get_db)):

    TIP_AMOUNT = 20
    ADMIN_USER_ID = 1

    req = db.query(TipRequest).filter(TipRequest.id == request_id).first()

    if not req or req.status != "PENDING":
        return {"error": "Invalid request"}

    user = db.query(User).filter(User.id == req.requester_id).first()
    
    if not user:
        return {"error": "User not found"}
    
    if not user.upi_id:
        return {"error": "User has not provided UPI ID"}

    entry = Ledger(
        from_user_id=ADMIN_USER_ID,
        to_user_id=req.requester_id,
        amount=TIP_AMOUNT,
        type="TIP"
    )

    db.add(entry)
    req.status = "APPROVED"
    db.commit()

    return {
        "message": "Approved! Request marked as paid.",
        "upi_id": user.upi_id,
        "amount": TIP_AMOUNT,
        "note": f"Send ₹{TIP_AMOUNT} from your PayTM account to {user.upi_id}"
    }
