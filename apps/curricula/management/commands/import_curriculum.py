import os
from django.core.management.base import BaseCommand, CommandError
from apps.curricula.parsing import extract_mandatory_courses, save_to_json


class Command(BaseCommand):
    """
    Django management command to import curriculum data from Excel files.
    
    Usage:
        python manage.py import_curriculum /path/to/curriculum.xlsx
    """
    help = 'Imports mandatory courses from a curriculum Excel file'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument('excel_file', type=str, help='Path to the curriculum Excel file')
        parser.add_argument(
            '--output', 
            type=str, 
            help='Path to the output JSON file (default: data/mandatory_courses.json)'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        excel_file = options['excel_file']
        output_file = options.get('output')
        
        # Validate excel file exists
        if not os.path.exists(excel_file):
            raise CommandError(f'Excel file does not exist: {excel_file}')
            
        # Set default output file if not specified
        if not output_file:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            output_file = os.path.join(data_dir, 'mandatory_courses.json')
            
        try:
            # Extract mandatory courses
            self.stdout.write(self.style.SUCCESS(f'Extracting mandatory courses from {excel_file}...'))
            mandatory_courses = extract_mandatory_courses(excel_file)
            
            # Save to JSON
            save_to_json(mandatory_courses, output_file)
            self.stdout.write(self.style.SUCCESS(f'Successfully extracted {len(mandatory_courses)} mandatory courses'))
            self.stdout.write(self.style.SUCCESS(f'Saved to {output_file}'))
            
        except Exception as e:
            raise CommandError(f'Failed to import curriculum: {str(e)}') 