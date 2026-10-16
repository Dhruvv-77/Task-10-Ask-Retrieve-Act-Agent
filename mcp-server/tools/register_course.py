import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("mcp_tools.register_course")
REGISTRATIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data", "registrations.json")
COURSES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mock_data", "courses.json")

def register_course(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enroll a student into a university course.
    Note: State-mutating operation requiring guardrail confirmation.
    Input schema: {"student_id": str, "course_code": str}
    """
    logger.info(f"Invoking register_course with input: {input_data}")
    
    student_id = str(input_data.get("student_id", "")).strip().upper()
    course_code = str(input_data.get("course_code", "")).strip().upper().replace(" ", "-")
    
    if not student_id or not course_code:
        return {
            "error": "Both 'student_id' and 'course_code' are required for course enrollment.",
            "code": "MISSING_REQUIRED_FIELDS"
        }
        
    try:
        registrations = {}
        if os.path.exists(REGISTRATIONS_PATH):
            with open(REGISTRATIONS_PATH, "r", encoding="utf-8") as f:
                registrations = json.load(f)
                
        reg_id = f"REG-{student_id}-{course_code}"
        registrations[reg_id] = {
            "registration_id": reg_id,
            "student_id": student_id,
            "course_code": course_code,
            "status": "Enrolled",
            "enrolled_at": "2026-10-16T12:00:00Z"
        }
        
        with open(REGISTRATIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(registrations, f, indent=2)
            
        logger.info(f"Successfully registered {student_id} into {course_code}")
        return {
            "registration_id": reg_id,
            "student_id": student_id,
            "course_code": course_code,
            "status": "Enrolled",
            "enrolled": True
        }
    except Exception as e:
        logger.error(f"Failed to register course: {e}")
        return {
            "error": f"Failed to complete course enrollment: {str(e)}",
            "code": "REGISTRATION_FAILED"
        }
