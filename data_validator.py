"""
Data Validation Tool
Validates medicine database structure, completeness, and quality.
"""

import json
from typing import Dict, List, Tuple
from config import MEDICINES_DB_PATH, REQUIRED_FIELDS


class DataValidator:
    """Validates medicine database structure and quality."""
    
    def __init__(self, database_path: str = MEDICINES_DB_PATH):
        """
        Initialize the data validator.
        
        Args:
            database_path: Path to medicines.json file
        """
        self.database_path = database_path
        self.medicines = []
        self.errors = []
        self.warnings = []
        self._load_database()
    
    def _load_database(self):
        """Load medicines from database."""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.medicines = data.get('medicines', [])
        except FileNotFoundError:
            self.errors.append(f"Database file '{self.database_path}' not found.")
            self.medicines = []
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in '{self.database_path}': {e}")
            self.medicines = []
    
    def validate_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate JSON structure and schema.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(self.medicines, list):
            errors.append("Root 'medicines' field must be a list")
            return False, errors
        
        for idx, medicine in enumerate(self.medicines):
            if not isinstance(medicine, dict):
                errors.append(f"Medicine at index {idx} is not a dictionary")
                continue
            
            # Check required fields
            for field in REQUIRED_FIELDS:
                if field not in medicine:
                    errors.append(f"Medicine at index {idx} missing required field: {field}")
            
            # Validate field types
            if 'name' in medicine and not isinstance(medicine['name'], str):
                errors.append(f"Medicine at index {idx}: 'name' must be a string")
            
            if 'uses' in medicine and not isinstance(medicine['uses'], list):
                errors.append(f"Medicine at index {idx}: 'uses' must be a list")
            
            if 'components' in medicine and not isinstance(medicine['components'], list):
                errors.append(f"Medicine at index {idx}: 'components' must be a list")
            
            if 'category' in medicine and not isinstance(medicine.get('category'), str):
                errors.append(f"Medicine at index {idx}: 'category' must be a string")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def check_required_fields(self) -> Dict:
        """
        Check if all required fields are present and non-empty.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'total': len(self.medicines),
            'complete': 0,
            'missing_fields': {},
            'empty_fields': {}
        }
        
        for idx, medicine in enumerate(self.medicines):
            is_complete = True
            
            for field in REQUIRED_FIELDS:
                if field not in medicine:
                    if field not in results['missing_fields']:
                        results['missing_fields'][field] = []
                    results['missing_fields'][field].append(idx)
                    is_complete = False
                elif not medicine[field]:
                    if field not in results['empty_fields']:
                        results['empty_fields'][field] = []
                    results['empty_fields'][field].append(idx)
                    is_complete = False
            
            if is_complete:
                results['complete'] += 1
        
        return results
    
    def detect_duplicates(self) -> List[Dict]:
        """
        Detect duplicate medicine entries.
        
        Returns:
            List of duplicate groups
        """
        name_map = {}
        duplicates = []
        
        for idx, medicine in enumerate(self.medicines):
            name = medicine.get('name', '').lower().strip()
            if name:
                if name not in name_map:
                    name_map[name] = []
                name_map[name].append((idx, medicine))
        
        for name, entries in name_map.items():
            if len(entries) > 1:
                duplicates.append({
                    'name': name,
                    'count': len(entries),
                    'indices': [idx for idx, _ in entries]
                })
        
        return duplicates
    
    def validate_data_types(self) -> List[str]:
        """
        Validate data types of all fields.
        
        Returns:
            List of type errors
        """
        errors = []
        
        for idx, medicine in enumerate(self.medicines):
            # Check name
            if 'name' in medicine and not isinstance(medicine['name'], str):
                errors.append(f"Index {idx}: 'name' must be string, got {type(medicine['name'])}")
            
            # Check uses
            if 'uses' in medicine:
                if not isinstance(medicine['uses'], list):
                    errors.append(f"Index {idx}: 'uses' must be list, got {type(medicine['uses'])}")
                else:
                    for use_idx, use in enumerate(medicine['uses']):
                        if not isinstance(use, str):
                            errors.append(f"Index {idx}, use {use_idx}: use must be string, got {type(use)}")
            
            # Check components
            if 'components' in medicine:
                if not isinstance(medicine['components'], list):
                    errors.append(f"Index {idx}: 'components' must be list, got {type(medicine['components'])}")
                else:
                    for comp_idx, comp in enumerate(medicine['components']):
                        if not isinstance(comp, str):
                            errors.append(f"Index {idx}, component {comp_idx}: component must be string, got {type(comp)}")
            
            # Check category
            if 'category' in medicine and medicine['category'] is not None:
                if not isinstance(medicine['category'], str):
                    errors.append(f"Index {idx}: 'category' must be string, got {type(medicine['category'])}")
            
            # Check description
            if 'description' in medicine and medicine['description'] is not None:
                if not isinstance(medicine['description'], str):
                    errors.append(f"Index {idx}: 'description' must be string, got {type(medicine['description'])}")
        
        return errors
    
    def check_completeness(self) -> Dict:
        """
        Check data completeness (uses or components must exist).
        
        Returns:
            Dictionary with completeness statistics
        """
        results = {
            'total': len(self.medicines),
            'has_uses': 0,
            'has_components': 0,
            'has_both': 0,
            'has_neither': 0,
            'empty_entries': []
        }
        
        for idx, medicine in enumerate(self.medicines):
            has_uses = bool(medicine.get('uses'))
            has_components = bool(medicine.get('components'))
            
            if has_uses:
                results['has_uses'] += 1
            if has_components:
                results['has_components'] += 1
            if has_uses and has_components:
                results['has_both'] += 1
            if not has_uses and not has_components:
                results['has_neither'] += 1
                results['empty_entries'].append({
                    'index': idx,
                    'name': medicine.get('name', 'Unknown')
                })
        
        return results
    
    def generate_quality_report(self) -> Dict:
        """
        Generate comprehensive quality report.
        
        Returns:
            Dictionary with quality metrics and issues
        """
        report = {
            'total_medicines': len(self.medicines),
            'structure_valid': False,
            'structure_errors': [],
            'required_fields': {},
            'duplicates': [],
            'type_errors': [],
            'completeness': {},
            'quality_score': 0.0
        }
        
        # Validate structure
        is_valid, errors = self.validate_structure()
        report['structure_valid'] = is_valid
        report['structure_errors'] = errors
        
        # Check required fields
        report['required_fields'] = self.check_required_fields()
        
        # Detect duplicates
        report['duplicates'] = self.detect_duplicates()
        
        # Validate data types
        report['type_errors'] = self.validate_data_types()
        
        # Check completeness
        report['completeness'] = self.check_completeness()
        
        # Calculate quality score (0-100)
        total_issues = (
            len(errors) +
            sum(len(v) for v in report['required_fields'].get('missing_fields', {}).values()) +
            len(report['duplicates']) +
            len(report['type_errors']) +
            report['completeness'].get('has_neither', 0)
        )
        
        total_medicines = len(self.medicines)
        if total_medicines > 0:
            max_possible_issues = total_medicines * 5  # Rough estimate
            report['quality_score'] = max(0, 100 - (total_issues / max_possible_issues * 100))
        else:
            report['quality_score'] = 0.0
        
        return report
    
    def print_quality_report(self):
        """Print formatted quality report to console."""
        report = self.generate_quality_report()
        
        print("\n" + "=" * 70)
        print("DATA QUALITY REPORT")
        print("=" * 70)
        print(f"\nTotal Medicines: {report['total_medicines']}")
        print(f"Quality Score: {report['quality_score']:.1f}/100")
        
        # Structure validation
        print(f"\nStructure Valid: {'✓' if report['structure_valid'] else '✗'}")
        if report['structure_errors']:
            print("  Errors:")
            for error in report['structure_errors'][:5]:
                print(f"    - {error}")
            if len(report['structure_errors']) > 5:
                print(f"    ... and {len(report['structure_errors']) - 5} more")
        
        # Required fields
        req_fields = report['required_fields']
        print(f"\nRequired Fields:")
        print(f"  Complete: {req_fields.get('complete', 0)}/{req_fields.get('total', 0)}")
        if req_fields.get('missing_fields'):
            print("  Missing fields:")
            for field, indices in req_fields['missing_fields'].items():
                print(f"    - {field}: {len(indices)} medicines")
        
        # Duplicates
        if report['duplicates']:
            print(f"\nDuplicates Found: {len(report['duplicates'])}")
            for dup in report['duplicates'][:5]:
                print(f"  - '{dup['name']}': {dup['count']} entries")
        else:
            print("\nDuplicates: None ✓")
        
        # Type errors
        if report['type_errors']:
            print(f"\nType Errors: {len(report['type_errors'])}")
            for error in report['type_errors'][:5]:
                print(f"  - {error}")
        else:
            print("\nType Errors: None ✓")
        
        # Completeness
        completeness = report['completeness']
        print(f"\nCompleteness:")
        print(f"  Has uses: {completeness.get('has_uses', 0)}")
        print(f"  Has components: {completeness.get('has_components', 0)}")
        print(f"  Has both: {completeness.get('has_both', 0)}")
        print(f"  Has neither: {completeness.get('has_neither', 0)}")
        
        if completeness.get('has_neither', 0) > 0:
            print("  Empty entries:")
            for entry in completeness.get('empty_entries', [])[:5]:
                print(f"    - Index {entry['index']}: {entry['name']}")
        
        print("\n" + "=" * 70)
    
    def fix_common_issues(self) -> Dict:
        """
        Automatically fix common data issues.
        
        Returns:
            Dictionary with fixes applied
        """
        fixes = {
            'trimmed_whitespace': 0,
            'removed_empty_lists': 0,
            'converted_types': 0
        }
        
        # This would modify the data, so we'll just report what could be fixed
        # Actual fixing should be done through DataEnricher
        
        return fixes
