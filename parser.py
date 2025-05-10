import pandas as pd
import json
from typing import Dict, List, Any

def extract_mandatory_courses(excel_path: str) -> List[Dict[str, Any]]:
    """Extract mandatory courses from curriculum Excel document."""
    df = pd.read_excel("Template.xlsx", header=None)
    
    rows = [(i, str(row.iloc[2]) if not pd.isna(row.iloc[2]) else "") for i, row in df.iterrows()]
    start_idx = next(i+1 for i, text in rows if text == "Majburiy fanlar")
    end_idx = next(i for i, text in rows if text == "Tanlov fanlari")
    
    course_df = df.iloc[start_idx:end_idx].copy()
    
    cols = ["index", "course_code", "course_title", "total_hours", "total_class_hours", 
            "lecture_hours", "practice_hours", "lab_hours", "seminar_hours", 
            "course_work_hours", "independent_hours",
            "sem1", "sem2", "sem3", "sem4", "sem5", "sem6", "sem7", "sem8", "total_credits"]
    
    col_count = len(course_df.columns)
    col_names = cols + list(range(col_count - len(cols)))
    course_df.columns = col_names
    
    valid_courses = [row for _, row in course_df.iterrows() 
                    if not pd.isna(row['index']) and not pd.isna(row['course_code'])]
    
    courses = [
        {
            "course_code": row['course_code'],
            "course_title": row['course_title'],
            "total_hours": int(row['total_hours']) if not pd.isna(row['total_hours']) else 0,
            "hours": {
                "lecture": int(row['lecture_hours']) if not pd.isna(row['lecture_hours']) else 0,
                "practice": int(row['practice_hours']) if not pd.isna(row['practice_hours']) else 0,
                "laboratory": int(row['lab_hours']) if not pd.isna(row['lab_hours']) else 0,
                "seminar": int(row['seminar_hours']) if not pd.isna(row['seminar_hours']) else 0,
                "independent": int(row['independent_hours']) if not pd.isna(row['independent_hours']) else 0
            },
            "credits": {
                sem: int(row[f'sem{sem}']) if not pd.isna(row[f'sem{sem}']) else 0
                for sem in range(1, 9)
            },
            "total_credits": int(row['total_credits']) if not pd.isna(row['total_credits']) else 0
        }
        for row in valid_courses
    ]
    
    return courses

def main():

    courses = extract_mandatory_courses("Template.xlsx")
    
    # Save to JSON with proper encoding
    with open("mandatory_courses.json", "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted {len(courses)} mandatory courses:")
    for course in courses[:3]:
        print(f"- {course['course_code']}: {course['course_title']} ({course['total_credits']} credits)")
    if len(courses) > 3:
        print(f"- ... and {len(courses) - 3} more courses")

if __name__ == "__main__":
    main()