import pandas as pd
import json
import os
from typing import List, Dict, Any, Optional

def extract_mandatory_courses(excel_file_path: str) -> List[Dict[str, Any]]:
    """
    Extract mandatory courses from the curriculum Excel file.
    
    Args:
        excel_file_path (str): Path to the Excel file containing curriculum data
        
    Returns:
        list: List of dictionaries containing mandatory course information
    """
    # Read the Excel file - skip header rows as they might be merged cells
    df = pd.read_excel(excel_file_path, header=None)
    
    # Initialize variables
    mandatory_courses = []
    is_mandatory_section = False
    in_table = False
    column_indices = {}
    
    # Iterate through rows to find mandatory courses
    for index, row in df.iterrows():
        row_str = ' '.join([str(val) for val in row.values if not pd.isna(val)])
        
        # Check if this row marks the beginning of the mandatory section
        if 'Majburiy fanlar' in row_str:
            is_mandatory_section = True
            in_table = False
            continue
            
        # Check if we've reached the elective courses section
        if 'Tanlov fanlari' in row_str:
            is_mandatory_section = False
            continue
        
        # Identify the header row to map column indices
        if is_mandatory_section and not in_table and any(x in row_str for x in ['Fanning kodi', 'T/r', 'Fanlarning nomi']):
            # Map column headers to their indices
            for i, cell in enumerate(row):
                cell_str = str(cell).strip() if not pd.isna(cell) else ""
                if 'T/r' in cell_str:
                    column_indices['row_num'] = i
                elif 'Fanning kodi' in cell_str:
                    column_indices['course_code'] = i
                elif 'Fanlarning nomi' in cell_str or 'nomi' in cell_str:
                    column_indices['course_title'] = i
                elif 'Hajmi' in cell_str:
                    column_indices['total_hours'] = i
                elif 'Jami' in cell_str and 'kreditlar' not in cell_str:
                    column_indices['classroom_hours'] = i
                elif "Ma'ruza" in cell_str:
                    column_indices['lecture_hours'] = i
                elif 'Amaliy' in cell_str:
                    column_indices['practice_hours'] = i
                elif 'Laboratoriya' in cell_str:
                    column_indices['laboratory_hours'] = i
                elif 'Seminar' in cell_str:
                    column_indices['seminar_hours'] = i
                elif 'Mustaqil' in cell_str:
                    column_indices['independent_hours'] = i
                elif '1-kurs' in cell_str:
                    column_indices['semester_1'] = i
                elif '2-kurs' in cell_str:
                    column_indices['semester_2'] = i
                elif '3-kurs' in cell_str:
                    column_indices['semester_3'] = i
                elif '4-kurs' in cell_str:
                    column_indices['semester_4'] = i
                elif '5' in cell_str and len(cell_str) < 3:
                    column_indices['semester_5'] = i
                elif '6' in cell_str and len(cell_str) < 3:
                    column_indices['semester_6'] = i
                elif '7' in cell_str and len(cell_str) < 3:
                    column_indices['semester_7'] = i
                elif '8' in cell_str and len(cell_str) < 3:
                    column_indices['semester_8'] = i
                elif 'Jami kreditlar' in cell_str:
                    column_indices['total_credits'] = i
            
            in_table = True
            continue
        
        # Skip rows that don't contain course data or are outside the mandatory section
        if not is_mandatory_section or not in_table or len(column_indices) == 0:
            continue
            
        # Check if this is a course row (has a row number)
        row_num_idx = column_indices.get('row_num')
        if row_num_idx is None or pd.isna(row[row_num_idx]):
            continue
            
        try:
            # Verify this is a course row by checking if row number is a digit
            if not str(row[row_num_idx]).strip().isdigit():
                continue
                
            # Extract course information using the mapped column indices
            def safe_get_value(idx_name, default=None, as_int=False):
                idx = column_indices.get(idx_name)
                if idx is None or pd.isna(row[idx]):
                    return default
                value = row[idx]
                return int(value) if as_int and not pd.isna(value) else value
            
            course_info = {
                'course_code': str(safe_get_value('course_code', '')),
                'course_title': str(safe_get_value('course_title', '')),
                'total_hours': safe_get_value('total_hours', None, as_int=True),
                'classroom_hours': safe_get_value('classroom_hours', None, as_int=True),
                'lecture_hours': safe_get_value('lecture_hours', None, as_int=True),
                'practice_hours': safe_get_value('practice_hours', None, as_int=True),
                'laboratory_hours': safe_get_value('laboratory_hours', None, as_int=True),
                'seminar_hours': safe_get_value('seminar_hours', None, as_int=True),
                'independent_hours': safe_get_value('independent_hours', None, as_int=True),
                'credits_by_semester': {
                    '1': safe_get_value('semester_1', 0, as_int=True),
                    '2': safe_get_value('semester_2', 0, as_int=True),
                    '3': safe_get_value('semester_3', 0, as_int=True),
                    '4': safe_get_value('semester_4', 0, as_int=True),
                    '5': safe_get_value('semester_5', 0, as_int=True),
                    '6': safe_get_value('semester_6', 0, as_int=True),
                    '7': safe_get_value('semester_7', 0, as_int=True),
                    '8': safe_get_value('semester_8', 0, as_int=True)
                },
                'total_credits': safe_get_value('total_credits', None, as_int=True)
            }
            
            # Skip rows with empty course code or title
            if not course_info['course_code'].strip() or not course_info['course_title'].strip():
                continue
                
            mandatory_courses.append(course_info)
        except Exception as e:
            print(f"Error processing row {index}: {e}")
    
    return mandatory_courses

def save_to_json(courses: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save course information to a JSON file.
    
    Args:
        courses (list): List of course information dictionaries
        output_file (str): Path to the output JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)
    print(f"Saved {len(courses)} mandatory courses to {output_file}")

def main() -> None:
    """Main function to extract and save mandatory courses."""
    # Define file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(os.path.dirname(base_dir)), 'data')
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Define input and output file paths
    excel_file = input("Enter the path to the curriculum Excel file: ")
    output_file = os.path.join(data_dir, 'mandatory_courses.json')
    
    # Extract and save mandatory courses
    mandatory_courses = extract_mandatory_courses(excel_file)
    save_to_json(mandatory_courses, output_file)
    
    print(f"Extracted {len(mandatory_courses)} mandatory courses from the curriculum.")

if __name__ == "__main__":
    main()
