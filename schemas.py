"""
Database Schemas for Rent It

Each Pydantic model represents a collection in MongoDB. The collection name is the
lowercase class name (e.g., User -> "user").

These schemas are used for validation in API endpoints and by the database viewer.
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl, conlist
from typing import List, Optional, Literal
from datetime import date

# -----------------------------
# Core Schemas
# -----------------------------

RoleType = Literal["landlord", "tenant"]
RoomType = Literal["private_room", "shared_room", "entire_flat"]

class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")
    address: Optional[str] = Field(None, description="Human readable address")
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class User(BaseModel):
    name: str
    email: EmailStr
    role: RoleType
    avatar_url: Optional[HttpUrl] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    verified: bool = False
    supabase_user_id: Optional[str] = Field(None, description="Supabase auth user id")

class Listing(BaseModel):
    landlord_id: str = Field(..., description="Owner user id")
    title: str
    description: str
    photos: List[HttpUrl] = Field(default_factory=list)
    video_url: Optional[HttpUrl] = None
    room_type: RoomType
    amenities: List[str] = Field(default_factory=list)
    house_rules: List[str] = Field(default_factory=list)
    price: float = Field(..., ge=0, description="Base price in local currency")
    price_unit: Literal["night", "week", "month"]
    location: Location
    available_now: bool = False
    availability_dates: List[date] = Field(default_factory=list, description="Specific dates available")

class Booking(BaseModel):
    listing_id: str
    tenant_id: str
    start_date: date
    end_date: date
    status: Literal["requested", "accepted", "declined", "cancelled", "completed"] = "requested"
    instant: bool = False
    payment_reference: Optional[str] = None

class Message(BaseModel):
    listing_id: str
    sender_id: str
    receiver_id: str
    content: str
    read: bool = False

class Review(BaseModel):
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class SavedSearch(BaseModel):
    tenant_id: str
    name: str
    query: dict
    alerts_enabled: bool = True

class VerificationRequest(BaseModel):
    user_id: str
    type: Literal["id", "property_ownership"]
    status: Literal["pending", "approved", "rejected"] = "pending"
    document_urls: conlist(HttpUrl, min_length=1) = Field(..., description="Links to uploaded documents")

# Note: The Flames database viewer will automatically:
# 1) Read these via GET /schema
# 2) Use them for document validation
# 3) Handle CRUD when applicable
