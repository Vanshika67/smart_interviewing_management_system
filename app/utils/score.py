from __future__ import annotations


REQUIRED_SKILLS = {
    "python",
    "flask",
    "mongodb",
    "javascript",
    "html",
    "css",
    "communication",
}


def calculate_score(candidate_skills: list[str]) -> int:
    if not REQUIRED_SKILLS:
        return 0
    matched = len(set(candidate_skills) & REQUIRED_SKILLS)
    score = int((matched / len(REQUIRED_SKILLS)) * 100)
    return max(0, min(100, score))


def interview_plan(score: int) -> str:
    if score >= 80:
        return "Round 1: Technical deep-dive | Round 2: System design | Round 3: HR discussion"
    if score >= 50:
        return "Round 1: Technical screening | Round 2: Coding task | Round 3: HR discussion"
    return "Round 1: Basic aptitude + communication | Round 2: Foundational technical screening"


def selection_status(score: int) -> str:
    return "Selected" if score >= 70 else "Under Review"

