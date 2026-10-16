import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("mcp_tools.course_lookup")
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data", "courses.json")

def course_lookup(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lookup course details by course_code.
    Input schema: {"course_code": str}
    Output schema: course details or structured error.
    """
    logger.info(f"Invoking course_lookup with input: {input_data}")
    
    if not isinstance(input_data, dict) or "course_code" not in input_data:
        return {
            "error": "Invalid input schema: 'course_code' is required as a string.",
            "code": "INVALID_INPUT"
        }
    
    course_code = str(input_data["course_code"]).strip().upper().replace(" ", "-")
    if not course_code:
        return {
            "error": "Course code cannot be empty.",
            "code": "EMPTY_COURSE_CODE"
        }
        
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            courses = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read courses catalog: {e}")
        return {
            "error": "Internal database error while accessing course catalog.",
            "code": "DATABASE_ERROR"
        }

    # Normalize lookup (e.g. CS301 -> CS-301)
    matched_key = None
    for k in courses.keys():
        if k == course_code or k.replace("-", "") == course_code.replace("-", ""):
            matched_key = k
            break

    if not matched_key:
        return {
            "error": f"Course '{course_code}' not found in the University course catalog.",
            "code": "COURSE_NOT_FOUND",
            "course_code": course_code
        }

    course = courses[matched_key]
    result = {
        "course_code": course["course_code"],
        "title": course["title"],
        "department": course["department"],
        "instructor": course["instructor"],
        "credits": course["credits"],
        "seats_available": course["seats_available"],
        "status": course["status"],
        "schedule": course["schedule"],
        "location": course["location"],
        "prerequisites": course["prerequisites"]
    }
    logger.info(f"course_lookup result: {result}")
    return result
