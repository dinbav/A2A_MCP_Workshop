import json
import logging
from pathlib import Path
from copy import deepcopy

from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger("mcp.learning.tools")

mcp = FastMCP()

# ---------------------------------------------------------------------------
# Load all static data files at startup
# ---------------------------------------------------------------------------
_DATA_DIR = Path(__file__).parent / "data"

with open(_DATA_DIR / "learning" / "topics.json", encoding="utf-8") as _f:
    TOPICS: dict = json.load(_f)

with open(_DATA_DIR / "learning" / "assessment_questions.json", encoding="utf-8") as _f:
    ASSESSMENT_QUESTIONS: dict = json.load(_f)

with open(_DATA_DIR / "learning" / "study_paths.json", encoding="utf-8") as _f:
    STUDY_PATHS: dict = json.load(_f)

with open(_DATA_DIR / "learning" / "user_learning_state.json", encoding="utf-8") as _f:
    _SEED_STATE: dict = json.load(_f)

with open(_DATA_DIR / "career" / "job_descriptions.json", encoding="utf-8") as _f:
    JOB_DESCRIPTIONS: dict = json.load(_f)

with open(_DATA_DIR / "career" / "sample_resumes.json", encoding="utf-8") as _f:
    SAMPLE_RESUMES: dict = json.load(_f)

with open(_DATA_DIR / "career" / "skill_map.json", encoding="utf-8") as _f:
    SKILL_MAP: dict = json.load(_f)

# In-memory learning state (seeded from JSON, updated by update_learning_state)
_LEARNING_STATE: dict = deepcopy(_SEED_STATE)

VALID_TOPICS  = list(TOPICS.keys())
VALID_LEVELS  = ["beginner", "intermediate", "advanced"]
VALID_TIMES   = ["30_minutes", "2_hours", "1_day"]
LEVEL_ORDER   = {"beginner": 0, "intermediate": 1, "advanced": 2}
LEVEL_UP      = {0: "intermediate", 1: "advanced", 2: "advanced"}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(tags={"topic", "explanation"})
def get_topic_summary(topic: str, level: str = "beginner") -> dict:
    """
    Get a structured summary of a learning topic at a specific level.

    Args:
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async
        level: One of: beginner, intermediate, advanced

    Returns:
        Dict with topic, level, summary, key_concepts, common_misconceptions,
        next_step suggestion, and data_source.
    """
    topic_key = topic.lower().strip().replace(" ", "_")
    level_key = level.lower().strip()

    if topic_key not in TOPICS:
        return {
            "topic": topic,
            "level": level,
            "found": False,
            "message": f"Topic '{topic}' not found. Available topics: {', '.join(VALID_TOPICS)}.",
            "data_source": "local_json",
        }

    if level_key not in VALID_LEVELS:
        level_key = "beginner"

    data = TOPICS[topic_key][level_key]

    return {
        "topic": topic_key,
        "level": level_key,
        "found": True,
        "summary": data["summary"],
        "key_concepts": data["key_concepts"],
        "common_misconceptions": data["common_misconceptions"],
        "next_step": data.get("next_step", ""),
        "data_source": "local_json",
    }


@mcp.tool(tags={"assessment", "quiz"})
def get_assessment_questions_by_topic(
    topic: str,
    level: str = "beginner",
    limit: int = 4,
) -> dict:
    """
    Get assessment questions for a topic at a given level.

    Args:
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async
        level: One of: beginner, intermediate, advanced
        limit: Maximum number of questions to return (default 4)

    Returns:
        Dict with topic, level, questions list, and data_source.
        Each question has: id, question, expected_answer, explanation, level, score_weight.
    """
    topic_key = topic.lower().strip().replace(" ", "_")
    level_key = level.lower().strip()

    if topic_key not in ASSESSMENT_QUESTIONS:
        return {
            "topic": topic,
            "level": level,
            "found": False,
            "questions": [],
            "message": f"Topic '{topic}' not found. Available topics: {', '.join(VALID_TOPICS)}.",
            "data_source": "local_json",
        }

    if level_key not in VALID_LEVELS:
        level_key = "beginner"

    questions = ASSESSMENT_QUESTIONS[topic_key].get(level_key, [])
    limited = questions[:max(1, min(limit, len(questions)))]

    return {
        "topic": topic_key,
        "level": level_key,
        "found": True,
        "questions": limited,
        "total_available": len(questions),
        "data_source": "local_json",
    }


