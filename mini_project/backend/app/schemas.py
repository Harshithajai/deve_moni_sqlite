from datetime import date, datetime
from typing import List, Optional, Any, Dict

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="parent", pattern="^(parent|professional)$")


class UserLogin(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class TokenData(BaseModel):
    user_id: int
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int


# ==================== Child Schemas ====================

class ChildBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: Optional[date] = None
    age: Optional[int] = Field(default=None, ge=0, le=25)
    gender: Optional[str] = Field(default=None, max_length=50)
    interests: Optional[str] = None
    communication_preferences: Optional[str] = None
    notes: Optional[str] = None


class ChildCreate(ChildBase):
    pass


class ChildUpdate(ChildBase):
    pass


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    name: str
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    interests: Optional[str] = None
    communication_preferences: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ChildShareRequest(BaseModel):
    professional_id: int

class ProfessionalConnectRequest(BaseModel):
    professional_id: int


class ParentSummaryOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    children_count: int

# ==================== Observation Schemas ====================

class ObservationBase(BaseModel):
    child_id: int
    observation_text: str = Field(..., min_length=10, max_length=5000)
    domain: str = Field(default="General Development", max_length=255)
    skill: str = Field(default="General observation", max_length=255)
    behavior: str = Field(default="Observed behavior", max_length=255)
    context: Optional[str] = None
    duration: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    confidence_score: int = Field(default=0, ge=0, le=100)
    observation_date: datetime = Field(default_factory=datetime.utcnow)


class ObservationCreate(ObservationBase):
    pass


class ObservationUpdate(BaseModel):
    observation_text: Optional[str] = Field(default=None, min_length=10, max_length=5000)
    domain: Optional[str] = Field(default=None, max_length=255)
    skill: Optional[str] = Field(default=None, max_length=255)
    behavior: Optional[str] = Field(default=None, max_length=255)
    context: Optional[str] = None
    duration: Optional[str] = Field(default=None, max_length=100)
    frequency: Optional[str] = Field(default=None, max_length=100)
    confidence_score: Optional[int] = Field(default=None, ge=0, le=100)
    observation_date: Optional[datetime] = None


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    observation_text: str
    domain: str
    skill: str
    behavior: str
    context: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None
    confidence_score: int
    observation_date: datetime
    created_at: datetime


# ==================== Feedback Schemas ====================

class FeedbackCreate(BaseModel):
    observation_id: Optional[int] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    observation_id: Optional[int] = None
    rating: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime


# ==================== Activity Log Schemas ====================

class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    action: str
    description: Optional[str] = None
    timestamp: datetime
    ip_address: Optional[str] = None

class AskAIRequest(BaseModel):
    child_id: int
    question: str

class CitationSchema(BaseModel):
    title: str
    authors: str
    year: Optional[int] = None
    doi: Optional[str] = None
    page_number: Optional[int] = None
    relevant_passage: str

class AskAIResponse(BaseModel):
    answer: str
    why_this_may_help: str
    suggested_activities: List[str]
    how_to_try_at_home: List[str]
    what_to_observe: List[str]
    evidence_sources: List[CitationSchema]
    safety_note: str
    is_insufficient_evidence: bool = False

class ActivityOut(BaseModel):
    id: int
    name: str
    domain: str
    description: str
    materials: Optional[str] = None
    duration: Optional[str] = None
    steps: str
    observation_targets: Optional[str] = None

    class Config:
        from_attributes = True

class ActivityRecommendationRequest(BaseModel):
    child_id: int

class ActivityRecommendationResponse(BaseModel):
    activity_id: Optional[int] = None
    title: str
    domain: str
    description: str
    materials: Optional[str] = None
    duration: Optional[str] = None
    steps: List[str]
    observation_targets: Optional[str] = None
    reasoning: str
    evidence_sources: List[str] = []
    disclaimer: str = "This activity is an optional educational suggestion and does not constitute medical advice or treatment."

class ActivityFeedbackCreate(BaseModel):
    activity_id: int
    rating: Optional[int] = None
    helpful: Optional[bool] = None
    comment: Optional[str] = None

class ActivityFeedbackOut(BaseModel):
    id: int
    user_id: int
    activity_id: int
    rating: Optional[int] = None
    helpful: Optional[bool] = None
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True