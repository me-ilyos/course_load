import re
from typing import Optional
from openpyxl.worksheet.worksheet import Worksheet

def parse_curriculum_metadata(sheet: Worksheet) -> dict:
    data = {
        'major_type': None,
        'major_duration': None,  # integer (years)
        'education_type': None,
        'major_code': None,
        'major_title': None,
    }
    ta_lim_yonalishi_row = None
    for row_idx, row in enumerate(sheet.iter_rows(min_row=1, max_row=30, values_only=True), 1):
        for col_idx, cell in enumerate(row):
            if cell and isinstance(cell, str):
                normalized = (
                    cell.replace("‘", "'")
                        .replace("’", "'")
                        .replace("ʼ", "'")
                        .replace("`", "'")
                        .replace("–", "-")
                        .replace("—", "-")
                        .replace("−", "-")
                )
                text = normalized.lower()
                if 'akademik daraja' in text and data['major_type'] is None:
                    parts = re.split(r'-|:', normalized)
                    if len(parts) > 1:
                        data['major_type'] = parts[1].strip()
                if "o'qish muddati" in text and data['major_duration'] is None:
                    parts = re.split(r'-|:', normalized)
                    if len(parts) > 1:
                        # Extract integer from e.g. '4 yil'
                        match = re.search(r'(\d+)', parts[1])
                        data['major_duration'] = int(match.group(1)) if match else None
                if "ta'lim shakli" in text and data['education_type'] is None:
                    parts = re.split(r'-|:', normalized)
                    if len(parts) > 1:
                        data['education_type'] = parts[1].strip()
                if "ta'lim yo'nalishi" in text and ta_lim_yonalishi_row is None:
                    ta_lim_yonalishi_row = row_idx
    if ta_lim_yonalishi_row:
        next_row = list(sheet.iter_rows(min_row=ta_lim_yonalishi_row+1, max_row=ta_lim_yonalishi_row+1, values_only=True))
        if next_row:
            for cell in next_row[0]:
                if cell and isinstance(cell, str):
                    normalized_cell = (
                        cell.replace("–", "-")
                            .replace("—", "-")
                            .replace("−", "-")
                            .replace("  ", " ")
                            .strip()
                    )
                    # Match code-title pattern
                    m = re.match(r"^(\d{5,})\s*-\s*(.+)$", normalized_cell)
                    if m:
                        data['major_code'] = m.group(1)
                        data['major_title'] = m.group(2).strip()
                        break
    return data 