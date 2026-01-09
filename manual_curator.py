"""
Manual Curation Tool for Medicine Data Entry
Interactive CLI tool for manually adding medicines to the database.
"""

import json
from typing import Dict, List, Optional
from config import MEDICINES_DB_PATH, CATEGORY_MAPPINGS, REQUIRED_FIELDS


class ManualCurator:
    """Interactive tool for manual medicine data entry."""
    
    def __init__(self, database_path: str = MEDICINES_DB_PATH):
        """
        Initialize the manual curator.
        
        Args:
            database_path: Path to medicines.json file
        """
        self.database_path = database_path
        self.medicines = []
        self._load_database()
    
    def _load_database(self):
        """Load existing medicines from database."""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.medicines = data.get('medicines', [])
        except FileNotFoundError:
            self.medicines = []
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {self.database_path}. Starting fresh.")
            self.medicines = []
    
    def _save_database(self):
        """Save medicines to database file."""
        data = {"medicines": self.medicines}
        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def check_duplicate(self, name: str) -> bool:
        """
        Check if medicine with given name already exists.
        
        Args:
            name: Medicine name to check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        name_lower = name.lower().strip()
        for med in self.medicines:
            if med.get('name', '').lower() == name_lower:
                return True
        return False
    
    def suggest_category(self, uses: List[str]) -> Optional[str]:
        """
        Suggest category based on uses.
        
        Args:
            uses: List of use cases
            
        Returns:
            Suggested category or None
        """
        use_text = " ".join(uses).lower()
        
        for use_term, category in CATEGORY_MAPPINGS.items():
            if use_term.lower() in use_text:
                return category
        
        return None
    
    def validate_medicine_data(self, medicine: Dict) -> tuple[bool, str]:
        """
        Validate medicine data structure.
        
        Args:
            medicine: Medicine dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in medicine:
                return False, f"Missing required field: {field}"
            
            if not medicine[field]:
                return False, f"Required field '{field}' is empty"
        
        # Validate types
        if not isinstance(medicine['name'], str):
            return False, "Field 'name' must be a string"
        
        if not isinstance(medicine['uses'], list):
            return False, "Field 'uses' must be a list"
        
        if not isinstance(medicine['components'], list):
            return False, "Field 'components' must be a list"
        
        # Check if uses and components are not empty
        if not medicine['uses'] and not medicine['components']:
            return False, "At least one of 'uses' or 'components' must have values"
        
        return True, ""
    
    def add_medicine_interactive(self) -> bool:
        """
        Interactive step-by-step guide to add a medicine.
        
        Returns:
            True if medicine was added successfully, False otherwise
        """
        print("\n" + "=" * 70)
        print("MANUAL MEDICINE ENTRY")
        print("=" * 70)
        
        medicine = {}
        
        # Get medicine name
        while True:
            name = input("\nMedicine Name: ").strip()
            if not name:
                print("Error: Medicine name cannot be empty.")
                continue
            
            if self.check_duplicate(name):
                overwrite = input(f"Medicine '{name}' already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite == 'y':
                    # Remove existing entry
                    self.medicines = [m for m in self.medicines if m.get('name', '').lower() != name.lower()]
                    break
                else:
                    print("Cancelled.")
                    return False
            break
        
        medicine['name'] = name
        
        # Get uses
        print("\nEnter uses/indications (conditions this medicine treats).")
        print("Press Enter after each use, or press Enter twice to finish:")
        uses = []
        while True:
            use = input(f"Use {len(uses) + 1}: ").strip().lower()
            if not use:
                if uses:
                    break
                else:
                    print("Please enter at least one use.")
                    continue
            uses.append(use)
        
        medicine['uses'] = uses
        
        # Get components
        print("\nEnter active ingredients/components.")
        print("Press Enter after each component, or press Enter twice to finish:")
        components = []
        while True:
            component = input(f"Component {len(components) + 1}: ").strip().lower()
            if not component:
                if components:
                    break
                else:
                    print("Please enter at least one component.")
                    continue
            components.append(component)
        
        medicine['components'] = components
        
        # Suggest category
        suggested_category = self.suggest_category(uses)
        if suggested_category:
            print(f"\nSuggested category: {suggested_category}")
            category = input("Category (press Enter to use suggestion): ").strip()
            medicine['category'] = category if category else suggested_category
        else:
            category = input("\nCategory: ").strip()
            medicine['category'] = category if category else "Unknown"
        
        # Get description (optional)
        description = input("\nDescription (optional, press Enter to skip): ").strip()
        if description:
            medicine['description'] = description
        
        # Preview
        print("\n" + "=" * 70)
        print("PREVIEW:")
        print("=" * 70)
        print(f"Name: {medicine['name']}")
        print(f"Uses: {', '.join(medicine['uses'])}")
        print(f"Components: {', '.join(medicine['components'])}")
        print(f"Category: {medicine.get('category', 'N/A')}")
        if medicine.get('description'):
            print(f"Description: {medicine['description']}")
        
        # Confirm
        confirm = input("\nAdd this medicine? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return False
        
        # Validate
        is_valid, error = self.validate_medicine_data(medicine)
        if not is_valid:
            print(f"Error: {error}")
            return False
        
        # Add to database
        self.medicines.append(medicine)
        self._save_database()
        
        print(f"\n✓ Successfully added '{medicine['name']}' to database!")
        print(f"Total medicines in database: {len(self.medicines)}")
        
        return True
    
    def add_medicine_from_dict(self, medicine: Dict) -> tuple[bool, str]:
        """
        Programmatically add medicine from dictionary.
        
        Args:
            medicine: Medicine dictionary with required fields
            
        Returns:
            Tuple of (success, message)
        """
        # Check duplicate
        if self.check_duplicate(medicine.get('name', '')):
            return False, f"Medicine '{medicine.get('name')}' already exists"
        
        # Validate
        is_valid, error = self.validate_medicine_data(medicine)
        if not is_valid:
            return False, error
        
        # Add category if missing
        if 'category' not in medicine or not medicine['category']:
            suggested = self.suggest_category(medicine.get('uses', []))
            medicine['category'] = suggested if suggested else "Unknown"
        
        # Add to database
        self.medicines.append(medicine)
        self._save_database()
        
        return True, f"Successfully added '{medicine['name']}'"
    
    def preview_and_save(self, medicine: Dict) -> bool:
        """
        Preview medicine data and save if confirmed.
        
        Args:
            medicine: Medicine dictionary to preview
            
        Returns:
            True if saved, False otherwise
        """
        print("\n" + "=" * 70)
        print("PREVIEW:")
        print("=" * 70)
        for key, value in medicine.items():
            if isinstance(value, list):
                print(f"{key.capitalize()}: {', '.join(value)}")
            else:
                print(f"{key.capitalize()}: {value}")
        
        confirm = input("\nSave this medicine? (y/n): ").strip().lower()
        if confirm == 'y':
            return self.add_medicine_from_dict(medicine)[0]
        return False
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about current database.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.medicines)
        categories = {}
        total_uses = 0
        total_components = 0
        
        for med in self.medicines:
            category = med.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1
            total_uses += len(med.get('uses', []))
            total_components += len(med.get('components', []))
        
        return {
            'total_medicines': total,
            'categories': categories,
            'total_uses': total_uses,
            'total_components': total_components,
            'avg_uses_per_medicine': total_uses / total if total > 0 else 0,
            'avg_components_per_medicine': total_components / total if total > 0 else 0
        }
