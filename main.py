import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import User, Listing, Booking, Message, Review, SavedSearch, VerificationRequest

app = FastAPI(title="Rent It API", description="Backend for Rent It platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Utility
# -----------------------------

def collection_name(model_cls) -> str:
    return model_cls.__name__.lower()


# -----------------------------
# Health & Schema
# -----------------------------

@app.get("/")
def root():
    return {"name": "Rent It API", "status": "ok"}


@app.get("/schema")
def get_schema():
    # Simple signal for Flames DB viewer
    return {"status": "ok"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "Unknown"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# -----------------------------
# Users
# -----------------------------

@app.post("/users", status_code=201)
def create_user(user: User):
    user_id = create_document(collection_name(User), user)
    return {"id": user_id, **user.model_dump()}


@app.get("/users")
def list_users(role: Optional[str] = None):
    filt = {"role": role} if role else {}
    docs = get_documents(collection_name(User), filt)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -----------------------------
# Listings
# -----------------------------

@app.post("/listings", status_code=201)
def create_listing(listing: Listing):
    listing_id = create_document(collection_name(Listing), listing)
    return {"id": listing_id, **listing.model_dump()}


@app.get("/listings")
def search_listings(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 20.0,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    room_type: Optional[str] = None,
    available_now: Optional[bool] = None,
):
    # Basic filter (no geo index in this simple version)
    filt = {}
    if price_min is not None or price_max is not None:
        filt["price"] = {}
        if price_min is not None:
            filt["price"]["$gte"] = price_min
        if price_max is not None:
            filt["price"]["$lte"] = price_max
    if room_type:
        filt["room_type"] = room_type
    if available_now is not None:
        filt["available_now"] = available_now

    docs = get_documents(collection_name(Listing), filt)
    results = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        results.append(d)
    return results


# -----------------------------
# Bookings
# -----------------------------

@app.post("/bookings", status_code=201)
def request_booking(booking: Booking):
    booking_id = create_document(collection_name(Booking), booking)
    return {"id": booking_id, **booking.model_dump()}


@app.get("/bookings")
def list_bookings(tenant_id: Optional[str] = None, landlord_id: Optional[str] = None):
    filt = {}
    if tenant_id:
        filt["tenant_id"] = tenant_id
    if landlord_id:
        filt["landlord_id"] = landlord_id
    docs = get_documents(collection_name(Booking), filt)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -----------------------------
# Messages
# -----------------------------

@app.post("/messages", status_code=201)
def send_message(msg: Message):
    msg_id = create_document(collection_name(Message), msg)
    return {"id": msg_id, **msg.model_dump()}


@app.get("/messages")
def get_messages(listing_id: Optional[str] = None, user_id: Optional[str] = None):
    filt = {}
    if listing_id:
        filt["listing_id"] = listing_id
    if user_id:
        filt["$or"] = [{"sender_id": user_id}, {"receiver_id": user_id}]
    docs = get_documents(collection_name(Message), filt)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -----------------------------
# Reviews
# -----------------------------

@app.post("/reviews", status_code=201)
def create_review(review: Review):
    review_id = create_document(collection_name(Review), review)
    return {"id": review_id, **review.model_dump()}


@app.get("/reviews")
def list_reviews(reviewee_id: Optional[str] = None):
    filt = {"reviewee_id": reviewee_id} if reviewee_id else {}
    docs = get_documents(collection_name(Review), filt)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -----------------------------
# Saved Searches
# -----------------------------

@app.post("/saved-searches", status_code=201)
def create_saved_search(payload: SavedSearch):
    ss_id = create_document(collection_name(SavedSearch), payload)
    return {"id": ss_id, **payload.model_dump()}


@app.get("/saved-searches")
def list_saved_searches(tenant_id: str):
    docs = get_documents(collection_name(SavedSearch), {"tenant_id": tenant_id})
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# -----------------------------
# Verification
# -----------------------------

@app.post("/verification", status_code=201)
def create_verification_request(req: VerificationRequest):
    v_id = create_document(collection_name(VerificationRequest), req)
    return {"id": v_id, **req.model_dump()}


@app.get("/verification")
def list_verification_requests(user_id: Optional[str] = None, status: Optional[str] = None):
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    if status:
        filt["status"] = status
    docs = get_documents(collection_name(VerificationRequest), filt)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
