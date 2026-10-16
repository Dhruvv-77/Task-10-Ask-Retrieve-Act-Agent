import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("mcp_tools.student_lookup")
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data", "students.json")

def student_lookup(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lookup student academic record by student_id.
    Input schema: {"student_id": str}
    Output schema: student record details or structured error.
    """
    logger.info(f"Invoking student_lookup with input: {input_data}")
    
    if not isinstance(input_data, dict) or "student_id" not in input_data:
        return {
            "error": "Invalid input schema: 'student_id' is required as a string.",
            "code": "INVALID_INPUT"
        }
    
    student_id = str(input_data["student_id"]).strip().upper()
    if not student_id:
        return {
            "error": "Student ID cannot be empty.",
            "code": "EMPTY_STUDENT_ID"
        }
        
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            students = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read students database: {e}")
        return {
            "error": "Internal database error while accessing students data.",
            "code": "DATABASE_ERROR"
        }

    if student_id not in students:
        return {
            "error": f"Student '{student_id}' not found in the University records.",
            "code": "STUDENT_NOT_FOUND",
            "student_id": student_id
        }

    student = students[student_id]
    result = {
        "student_id": student["student_id"],
        "name": student["name"],
        "major": student["major"],
        "year": student["year"],
        "cumulative_gpa": student["cumulative_gpa"],
        "attendance_pct": student["attendance_pct"],
        "academic_standing": student["academic_standing"],
        "eligible_for_exams": student["eligible_for_exams"],
        "holds": student["holds"],
        "enrolled_courses": student["enrolled_courses"]
    }
    logger.info(f"student_lookup result: {result}")
    return result
