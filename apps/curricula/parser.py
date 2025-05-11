import pandas as pd
import json
from typing import Dict, List, Any, Optional

def parse_credit_value(value_from_excel: Any) -> Optional[int]:
    """Parses a credit value from Excel. Returns None for empty, '-', or unparseable values."""
    if pd.isna(value_from_excel):
        return None
    if isinstance(value_from_excel, str):
        stripped_value = value_from_excel.strip()
        if stripped_value == '' or stripped_value == '-':
            return None
    try:
        return int(value_from_excel)
    except (ValueError, TypeError):
        return None

def extract_mandatory_courses(excel_path: str) -> List[Dict[str, Any]]:
    df = pd.read_excel(excel_path, header=None)
   
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
                sem: parse_credit_value(row[f'sem{sem}'])
                for sem in range(1, 9)
            },
            "total_credits": int(row['total_credits']) if not pd.isna(row['total_credits']) else 0
        }
        for row in valid_courses
    ]
   
    return courses

def extract_selective_courses(excel_path: str) -> List[Dict[str, Any]]:
    df = pd.read_excel(excel_path, header=None)
   
    rows = [(i, str(row.iloc[2]) if not pd.isna(row.iloc[2]) else "") for i, row in df.iterrows()]
    selective_start_idx = next(i+1 for i, text in rows if text == "Tanlov fanlari")
    
    selective_df = df.iloc[selective_start_idx:].copy()
   
    cols = ["index", "course_code", "course_title", "total_hours", "total_class_hours",
            "lecture_hours", "practice_hours", "lab_hours", "seminar_hours",
            "course_work_hours", "independent_hours",
            "sem1", "sem2", "sem3", "sem4", "sem5", "sem6", "sem7", "sem8", "total_credits"]
   
    col_count = len(selective_df.columns)
    col_names = cols + list(range(col_count - len(cols)))
    selective_df.columns = col_names
    
    slots = []
    current_slot_num = None
    slot_metadata = {}
    slot_options = []
    
    for _, row in selective_df.iterrows():
        # Skip rows with no course information
        if pd.isna(row['course_code']) and pd.isna(row['course_title']):
            continue
            
        # Check for new slot
        if not pd.isna(row['index']):
            try:
                potential_slot_num = int(float(row['index']))
                
                # Save previous slot if it exists
                if current_slot_num is not None and slot_options:
                    slots.append({
                        "slot_number": current_slot_num,
                        "course_options": slot_options,
                        "total_hours": slot_metadata.get("total_hours", 0),
                        "hours": slot_metadata.get("hours", {}),
                        "credits": slot_metadata.get("credits", {}),
                        "total_credits": slot_metadata.get("total_credits", 0)
                    })
                
                # Start a new slot
                current_slot_num = potential_slot_num
                slot_options = []
                
                # Extract shared slot metadata
                slot_metadata = {
                    "total_hours": int(row['total_hours']) if not pd.isna(row['total_hours']) else 0,
                    "hours": {
                        "lecture": int(row['lecture_hours']) if not pd.isna(row['lecture_hours']) else 0,
                        "practice": int(row['practice_hours']) if not pd.isna(row['practice_hours']) else 0,
                        "laboratory": int(row['lab_hours']) if not pd.isna(row['lab_hours']) else 0,
                        "seminar": int(row['seminar_hours']) if not pd.isna(row['seminar_hours']) else 0,
                        "independent": int(row['independent_hours']) if not pd.isna(row['independent_hours']) else 0
                    },
                    "credits": {
                        sem: parse_credit_value(row[f'sem{sem}'])
                        for sem in range(1, 9)
                    },
                    "total_credits": int(row['total_credits']) if not pd.isna(row['total_credits']) else 0
                }
                
            except (ValueError, TypeError):
                pass
        
        # Add course option to current slot
        if current_slot_num is not None and not pd.isna(row['course_code']) and not pd.isna(row['course_title']):
            slot_options.append({
                "course_code": row['course_code'],
                "course_title": row['course_title']
            })
    
    # Add the final slot
    if current_slot_num is not None and slot_options:
        slots.append({
            "slot_number": current_slot_num,
            "course_options": slot_options,
            "total_hours": slot_metadata.get("total_hours", 0),
            "hours": slot_metadata.get("hours", {}),
            "credits": slot_metadata.get("credits", {}),
            "total_credits": slot_metadata.get("total_credits", 0)
        })
    
    return slots

def main():
    excel_path = "Template.xlsx"
    
    mandatory_courses = extract_mandatory_courses(excel_path)
    selective_slots = extract_selective_courses(excel_path)
   
    curriculum = {
        "mandatory_courses": mandatory_courses,
        "selective_courses": selective_slots
    }
    
    with open("curriculum.json", "w", encoding="utf-8") as f:
        json.dump(curriculum, f, ensure_ascii=False, indent=2)
   
    print(f"Successfully extracted curriculum data to curriculum.json")

if __name__ == "__main__":
    main()