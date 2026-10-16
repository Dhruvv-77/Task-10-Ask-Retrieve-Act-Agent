"""
Populate University Policy Documents and Ingest into ChromaDB Vector Store
"""

import os
import sys

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "documents"))

UNIVERSITY_DOCS = [
    {
        "filename": "policy-001_grading_system_and_gpa.md",
        "title": "Academic Grading Scale and Dean's Honor List",
        "docId": "policy-001",
        "content": """# Academic Grading Scale and Dean's Honor List (Doc ID: policy-001)

## 1. Grading Scale
The University computes Grade Point Averages (GPA) on a standard 4.0 scale:
- Grade A: 4.00 (93-100%) - Excellent
- Grade A-: 3.70 (90-92%)
- Grade B+: 3.30 (87-89%)
- Grade B: 3.00 (83-86%) - Good
- Grade B-: 2.70 (80-82%)
- Grade C+: 2.30 (77-79%)
- Grade C: 2.00 (73-76%) - Satisfactory / Minimum Passing for Major Core
- Grade D: 1.00 (60-72%) - Minimum Passing for General Electives
- Grade F: 0.00 (< 60%) - Failing Grade

## 2. Dean's Honor List
Undergraduate students who achieve a semester GPA of 3.75 or higher while completing a minimum of 12 letter-graded credit hours are awarded Dean's Honor List distinction. Students with Incomplete (I) grades or disciplinary sanctions are ineligible."""
    },
    {
        "filename": "policy-002_attendance_and_absence_rules.md",
        "title": "Mandatory Attendance and Final Examination Eligibility",
        "docId": "policy-002",
        "content": """# Mandatory Attendance and Final Examination Eligibility (Doc ID: policy-002)

## 1. 75% Attendance Requirement
Regular and punctual class attendance is mandatory in all registered lecture, seminar, and laboratory sections. To be eligible to sit for the final semester examination in any course, students must maintain a minimum documented attendance of 75.0% across all scheduled class sessions.

## 2. Debarment from Final Examinations
Students whose attendance in a course falls below 75% without authorized medical or institutional leave are classified as 'Debarred' and will receive an automatic grade of 'FA' (Failure due to Absences).

## 3. Excused Medical Absences
Absences due to illness must be supported by official medical documentation submitted to the Student Health Center and Academic Dean within 5 business days of returning to campus."""
    },
    {
        "filename": "policy-003_course_drop_add_deadlines.md",
        "title": "Course Registration, Add/Drop Deadlines, and Withdrawals",
        "docId": "policy-003",
        "content": """# Course Registration, Add/Drop Deadlines, and Withdrawals (Doc ID: policy-003)

## 1. Add/Drop Period
Students may freely add or drop courses without academic or financial penalty through the official Add/Drop window, which closes at 11:59 PM EST on Friday of the second instructional week (Week 2) of the semester.

## 2. Course Withdrawal ('W' Grade)
Following the close of Week 2, students may officially withdraw from a course through the end of Week 8. A grade of 'W' (Withdrawn) will appear on the student transcript. The 'W' grade carries 0.00 quality points and does NOT negatively affect the student's cumulative GPA.

## 3. Late Withdrawals
Withdrawals after Week 8 require Dean's emergency medical approval; otherwise, an earned letter grade is recorded."""
    },
    {
        "filename": "policy-004_tuition_fee_refund_schedule.md",
        "title": "Tuition Adjustment and Fee Refund Schedule",
        "docId": "policy-004",
        "content": """# Tuition Adjustment and Fee Refund Schedule (Doc ID: policy-004)

## 1. Withdrawal Refund Windows
Tuition fee refunds for students who withdraw from courses or take an approved leave of absence are calculated according to the academic calendar:
- Prior to the first day of classes: 100% tuition refund (less $50 administrative fee).
- During Week 1 of the semester: 80% tuition refund.
- During Week 2 of the semester: 50% tuition refund.
- After Week 2 (following Add/Drop deadline): 0% refund (no tuition credit granted).

## 2. Non-Refundable Fees
Campus technology fees, student activity fees, and lab consumable fees are strictly non-refundable once the semester officially commences."""
    },
    {
        "filename": "policy-005_academic_probation_and_suspension.md",
        "title": "Academic Standing, Probation, and Suspension Standards",
        "docId": "policy-005",
        "content": """# Academic Standing, Probation, and Suspension Standards (Doc ID: policy-005)

## 1. Good Academic Standing
An undergraduate student is in Good Academic Standing if their cumulative Grade Point Average (CGPA) is 2.00 or higher.

## 2. Academic Probation
Any student whose cumulative GPA drops below 2.00 at the end of any regular semester is automatically placed on Academic Probation. While on probation:
- The student may register for a maximum of 13 credit hours per semester.
- The student is restricted from holding office in student organizations or representing the university in athletics.

## 3. Academic Suspension
If a student on Academic Probation fails to raise their cumulative GPA to at least 2.00 after two consecutive regular semesters, they are placed on Academic Suspension for a minimum of one full academic term."""
    },
    {
        "filename": "policy-006_scholarship_eligibility_criteria.md",
        "title": "University Merit Scholarships and Financial Aid Renewal",
        "docId": "policy-006",
        "content": """# University Merit Scholarships and Financial Aid Renewal (Doc ID: policy-006)

## 1. Presidential and Provost Merit Scholarships
The Presidential Merit Scholarship covers 100% tuition and requires recipients to maintain a cumulative GPA of 3.60 or higher with full-time enrollment (minimum 12 credits/semester). The Provost Scholarship covers 50% tuition and requires a cumulative GPA of 3.40.

## 2. Annual Renewal Review
Scholarship standings are evaluated at the conclusion of each Spring semester. Students who fall below the required GPA threshold are given a one-semester grace period before financial aid reduction takes effect.

## 3. Need-Based Grants
Institutional need-based grants require maintaining Satisfactory Academic Progress (SAP) and cumulative GPA >= 2.00."""
    },
    {
        "filename": "policy-007_dormitory_hostel_housing_rules.md",
        "title": "Campus Residential Life, Curfew, and Housing Guidelines",
        "docId": "policy-007",
        "content": """# Campus Residential Life, Curfew, and Housing Guidelines (Doc ID: policy-007)

## 1. Quiet Hours and Curfew
Quiet hours in all university dormitories are enforced Sunday through Thursday from 10:00 PM to 8:00 AM, and Friday through Saturday from 12:00 Midnight to 9:00 AM. External residential gates require student keycard access after 11:00 PM.

## 2. Room Change Requests
Students seeking room transfers may submit requests to Residential Life beginning the third week of classes. Transfers are granted subject to space availability and roommate mediation.

## 3. Prohibited Items
Cooking appliances with exposed heating coils, candles, space heaters, and unauthorized pets (excluding registered service animals) are strictly prohibited."""
    },
    {
        "filename": "policy-008_library_borrowing_and_fines.md",
        "title": "University Library Borrowing Privileges and Overdue Fines",
        "docId": "policy-008",
        "content": """# University Library Borrowing Privileges and Overdue Fines (Doc ID: policy-008)

## 1. Borrowing Limits
- Undergraduate Students: Up to 10 books for 21 calendar days, with 2 online renewals permitted.
- Graduate Students: Up to 25 books for 60 calendar days.
- Course Reserve Textbooks: 3-hour in-library use only.

## 2. Overdue Fines and Account Holds
Overdue fines for general circulating materials accrue at $0.50 per item per day. Reserve items accrue at $1.00 per hour. If unpaid library fines exceed $25.00, an automatic Registrar Hold is placed on the student account, preventing course registration and transcript issuance."""
    },
    {
        "filename": "policy-009_graduation_credit_requirements.md",
        "title": "Undergraduate Degree Completion and Graduation Requirements",
        "docId": "policy-009",
        "content": """# Undergraduate Degree Completion and Graduation Requirements (Doc ID: policy-009)

## 1. Total Credit Hours
To qualify for a Bachelor of Science or Bachelor of Arts degree, students must successfully complete a minimum of 120 semester credit hours, including:
- 36 General Education Core credits.
- Minimum 45 Major specific credits (with at least 30 upper-division credits at 300+ level).
- Elective credits satisfying total degree requirements.

## 2. Minimum Cumulative GPA
A cumulative GPA of at least 2.00 overall and 2.25 within the declared Major is required for graduation.

## 3. Residency Requirement
The final 30 credit hours must be earned in residence at this university."""
    },
    {
        "filename": "policy-010_parking_permit_and_transit.md",
        "title": "Campus Parking Permits and Shuttle Transportation",
        "docId": "policy-010",
        "content": """# Campus Parking Permits and Shuttle Transportation (Doc ID: policy-010)

## 1. Parking Permit Classes
All motor vehicles parked on campus property must display a valid digital permit:
- Commuter Permit (Blue Lot): $120 per semester.
- Resident Permit (Green Lot): $160 per semester.

## 2. Shuttle Schedule
Free campus shuttles operate along Blue and Green routes every 10 minutes between 7:00 AM and 10:00 PM on weekdays. Weekend shuttles operate every 25 minutes.

## 3. Violations and Towing
Vehicles parked in fire lanes, ADA spaces without credentials, or unauthorized faculty zones are subject to an immediate $75 citation and immobilization towing."""
    },
    {
        "filename": "policy-011_health_center_and_counseling.md",
        "title": "Student Health Services and Psychological Counseling",
        "docId": "policy-011",
        "content": """# Student Health Services and Psychological Counseling (Doc ID: policy-011)

## 1. Primary Medical Care
All enrolled students taking 6 or more credits have access to on-campus outpatient health visits at zero copay. Basic wellness exams, rapid strep/flu tests, and triage nursing are provided at no charge.

## 2. Confidential Mental Health Counseling
The University Counseling Center provides up to 10 free individual counseling sessions per academic year. Crisis walk-in hours are open 24/7.

## 3. Mandatory Immunizations
State regulations require proof of MMR, Tdap, Hepatitis B, and Meningococcal vaccines prior to residential dorm move-in."""
    },
    {
        "filename": "policy-012_student_conduct_and_plagiarism.md",
        "title": "Academic Integrity, Plagiarism, and Code of Conduct",
        "docId": "policy-012",
        "content": """# Academic Integrity, Plagiarism, and Code of Conduct (Doc ID: policy-012)

## 1. Definition of Academic Misconduct
Academic misconduct includes submitting work written by another person or unapproved AI tool, copying exam answers, unauthorized collaboration, and failing to properly cite scholarly sources.

## 2. Penalties
- First Violation: Recorded sanction and automatic grade of Zero ('F') on the assignment/exam.
- Second Violation: Automatic failure of the course ('XF' on transcript) and referral to the Academic Disciplinary Board for potential semester suspension.

## 3. Appeal Rights
Students have 10 business days to file an appeal with the Dean of Academic Affairs."""
    },
    {
        "filename": "policy-013_career_services_and_internships.md",
        "title": "Campus Employment, Internships, and CPT/OPT Guidelines",
        "docId": "policy-013",
        "content": """# Campus Employment, Internships, and CPT/OPT Guidelines (Doc ID: policy-013)

## 1. On-Campus Student Employment Limits
Enrolled students holding on-campus student worker or teaching assistant positions may work a maximum of 20 hours per week during active academic semesters, and up to 40 hours per week during university break periods.

## 2. Curricular Practical Training (CPT)
International F-1 students become eligible for off-campus internships via CPT after completing two consecutive full-time semesters in the United States in valid student status."""
    },
    {
        "filename": "policy-014_campus_wifi_and_it_acceptable_use.md",
        "title": "Campus Information Technology and Network Acceptable Use",
        "docId": "policy-014",
        "content": """# Campus Information Technology and Network Acceptable Use (Doc ID: policy-014)

## 1. Campus Network Access
Campus Wi-Fi ('Eduroam') requires authentication using primary university email credentials. Guest Wi-Fi ('Campus-Guest') is limited to basic web browsing and bandwidth-capped at 5 Mbps.

## 2. Prohibited Network Activities
Peer-to-peer file sharing (BitTorrent), unauthorized vulnerability scanning, commercial hosting, and cryptocurrency mining on university servers or student network jacks are grounds for immediate termination of network privileges."""
    },
    {
        "filename": "policy-015_dining_hall_meal_plans.md",
        "title": "Campus Dining Services and Meal Plan Rollover Rules",
        "docId": "policy-015",
        "content": """# Campus Dining Services and Meal Plan Rollover Rules (Doc ID: policy-015)

## 1. Meal Plans
- All-Access Plan: Unlimited entry to residential dining halls + $250 Dining Dollars.
- Block 150 Plan: 150 meal swipes per semester + $400 Dining Dollars.

## 2. Rollover Policies
Dining Dollars roll over from the Fall semester to the Spring semester if a Spring meal plan is maintained. All unused meal swipes and Dining Dollars expire without refund on the final day of the Spring semester."""
    },
    {
        "filename": "policy-016_study_abroad_prerequisites.md",
        "title": "International Exchange and Study Abroad Eligibility",
        "docId": "policy-016",
        "content": """# International Exchange and Study Abroad Eligibility (Doc ID: policy-016)

## 1. Minimum Eligibility Requirements
Undergraduate students applying for semester exchange programs must meet the following criteria:
- Minimum Sophomore standing (at least 30 credit hours completed).
- Cumulative GPA of 2.80 or higher at the time of application.
- Clear disciplinary record with no active university sanctions.

## 2. Application Deadlines
Fall semester programs: March 15. Spring semester programs: October 15."""
    },
    {
        "filename": "policy-017_leave_of_absence_medical.md",
        "title": "Leave of Absence and Medical Withdrawal Procedures",
        "docId": "policy-017",
        "content": """# Leave of Absence and Medical Withdrawal Procedures (Doc ID: policy-017)

## 1. Term of Leave
Students in good standing may request an official Leave of Absence (LOA) for personal or medical reasons for up to two consecutive regular semesters.

## 2. Readmission Process
Students on approved LOA retain their university catalog year and do not pay readmission fees. For medical leaves, a return clearance letter from a licensed healthcare provider is required 30 days prior to semester registration."""
    },
    {
        "filename": "policy-018_student_club_funding_guidelines.md",
        "title": "Student Organizations and SGA Budget Allocation",
        "docId": "policy-018",
        "content": """# Student Organizations and SGA Budget Allocation (Doc ID: policy-018)

## 1. Registered Student Organizations (RSO)
RSOs with at least 10 active student members and a full-time faculty advisor may apply for annual programming grants from the Student Government Association (SGA).

## 2. Funding Caps
New clubs are eligible for up to $1,000 in baseline operating funds. Established clubs may request up to $5,000 for academic conferences and campus-wide cultural events."""
    },
    {
        "filename": "policy-019_exam_rescheduling_conflicts.md",
        "title": "Final Examination Conflicts and Rescheduling Policy",
        "docId": "policy-019",
        "content": """# Final Examination Conflicts and Rescheduling Policy (Doc ID: policy-019)

## 1. Three-Exam Conflict Rule
A student who has three final examinations scheduled on the same calendar day, or two examinations scheduled at the exact same hour, has the right to reschedule the middle examination.

## 2. Request Procedure
The student must submit an Exam Conflict Form to the Office of the University Registrar at least 14 calendar days prior to the start of the final examination period."""
    },
    {
        "filename": "policy-020_official_transcript_and_diplomas.md",
        "title": "Transcript Ordering, Diploma Distribution, and Account Holds",
        "docId": "policy-020",
        "content": """# Transcript Ordering, Diploma Distribution, and Account Holds (Doc ID: policy-020)

## 1. Official Transcript Requests
Official digital transcripts are delivered electronically via National Student Clearinghouse within 24 business hours for a standard fee of $10.00. Expedited paper transcripts cost $25.00.

## 2. Financial and Disciplinary Holds
Transcripts and physical diplomas cannot be released to any student with an outstanding financial balance exceeding $50.00 or an unresolved disciplinary hold."""
    }
]

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for doc in UNIVERSITY_DOCS:
        file_path = os.path.join(DATA_DIR, doc["filename"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(doc["content"].strip() + "\n")
        print(f"Created: {doc['filename']}")
    print(f"\nSuccessfully wrote {len(UNIVERSITY_DOCS)} university policy files to {DATA_DIR}")

if __name__ == "__main__":
    main()
