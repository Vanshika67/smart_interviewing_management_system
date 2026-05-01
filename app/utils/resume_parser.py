from __future__ import annotations

from pathlib import Path
from typing import Set

from PyPDF2 import PdfReader
from docx import Document


KNOWN_SKILLS = {
    "python",
    "flask",
    "django",
    "javascript",
    "html",
    "css",
    "react",
    "node",
    "mongodb",
    "sql",
    "git",
    "docker",
    "aws",
    "java",
    "c++",
    "data structures",
    "algorithms",
    "machine learning",
    "communication",
    "leadership",
}


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text_parts = []
        with path.open("rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    if suffix == ".docx":
        doc = Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    return ""


def extract_skills(raw_text: str) -> list[str]:
    text = raw_text.lower()
    found: Set[str] = set()
    for skill in KNOWN_SKILLS:
        if skill in text:
            found.add(skill)
    return sorted(found)
