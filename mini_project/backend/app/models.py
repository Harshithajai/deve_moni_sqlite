from datetime import datetime

from sqlalchemy import Date, Column, DateTime, ForeignKey, Integer, String, Text, Boolean, Table, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

# Association table for Child-Professional relationship
child_professional = Table(
    'child_professional',
    Base.metadata,
    Column('child_id', Integer, ForeignKey('children.id', ondelete='CASCADE'), primary_key=True),
    Column('professional_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

# Association table for Professional-Parent relationship (NEW)
parent_professional = Table(
    'parent_professional',
    Base.metadata,
    Column('parent_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('professional_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="parent")  # parent, professional, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    children = relationship("Child", back_populates="parent", foreign_keys="Child.parent_id", cascade="all, delete-orphan")
    shared_children = relationship(
        "Child",
        secondary=child_professional,
        backref="professionals",
    )

    # Parents assigned to this professional (role == "professional").
    # Via the backref, a parent can access `parent.assigned_professionals`.
    assigned_parents = relationship(
        "User",
        secondary=parent_professional,
        primaryjoin=id == parent_professional.c.professional_id,
        secondaryjoin=id == parent_professional.c.parent_id,
        backref="assigned_professionals",
    )

    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    interests = Column(Text, nullable=True)
    communication_preferences = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    parent = relationship("User", back_populates="children", foreign_keys=[parent_id])
    observations = relationship("Observation", back_populates="child", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    observation_text = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, default="General Development")
    skill = Column(String(255), nullable=False, default="General observation")
    behavior = Column(String(255), nullable=False, default="Observed behavior")
    context = Column(Text, nullable=True)
    duration = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    confidence_score = Column(Integer, nullable=False, default=0)
    observation_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    child = relationship("Child", back_populates="observations")
    feedback = relationship("Feedback", back_populates="observation", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="feedback")
    observation = relationship("Observation", back_populates="feedback")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)  # login, logout, child_creation, etc.
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6

    # Relationships
    user = relationship("User", back_populates="activity_logs")


# =====================================================================
# RAG Knowledge Base Models (Phase 5)
# =====================================================================

class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    source = Column(String(255), nullable=True)
    document_type = Column(String(100), nullable=True)
    file_name = Column(String(500), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    chunks = relationship("ResearchChunk", back_populates="document", cascade="all, delete-orphan")


class ResearchChunk(Base):
    __tablename__ = "research_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("research_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)

    # Relationships
    document = relationship("ResearchDocument", back_populates="chunks")

class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    question = Column(Text, nullable=False)
    retrieved_sources = Column(JSON, nullable=True)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    child = relationship("Child")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)  # e.g., "Social Interaction", "Communication", "Motor Skills"
    description = Column(Text, nullable=False)
    materials = Column(Text, nullable=True)  # JSON string or comma-separated list
    duration = Column(String, nullable=True)  # e.g., "10-15 mins"
    steps = Column(Text, nullable=False)  # JSON array string or step-by-step text
    observation_targets = Column(Text, nullable=True)  # What caregivers should watch for

    feedbacks = relationship("ActivityFeedback", back_populates="activity", cascade="all, delete-orphan")


class ActivityFeedback(Base):
    __tablename__ = "activity_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    rating = Column(Integer, nullable=True)  # e.g., 1 to 5
    helpful = Column(Boolean, nullable=True)  # True = Helpful, False = Not helpful
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    activity = relationship("Activity", back_populates="feedbacks")