@mcp.tool(tags={"assessment", "state"})
def get_learning_state(user_id: str, topic: str) -> dict:
    """
    Get the current learning state for a user on a specific topic.

    Args:
        user_id: User identifier (e.g. "user_1")
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async

    Returns:
        Dict with current_level, answered_questions, correct_answers,
        total_answers, confidence_score, and data_source.
    """
    topic_key = topic.lower().strip().replace(" ", "_")

    user_state = _LEARNING_STATE.get(user_id, {})
    topic_state = user_state.get(topic_key)

    if topic_state is None:
        return {
            "user_id": user_id,
            "topic": topic_key,
            "current_level": "beginner",
            "answered_questions": [],
            "correct_answers": 0,
            "total_answers": 0,
            "confidence_score": 0.0,
            "note": "No prior state found. Starting at beginner level.",
            "data_source": "local_json",
        }

    return {
        "user_id": user_id,
        "topic": topic_key,
        "current_level": topic_state["current_level"],
        "answered_questions": topic_state.get("answered_questions", []),
        "correct_answers": topic_state.get("correct_answers", 0),
        "total_answers": topic_state.get("total_answers", 0),
        "confidence_score": topic_state.get("confidence_score", 0.0),
        "data_source": "local_json",
    }


@mcp.tool(tags={"assessment", "state"})
def update_learning_state(
    user_id: str,
    topic: str,
    correct_count: int,
    total_count: int,
) -> dict:
    """
    Update a user's learning state based on quiz results.

    Level-up logic:
    - score = correct_count / total_count
    - if score >= 0.75: advance one level (beginner → intermediate → advanced)
    - otherwise: stay at current level
    - advanced stays advanced

    Args:
        user_id: User identifier
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async
        correct_count: Number of questions answered correctly
        total_count: Total number of questions attempted

    Returns:
        Dict with previous_level, new_level, score, message, and data_source.
    """
    if total_count <= 0:
        return {
            "user_id": user_id,
            "topic": topic,
            "previous_level": "unknown",
            "new_level": "unknown",
            "score": 0.0,
            "message": "total_count must be greater than 0.",
            "data_source": "local_json",
        }

    topic_key = topic.lower().strip().replace(" ", "_")
    score = correct_count / total_count

    # Ensure user and topic structures exist
    if user_id not in _LEARNING_STATE:
        _LEARNING_STATE[user_id] = {}
    if topic_key not in _LEARNING_STATE[user_id]:
        _LEARNING_STATE[user_id][topic_key] = {
            "current_level": "beginner",
            "answered_questions": [],
            "correct_answers": 0,
            "total_answers": 0,
            "confidence_score": 0.0,
        }

    state = _LEARNING_STATE[user_id][topic_key]
    previous_level = state["current_level"]
    previous_idx   = LEVEL_ORDER.get(previous_level, 0)

    if score >= 0.75:
        new_level = LEVEL_UP[previous_idx]
        message = (
            f"Excellent! Score {score:.0%}. "
            f"Level advanced from {previous_level} to {new_level}."
            if new_level != previous_level
            else f"Outstanding! Score {score:.0%}. Already at maximum level: {new_level}."
        )
    else:
        new_level = previous_level
        message = (
            f"Score {score:.0%}. Staying at {new_level} level. "
            f"Aim for 75% or higher to advance."
        )

    # Update state
    state["current_level"]    = new_level
    state["correct_answers"]  = state.get("correct_answers", 0) + correct_count
    state["total_answers"]    = state.get("total_answers", 0) + total_count
    total_so_far = state["total_answers"]
    state["confidence_score"] = round(state["correct_answers"] / total_so_far, 2) if total_so_far else 0.0

    return {
        "user_id": user_id,
        "topic": topic_key,
        "previous_level": previous_level,
        "new_level": new_level,
        "score": round(score, 2),
        "message": message,
        "data_source": "local_json",
    }


@mcp.tool(tags={"study", "plan"})
def get_study_path(
    topic: str,
    level: str = "beginner",
    available_time: str = "2_hours",
) -> dict:
    """
    Get a personalized study path for a topic, level, and available time.

    Args:
        topic: One of: mcp, a2a, rag, prompt_engineering, python_async
        level: One of: beginner, intermediate, advanced
        available_time: One of: 30_minutes, 2_hours, 1_day

    Returns:
        Dict with learning_objectives, ordered_steps, practice_suggestions,
        estimated_total_time, and data_source.
    """
    topic_key = topic.lower().strip().replace(" ", "_")
    level_key = level.lower().strip()
    time_key  = available_time.lower().strip().replace(" ", "_")

    if topic_key not in STUDY_PATHS:
        return {
            "topic": topic,
            "level": level,
            "available_time": available_time,
            "found": False,
            "message": f"Topic '{topic}' not found. Available topics: {', '.join(VALID_TOPICS)}.",
            "data_source": "local_json",
        }

    if level_key not in VALID_LEVELS:
        level_key = "beginner"
    if time_key not in VALID_TIMES:
        time_key = "2_hours"

    path = STUDY_PATHS[topic_key][level_key][time_key]

    return {
        "topic": topic_key,
        "level": level_key,
        "available_time": time_key,
        "found": True,
        "learning_objectives": path["learning_objectives"],
        "ordered_steps": path["ordered_steps"],
        "practice_suggestions": path["practice_suggestions"],
        "estimated_total_time": path["estimated_total_time"],
        "data_source": "local_json",
    }


