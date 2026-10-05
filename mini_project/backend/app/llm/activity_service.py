import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Child, Observation, Activity
from .service import query_rag_knowledgebase  # Assuming your existing RAG retrieval helper

def generate_activity_recommendations(child_id: int, db: Session) -> Dict[str, Any]:
    # 1. Gather Child & Observation Context
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise ValueError("Child not found")

    recent_obs = (
        db.query(Observation)
        .filter(Observation.child_id == child.id)
        .order_by(Observation.observation_date.desc())
        .limit(5)
        .all()
    )

    observed_domains = list(set([o.domain for o in recent_obs if o.domain]))
    obs_summary = "; ".join([f"{o.domain}: {o.observation_text}" for o in recent_obs])
    child_interests = getattr(child, "interests", "Toy cars, drawing, building blocks")

    # 2. RAG Retrieval for Evidence-Based Strategy
    rag_query = f"Activities for age {child.age_months if hasattr(child, 'age_months') else 'toddler'} focused on domains: {', '.join(observed_domains)}"
    rag_context = query_rag_knowledgebase(rag_query)

    # 3. Formulate Prompt for LLM
    prompt = f"""
    You are a child development specialist. Suggest a fun, supportive caregiver-led activity.

    Child Context:
    - Interests: {child_interests}
    - Observed Domains needing focus: {observed_domains}
    - Recent Observations: {obs_summary}

    Evidence/Research Context:
    {rag_context.get('context', 'No specific guidelines retrieved.')}

    Return a JSON response with the following keys:
    {{
      "title": "Activity Name",
      "domain": "Target Domain",
      "description": "Short explanation",
      "materials": "Required items",
      "duration": "Estimated time",
      "steps": ["Step 1", "Step 2", "Step 3"],
      "observation_targets": "What caregiver should observe",
      "reasoning": "Why this activity was suggested based on interests and observations",
      "evidence_sources": ["Supporting reference or guideline"]
    }}
    Do NOT include medical treatment claims.
    """

    # Call LLM (using your LLM execution pattern)
    # Example mock fallback / formatted response wrapper:
    response_data = {
        "title": f"Take Turns With {child_interests.split(',')[0]}",
        "domain": observed_domains[0] if observed_domains else "Social Interaction",
        "description": f"An interactive play session structured around {child_interests.split(',')[0]} to encourage turn-taking.",
        "materials": "Toy cars or building blocks",
        "duration": "10-15 minutes",
        "steps": [
            "Set up a simple track or play zone.",
            "Say 'My turn!' and roll the car across.",
            "Prompt the child: 'Your turn!' and wait patiently.",
            "Celebrate each back-and-forth exchange."
        ],
        "observation_targets": "Notice eye contact, gesture sharing, and patience during waiting periods.",
        "reasoning": f"Suggested because the child enjoys {child_interests.split(',')[0]} and recent observations highlight opportunities in {observed_domains[0] if observed_domains else 'Social Interaction'}.",
        "evidence_sources": rag_context.get("sources", ["CDC Developmental Milestones & Early Intervention Guidelines"]),
        "disclaimer": "This activity is an optional educational suggestion and does not constitute medical advice or treatment."
    }

    return response_data