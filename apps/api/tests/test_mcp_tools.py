import pytest
from tools.student_lookup import student_lookup
from tools.course_lookup import course_lookup
from tools.register_course import register_course

def test_student_lookup_valid():
    res = student_lookup({"student_id": "STU-1001"})
    assert "error" not in res
    assert res["student_id"] == "STU-1001"
    assert res["name"] == "Aarav Patel"
    assert res["cumulative_gpa"] == 3.85
    assert res["attendance_pct"] == 88
    assert res["eligible_for_exams"] is True

def test_student_lookup_not_found():
    res = student_lookup({"student_id": "STU-9999"})
    assert "error" in res
    assert res["code"] == "STUDENT_NOT_FOUND"

def test_student_lookup_invalid_input():
    res = student_lookup({})
    assert "error" in res
    assert res["code"] == "INVALID_INPUT"

def test_course_lookup_valid():
    res = course_lookup({"course_code": "CS-301"})
    assert "error" not in res
    assert res["course_code"] == "CS-301"
    assert res["title"] == "Database Management Systems"
    assert res["seats_available"] > 0
    assert "instructor" in res

def test_course_lookup_not_found():
    res = course_lookup({"course_code": "INVALID-999"})
    assert "error" in res
    assert res["code"] == "COURSE_NOT_FOUND"

def test_course_lookup_invalid_input():
    res = course_lookup({})
    assert "error" in res
    assert res["code"] == "INVALID_INPUT"

def test_register_course_valid():
    res = register_course({"student_id": "STU-1001", "course_code": "CS-301"})
    assert "error" not in res
    assert res["enrolled"] is True
    assert "registration_id" in res

def test_register_course_missing_fields():
    res = register_course({"student_id": "STU-1001"})
    assert "error" in res
    assert res["code"] == "MISSING_REQUIRED_FIELDS"
