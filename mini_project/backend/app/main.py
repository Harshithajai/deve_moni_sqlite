import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from datetime import date, datetime, time
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.routes import rag
from app.routes import activity

from .auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    require_parent,
    require_professional,
    verify_password,
)
from .database import Base, check_database_available, ensure_legacy_schema, engine, get_db
from .models import ActivityLog, AIInteraction, Child, Feedback, Observation, User, child_professional, parent_professional
from .schemas import (
    ActivityLogOut,
    AskAIRequest,
    AskAIResponse,
    ChildCreate,
    ChildOut,
    ChildShareRequest,
    ChildUpdate,
    FeedbackCreate,
    FeedbackOut,
    ObservationCreate,
    ObservationOut,
    ObservationUpdate,
    ParentSummaryOut,
    ProfessionalConnectRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
)
from app.llm.service import process_caregiver_query

# Allowed frontend origins. Set CORS_ORIGINS on the server to a comma-separated list,
# e.g. https://devcare.netlify.app  (no trailing slash). Localhost stays allowed for dev.
ALLOWED_ORIGINS = [
    o.strip().rstrip("/")
    for o in os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
] + ["http://localhost:5173", "http://localhost:5174"]

app = FastAPI(title="DevCare API", version="1.0.0")
app.include_router(rag.router)
app.include_router(activity.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://devcare-mini.netlify.app", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    try:
        ensure_legacy_schema()
        Base.metadata.create_all(bind=engine)
        print("[DATABASE] Startup database initialization successful.")
    except SQLAlchemyError as exc:
        print(f"[DATABASE] Startup database initialization FAILED: {exc}")


@app.get("/")
def read_root():
    return {"message": "DevCare API is running"}


# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match.",
            )

        existing_user = db.query(User).filter(User.email == user.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        db_user = User(
            full_name=user.full_name.strip(),
            email=user.email.lower(),
            password_hash=hash_password(user.password),
            role=user.role,
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Log activity
        log = ActivityLog(
            user_id=db_user.id,
            action="registration",
            description=f"User registered with role: {user.role}",
        )
        db.add(log)
        db.commit()
        
        return db_user
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        clean_email = login_data.email.strip().lower()
        user = db.query(User).filter(User.email == clean_email).first()
        if not user or not user.is_active or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(user.id, user.email, user.role)
        
        # Log activity
        log = ActivityLog(
            user_id=user.id,
            action="login",
            description="User logged in",
        )
        db.add(log)
        db.commit()
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": user.id,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.get("/api/auth/me", response_model=UserOut)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    return current_user


# ==================== HELPERS ====================

def professional_can_access_child(professional: User, child: Child) -> bool:
    """Access via direct child-share OR via the professional's assigned parents."""
    if professional in child.professionals:
        return True
    if child.parent_id in {p.id for p in professional.assigned_parents}:
        return True
    return False


# ==================== AI CAREGIVER ASSISTANT (PHASE 6) ====================

@app.post("/api/ai/ask", response_model=AskAIResponse)
def ask_ai_assistant(
    req: AskAIRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evidence-Grounded AI Caregiver Assistant endpoint"""
    try:
        # Verify child access/ownership
        child = db.query(Child).filter(Child.id == req.child_id).first()
        if not child:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found.")
        
        if current_user.role == "parent" and child.parent_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized access to this child profile.")
        elif current_user.role == "professional" and not professional_can_access_child(current_user, child):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This child has not been shared with you.")

        # Fetch recent observations for contextual grounding
        obs = (
            db.query(Observation)
            .filter(Observation.child_id == child.id)
            .order_by(Observation.observation_date.desc(), Observation.created_at.desc())
            .limit(5)
            .all()
        )
        obs_texts = [f"{o.observation_date}: {o.observation_text}" for o in obs]

        # Execute RAG + LLM analysis
        result = process_caregiver_query(question=req.question, child_observations=obs_texts)

        # Log AI interaction
        interaction = AIInteraction(
            user_id=current_user.id,
            child_id=child.id,
            question=req.question,
            retrieved_sources=result.get("evidence_sources", []),
            response=result
        )
        db.add(interaction)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="ai_query",
            description=f"Asked AI Assistant for child ID {child.id}",
        )
        db.add(log)
        db.commit()

        return result

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


# ==================== CHILD MANAGEMENT (PARENTS ONLY) ====================

def get_child_for_parent(db: Session, child_id: int, parent_id: int) -> Child:
    """Get a child only if the parent owns it"""
    child = db.query(Child).filter(Child.id == child_id, Child.parent_id == parent_id).first()
    if child is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found.",
        )
    return child


def get_observation_for_parent(db: Session, observation_id: int, parent_id: int) -> Observation:
    """Get an observation only if the parent owns the child"""
    observation = (
        db.query(Observation)
        .join(Child)
        .filter(Observation.id == observation_id, Child.parent_id == parent_id)
        .first()
    )
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Observation not found.",
        )
    return observation


@app.post("/api/children", response_model=ChildOut, status_code=status.HTTP_201_CREATED)
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    try:
        db_child = Child(parent_id=current_user.id, **child.model_dump())
        db.add(db_child)
        db.commit()
        db.refresh(db_child)
        
        # Log activity
        log = ActivityLog(
            user_id=current_user.id,
            action="child_creation",
            description=f"Created child profile: {child.name}",
        )
        db.add(log)
        db.commit()
        
        return db_child
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.get("/api/children", response_model=list[ChildOut])
def get_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    try:
        return db.query(Child).filter(Child.parent_id == current_user.id).order_by(Child.created_at.desc()).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.get("/api/children/{child_id}", response_model=ChildOut)
def get_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    return get_child_for_parent(db, child_id, current_user.id)


@app.put("/api/children/{child_id}", response_model=ChildOut)
def update_child(
    child_id: int,
    child_update: ChildUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    child = get_child_for_parent(db, child_id, current_user.id)
    try:
        for field, value in child_update.model_dump(exclude_unset=True).items():
            setattr(child, field, value)
        db.commit()
        db.refresh(child)
        
        log = ActivityLog(
            user_id=current_user.id,
            action="child_update",
            description=f"Updated child profile: {child.name}",
        )
        db.add(log)
        db.commit()
        
        return child
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.delete("/api/children/{child_id}")
def delete_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    child = get_child_for_parent(db, child_id, current_user.id)
    try:
        child_name = child.name
        db.delete(child)
        db.commit()
        
        log = ActivityLog(
            user_id=current_user.id,
            action="child_deletion",
            description=f"Deleted child profile: {child_name}",
        )
        db.add(log)
        db.commit()
        
        return {"message": "Child deleted successfully."}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


# ==================== OBSERVATION MANAGEMENT ====================

@app.post("/api/observations", response_model=ObservationOut, status_code=status.HTTP_201_CREATED)
def create_observation(
    observation: ObservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    get_child_for_parent(db, observation.child_id, current_user.id)
    try:
        db_observation = Observation(
            child_id=observation.child_id,
            observation_text=observation.observation_text,
            domain=observation.domain,
            skill=observation.skill,
            behavior=observation.behavior,
            context=observation.context,
            duration=observation.duration,
            frequency=observation.frequency,
            confidence_score=observation.confidence_score,
            observation_date=observation.observation_date,
        )
        db.add(db_observation)
        db.commit()
        db.refresh(db_observation)
        
        log = ActivityLog(
            user_id=current_user.id,
            action="observation_creation",
            description=f"Created observation for domain: {observation.domain}",
        )
        db.add(log)
        db.commit()
        
        return db_observation
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.get("/api/observations/{child_id}", response_model=list[ObservationOut])
def get_observations_for_child(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Allow both parent and professional to view observations of shared children
    if current_user.role == "parent":
        get_child_for_parent(db, child_id, current_user.id)
    elif current_user.role == "professional":
        child = db.query(Child).filter(Child.id == child_id).first()
        if not child:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found.")
        if not professional_can_access_child(current_user, child):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This child has not been shared with you.")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only parents and professionals can view observations.")
    
    try:
        return (
            db.query(Observation)
            .filter(Observation.child_id == child_id)
            .order_by(Observation.observation_date.desc(), Observation.created_at.desc())
            .all()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.put("/api/observations/{observation_id}", response_model=ObservationOut)
def update_observation(
    observation_id: int,
    observation_update: ObservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    observation = get_observation_for_parent(db, observation_id, current_user.id)
    try:
        for field, value in observation_update.model_dump(exclude_unset=True).items():
            setattr(observation, field, value)
        db.commit()
        db.refresh(observation)
        
        log = ActivityLog(
            user_id=current_user.id,
            action="observation_update",
            description=f"Updated observation for domain: {observation.domain}",
        )
        db.add(log)
        db.commit()
        
        return observation
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


@app.delete("/api/observations/{observation_id}")
def delete_observation(
    observation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    observation = get_observation_for_parent(db, observation_id, current_user.id)
    try:
        db.delete(observation)
        db.commit()
        
        log = ActivityLog(
            user_id=current_user.id,
            action="observation_deletion",
            description="Deleted observation",
        )
        db.add(log)
        db.commit()
        
        return {"message": "Observation deleted successfully."}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please check the database file and try again.",
        ) from exc


# ==================== PROGRESS & ANALYTICS ====================

@app.get("/api/progress/{child_id}")
def get_child_progress(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    domain: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    # Verify access
    if current_user.role == "parent":
        get_child_for_parent(db, child_id, current_user.id)
    elif current_user.role == "professional":
        child = db.query(Child).filter(Child.id == child_id).first()
        if not child or not professional_can_access_child(current_user, child):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    query = db.query(Observation).filter(Observation.child_id == child_id)

    if domain:
        query = query.filter(Observation.domain == domain)
    if start_date:
        query = query.filter(Observation.observation_date >= datetime.combine(start_date, time.min))
    if end_date:
        query = query.filter(Observation.observation_date <= datetime.combine(end_date, time.max))

    observations = query.order_by(Observation.observation_date.asc(), Observation.created_at.asc()).all()

    summary_query = (
        db.query(Observation.domain.label("domain"), func.count(Observation.id).label("count"))
        .filter(Observation.child_id == child_id)
    )
    if domain:
        summary_query = summary_query.filter(Observation.domain == domain)
    if start_date:
        summary_query = summary_query.filter(Observation.observation_date >= datetime.combine(start_date, time.min))
    if end_date:
        summary_query = summary_query.filter(Observation.observation_date <= datetime.combine(end_date, time.max))

    domain_summary = (
        summary_query.group_by(Observation.domain)
        .order_by(func.count(Observation.id).desc())
        .all()
    )
    domain_summary = [{"domain": item.domain, "count": item.count} for item in domain_summary]

    timeline_query = (
        db.query(func.date(Observation.observation_date).label("date"), func.count(Observation.id).label("count"))
        .filter(Observation.child_id == child_id)
    )
    if domain:
        timeline_query = timeline_query.filter(Observation.domain == domain)
    if start_date:
        timeline_query = timeline_query.filter(Observation.observation_date >= datetime.combine(start_date, time.min))
    if end_date:
        timeline_query = timeline_query.filter(Observation.observation_date <= datetime.combine(end_date, time.max))

    timeline = (
        timeline_query.group_by(func.date(Observation.observation_date))
        .order_by(func.date(Observation.observation_date).asc())
        .all()
    )

    if start_date:
        timeline = [item for item in timeline if item.date >= start_date]
    if end_date:
        timeline = [item for item in timeline if item.date <= end_date]

    recent_observations = [ObservationOut.model_validate(item).model_dump() for item in observations[-5:]]

    primary_domain = domain_summary[0]["domain"] if domain_summary else None
    latest_date = observations[-1].observation_date.date().isoformat() if observations else None

    return {
        "child_id": child_id,
        "total_observations": len(observations),
        "primary_domain": primary_domain,
        "latest_date": latest_date,
        "domain_summary": domain_summary,
        "timeline": [
            {"date": item.date.isoformat() if hasattr(item.date, "isoformat") else str(item.date), "count": item.count}
            for item in timeline
        ],
        "recent_observations": recent_observations,
    }


# ==================== CHILD & PROFESSIONAL SHARING ====================

@app.post("/api/children/{child_id}/share")
def share_child_with_professional(
    child_id: int,
    share_request: ChildShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    """Parent shares a child with a professional"""
    try:
        child = get_child_for_parent(db, child_id, current_user.id)
        professional = db.query(User).filter(User.id == share_request.professional_id, User.role == "professional").first()
        
        if not professional:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found.")
        
        # Add professional to child's professionals list if not already there
        if professional not in child.professionals:
            child.professionals.append(professional)
            db.commit()
        
        log = ActivityLog(
            user_id=current_user.id,
            action="child_shared",
            description=f"Shared child '{child.name}' with professional {professional.full_name}",
        )
        db.add(log)
        db.commit()
        
        return {"message": f"Child '{child.name}' shared with professional '{professional.full_name}'."}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/professionals/children", response_model=list[ChildOut])
def get_shared_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
):
    """Professional views children shared with them directly"""
    try:
        return current_user.shared_children
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


# ==================== PROFESSIONAL ↔ PARENT ====================

@app.post("/api/parents/connect-professional")
def connect_parent_with_professional(
    request: ProfessionalConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_parent),
):
    """Parent associates themselves with a professional (mirrors child-share flow)."""
    try:
        professional = db.query(User).filter(
            User.id == request.professional_id, User.role == "professional"
        ).first()
        if not professional:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professional not found.")

        if professional not in current_user.assigned_professionals:
            current_user.assigned_professionals.append(professional)
            db.commit()

        log = ActivityLog(
            user_id=current_user.id,
            action="parent_professional_link",
            description=f"Connected with professional {professional.full_name}",
        )
        db.add(log)
        db.commit()

        return {"message": f"Connected with professional '{professional.full_name}'."}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/professionals/dashboard")
def get_professional_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
):
    """Professional views summary: parents, children, observations."""
    try:
        parents = current_user.assigned_parents
        all_children = [c for p in parents for c in p.children]
        child_ids = [c.id for c in all_children]

        total_observations = 0
        latest_observation_date = None
        if child_ids:
            total_observations = db.query(Observation).filter(Observation.child_id.in_(child_ids)).count()
            latest = (
                db.query(Observation)
                .filter(Observation.child_id.in_(child_ids))
                .order_by(Observation.observation_date.desc())
                .first()
            )
            latest_observation_date = latest.observation_date if latest else None

        return {
            "id": current_user.id,  # ADDED: Returns logged-in professional ID
            "total_parents": len(parents),
            "total_children": len(all_children),
            "total_observations": total_observations,
            "latest_observation_date": latest_observation_date,
            "parents": [
                {
                    "id": p.id,
                    "full_name": p.full_name,
                    "email": p.email,
                    "children_count": len(p.children),
                }
                for p in parents
            ],
        }
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/professionals/analytics")
def get_professional_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
):
    """Overall analytics for a professional: domain breakdown across ALL their
    assigned children, plus a per-child summary (total observations, primary
    domain, latest observation date). This is the 'necessary output based on
    the observation' view for the professional's whole caseload."""
    try:
        parents = current_user.assigned_parents
        all_children = [c for p in parents for c in p.children]
        child_ids = [c.id for c in all_children]

        if not child_ids:
            return {
                "total_parents": len(parents),
                "total_children": 0,
                "total_observations": 0,
                "domain_breakdown": [],
                "timeline": [],
                "parent_breakdown": [],
                "children": [],
            }

        # ---- Domain breakdown across every child this professional can see ----
        domain_rows = (
            db.query(Observation.domain, func.count(Observation.id))
            .filter(Observation.child_id.in_(child_ids))
            .group_by(Observation.domain)
            .order_by(func.count(Observation.id).desc())
            .all()
        )
        domain_breakdown = [{"domain": d, "count": c} for d, c in domain_rows]
        total_observations = sum(c for _, c in domain_rows)

        # ---- Overall observation trend (all children combined, by day) ----
        timeline_rows = (
            db.query(func.date(Observation.observation_date).label("date"), func.count(Observation.id).label("count"))
            .filter(Observation.child_id.in_(child_ids))
            .group_by(func.date(Observation.observation_date))
            .order_by(func.date(Observation.observation_date).asc())
            .all()
        )
        timeline = [
            {"date": item.date.isoformat() if hasattr(item.date, "isoformat") else str(item.date), "count": item.count}
            for item in timeline_rows
        ]

        # ---- Observations rolled up per parent ----
        parent_rows = (
            db.query(User.id, User.full_name, User.email, func.count(Observation.id))
            .join(Child, Child.parent_id == User.id)
            .join(Observation, Observation.child_id == Child.id)
            .filter(Child.id.in_(child_ids))
            .group_by(User.id)
            .order_by(func.count(Observation.id).desc())
            .all()
        )
        parent_breakdown = [
            {"parent_id": pid, "parent_name": name, "parent_email": email, "total_observations": count}
            for pid, name, email, count in parent_rows
        ]

        # ---- Per-child summary ----
        children_summary = []
        for child in all_children:
            child_domain_rows = (
                db.query(Observation.domain, func.count(Observation.id))
                .filter(Observation.child_id == child.id)
                .group_by(Observation.domain)
                .order_by(func.count(Observation.id).desc())
                .all()
            )
            latest = (
                db.query(Observation)
                .filter(Observation.child_id == child.id)
                .order_by(Observation.observation_date.desc())
                .first()
            )
            children_summary.append({
                "child_id": child.id,
                "child_name": child.name,
                "parent_name": child.parent.full_name if child.parent else None,
                "parent_email": child.parent.email if child.parent else None,
                "total_observations": sum(c for _, c in child_domain_rows),
                "primary_domain": child_domain_rows[0][0] if child_domain_rows else None,
                "domain_breakdown": [{"domain": d, "count": c} for d, c in child_domain_rows],
                "latest_observation_date": latest.observation_date if latest else None,
            })

        # Sort children by total_observations desc so the busiest cases surface first
        children_summary.sort(key=lambda c: c["total_observations"], reverse=True)

        return {
            "total_parents": len(parents),
            "total_children": len(all_children),
            "total_observations": total_observations,
            "domain_breakdown": domain_breakdown,
            "timeline": timeline,
            "parent_breakdown": parent_breakdown,
            "children": children_summary,
        }
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/professionals/parents/{parent_id}/children", response_model=list[ChildOut])
def get_children_for_assigned_parent(
    parent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_professional),
):
    """Professional views children under one of their assigned parents."""
    try:
        parent = db.query(User).filter(User.id == parent_id, User.role == "parent").first()
        if not parent or parent.id not in {p.id for p in current_user.assigned_parents}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This parent is not associated with you.")
        return parent.children
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


# ==================== ADMIN ENDPOINTS ====================

@app.get("/api/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin dashboard statistics"""
    try:
        total_users = db.query(User).count()
        parents = db.query(User).filter(User.role == "parent").count()
        professionals = db.query(User).filter(User.role == "professional").count()
        children = db.query(Child).count()
        observations = db.query(Observation).count()
        
        return {
            "total_users": total_users,
            "parents": parents,
            "professionals": professionals,
            "admins": db.query(User).filter(User.role == "admin").count(),
            "children": children,
            "observations": observations,
            "feedback_count": db.query(Feedback).count(),
        }
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/admin/users", response_model=list[UserOut])
def admin_get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    role: str | None = Query(default=None),
):
    """Admin views all users"""
    try:
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)
        return query.order_by(User.created_at.desc()).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.patch("/api/admin/users/{user_id}/status")
def admin_toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin activate/deactivate user"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        
        user.is_active = not user.is_active
        db.commit()
        
        log = ActivityLog(
            user_id=current_user.id,
            action="user_status_changed",
            description=f"User {user.full_name} status changed to {'active' if user.is_active else 'inactive'}",
        )
        db.add(log)
        db.commit()
        
        return {"message": f"User status updated to {'active' if user.is_active else 'inactive'}.", "user": UserOut.model_validate(user)}
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


@app.get("/api/admin/activity-logs", response_model=list[ActivityLogOut])
def admin_get_activity_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Admin views activity logs"""
    try:
        return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


# ==================== FEEDBACK ====================

@app.post("/api/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create feedback on an observation or AI response"""
    try:
        db_feedback = Feedback(
            user_id=current_user.id,
            observation_id=feedback.observation_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database error.") from exc


# ==================== HEALTH CHECK ====================

@app.get("/api/health/db")
def database_health():
    if check_database_available():
        return {"status": "ok"}
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database is unavailable. Please check the database file and try again.",
    )