@mcp.tool(tags={"career", "job"})
def get_job_description(job_id: str) -> dict:
    """
    Get a job description by job ID.

    Args:
        job_id: One of: ai_engineer, data_scientist, backend_engineer

    Returns:
        Dict with job_id, title, required_skills, nice_to_have, description,
        experience_years, and data_source.
    """
    job_key = job_id.lower().strip().replace(" ", "_")

    if job_key not in JOB_DESCRIPTIONS:
        return {
            "job_id": job_id,
            "found": False,
            "message": f"Job '{job_id}' not found. Available jobs: {', '.join(JOB_DESCRIPTIONS.keys())}.",
            "data_source": "local_json",
        }

    job = JOB_DESCRIPTIONS[job_key]

    return {
        "job_id": job_key,
        "found": True,
        "title": job["title"],
        "description": job["description"],
        "required_skills": job["required_skills"],
        "nice_to_have": job["nice_to_have"],
        "experience_years": job["experience_years"],
        "data_source": "local_json",
    }


@mcp.tool(tags={"career", "resume"})
def get_resume_profile(candidate_id: str) -> dict:
    """
    Get a candidate resume profile by candidate ID.

    Args:
        candidate_id: One of: candidate_1, candidate_2

    Returns:
        Dict with candidate_id, name, current_role, skills, experience,
        learning_goals, and data_source.
    """
    candidate_key = candidate_id.lower().strip().replace(" ", "_")

    if candidate_key not in SAMPLE_RESUMES:
        return {
            "candidate_id": candidate_id,
            "found": False,
            "message": f"Candidate '{candidate_id}' not found. Available candidates: {', '.join(SAMPLE_RESUMES.keys())}.",
            "data_source": "local_json",
        }

    profile = SAMPLE_RESUMES[candidate_key]

    return {
        "candidate_id": candidate_key,
        "found": True,
        "name": profile["name"],
        "current_role": profile["current_role"],
        "skills": profile["skills"],
        "experience_years": profile["experience_years"],
        "experience": profile["experience"],
        "learning_goals": profile["learning_goals"],
        "data_source": "local_json",
    }


@mcp.tool(tags={"career", "gap"})
def get_skill_gap_analysis(job_id: str, candidate_id: str) -> dict:
    """
    Compute a skill gap analysis between a job description and a candidate resume.

    Uses job_descriptions.json, sample_resumes.json, and skill_map.json to
    determine matched skills, missing required skills, missing nice-to-have skills,
    and recommended learning topics.

    Args:
        job_id: One of: ai_engineer, data_scientist, backend_engineer
        candidate_id: One of: candidate_1, candidate_2

    Returns:
        Dict with matched_skills, missing_required_skills, missing_nice_to_have,
        recommended_learning_topics, and data_source.
    """
    job_key       = job_id.lower().strip().replace(" ", "_")
    candidate_key = candidate_id.lower().strip().replace(" ", "_")

    if job_key not in JOB_DESCRIPTIONS:
        return {
            "found": False,
            "message": f"Job '{job_id}' not found. Available: {', '.join(JOB_DESCRIPTIONS.keys())}.",
            "data_source": "local_json",
        }
    if candidate_key not in SAMPLE_RESUMES:
        return {
            "found": False,
            "message": f"Candidate '{candidate_id}' not found. Available: {', '.join(SAMPLE_RESUMES.keys())}.",
            "data_source": "local_json",
        }

    job       = JOB_DESCRIPTIONS[job_key]
    candidate = SAMPLE_RESUMES[candidate_key]

    candidate_skills = set(candidate["skills"])
    required_skills  = set(job["required_skills"])
    nice_to_have     = set(job["nice_to_have"])

    matched_required    = sorted(required_skills & candidate_skills)
    missing_required    = sorted(required_skills - candidate_skills)
    missing_nice        = sorted(nice_to_have - candidate_skills)

    # Map missing skills to learning topics
    recommended_topics = set()
    for skill in missing_required + missing_nice:
        skill_info = SKILL_MAP.get(skill, {})
        topic = skill_info.get("learning_topic")
        if topic and topic in VALID_TOPICS:
            recommended_topics.add(topic)

    # Prioritise topics for missing required skills first
    priority_topics = set()
    for skill in missing_required:
        skill_info = SKILL_MAP.get(skill, {})
        topic = skill_info.get("learning_topic")
        if topic and topic in VALID_TOPICS:
            priority_topics.add(topic)

    return {
        "job_id": job_key,
        "candidate_id": candidate_key,
        "job_title": job["title"],
        "candidate_name": candidate["name"],
        "found": True,
        "matched_skills": matched_required,
        "missing_required_skills": missing_required,
        "missing_nice_to_have": missing_nice,
        "recommended_learning_topics": sorted(priority_topics) + sorted(recommended_topics - priority_topics),
        "data_source": "local_json",
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8004, path="/mcp", log_level="info")
