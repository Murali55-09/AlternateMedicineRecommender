"""
Data Enrichment Tool
Fills missing fields, standardizes terminology, and improves data quality.
"""

import json
from typing import Dict, List
from config import (
    MEDICINES_DB_PATH,
    CATEGORY_MAPPINGS,
    TERM_STANDARDIZATION,
    REQUIRED_FIELDS
)


class DataEnricher:
    """Enriches and standardizes medicine data."""
    
    def __init__(self, database_path: str = MEDICINES_DB_PATH):
        """
        Initialize the data enricher.
        
        Args:
            database_path: Path to medicines.json file
        """
        self.database_path = database_path
        self.medicines = []
        self._load_database()
    
    def _load_database(self):
        """Load medicines from database."""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.medicines = data.get('medicines', [])
        except FileNotFoundError:
            print(f"Error: Database file '{self.database_path}' not found.")
            self.medicines = []
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{self.database_path}'.")
            self.medicines = []
    
    def _save_database(self):
        """Save medicines to database."""
        data = {"medicines": self.medicines}
        with open(self.database_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def standardize_uses(self) -> int:
        """
        Standardize use case terminology.
        
        Returns:
            Number of terms standardized
        """
        standardized_count = 0
        
        for medicine in self.medicines:
            uses = medicine.get('uses', [])
            standardized_uses = []
            
            for use in uses:
                use_lower = use.lower().strip()
                # Check if term needs standardization
                if use_lower in TERM_STANDARDIZATION:
                    standardized_uses.append(TERM_STANDARDIZATION[use_lower])
                    standardized_count += 1
                else:
                    standardized_uses.append(use)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_uses = []
            for use in standardized_uses:
                use_lower = use.lower()
                if use_lower not in seen:
                    seen.add(use_lower)
                    unique_uses.append(use)
            
            medicine['uses'] = unique_uses
        
        if standardized_count > 0:
            self._save_database()
        
        return standardized_count
    
    def add_missing_categories(self) -> int:
        """
        Add category if missing, based on uses.
        
        Returns:
            Number of categories added
        """
        added_count = 0
        
        for medicine in self.medicines:
            # Skip if category already exists
            if medicine.get('category') and medicine['category'] != 'Unknown':
                continue
            
            uses = medicine.get('uses', [])
            if not uses:
                continue
            
            # Infer category from uses
            category = self._infer_category(uses)
            if category and category != 'Unknown':
                medicine['category'] = category
                added_count += 1
        
        if added_count > 0:
            self._save_database()
        
        return added_count
    
    def _infer_category(self, uses: List[str]) -> str:
        """
        Infer category from uses.
        
        Args:
            uses: List of use cases
            
        Returns:
            Category name or "Unknown"
        """
        use_text = " ".join(uses).lower()
        
        for use_term, category in CATEGORY_MAPPINGS.items():
            if use_term.lower() in use_text:
                return category
        
        return "Unknown"
    
    def merge_duplicates(self) -> int:
        """
        Merge duplicate medicine entries.
        
        Returns:
            Number of duplicates merged
        """
        merged_count = 0
        seen_names = {}
        unique_medicines = []
        
        for medicine in self.medicines:
            name_lower = medicine.get('name', '').lower().strip()
            
            if name_lower in seen_names:
                # Merge with existing entry
                existing = seen_names[name_lower]
                
                # Merge uses
                existing_uses = set(existing.get('uses', []))
                new_uses = set(medicine.get('uses', []))
                existing['uses'] = list(existing_uses.union(new_uses))
                
                # Merge components
                existing_components = set(existing.get('components', []))
                new_components = set(medicine.get('components', []))
                existing['components'] = list(existing_components.union(new_components))
                
                # Use non-empty category
                if not existing.get('category') or existing['category'] == 'Unknown':
                    if medicine.get('category') and medicine['category'] != 'Unknown':
                        existing['category'] = medicine['category']
                
                # Use non-empty description
                if not existing.get('description') and medicine.get('description'):
                    existing['description'] = medicine['description']
                
                merged_count += 1
            else:
                seen_names[name_lower] = medicine
                unique_medicines.append(medicine)
        
        if merged_count > 0:
            self.medicines = unique_medicines
            self._save_database()
        
        return merged_count
    
    def fill_missing_fields(self) -> Dict[str, int]:
        """
        Fill missing optional fields with defaults.
        
        Returns:
            Dictionary with counts of fields added
        """
        added = {
            'categories': 0,
            'descriptions': 0
        }
        
        for medicine in self.medicines:
            # Add category if missing
            if not medicine.get('category'):
                uses = medicine.get('uses', [])
                category = self._infer_category(uses)
                medicine['category'] = category
                added['categories'] += 1
            
            # Add empty description if completely missing (optional, so we skip)
            # if 'description' not in medicine:
            #     medicine['description'] = ""
            #     added['descriptions'] += 1
        
        if added['categories'] > 0 or added['descriptions'] > 0:
            self._save_database()
        
        return added
    
    def validate_completeness(self) -> Dict:
        """
        Check data completeness and return statistics.
        
        Returns:
            Dictionary with completeness statistics
        """
        stats = {
            'total': len(self.medicines),
            'complete': 0,
            'missing_name': 0,
            'missing_uses': 0,
            'missing_components': 0,
            'missing_category': 0,
            'missing_both_uses_and_components': 0
        }
        
        for medicine in self.medicines:
            has_name = bool(medicine.get('name'))
            has_uses = bool(medicine.get('uses'))
            has_components = bool(medicine.get('components'))
            has_category = bool(medicine.get('category'))
            
            if not has_name:
                stats['missing_name'] += 1
            if not has_uses:
                stats['missing_uses'] += 1
            if not has_components:
                stats['missing_components'] += 1
            if not has_category:
                stats['missing_category'] += 1
            if not has_uses and not has_components:
                stats['missing_both_uses_and_components'] += 1
            
            if has_name and (has_uses or has_components):
                stats['complete'] += 1
        
        return stats
    
    def enrich_medicines(self, verbose: bool = True) -> Dict:
        """
        Run all enrichment processes.
        
        Args:
            verbose: Print progress messages
            
        Returns:
            Dictionary with enrichment statistics
        """
        if verbose:
            print("Starting data enrichment...")
        
        results = {}
        
        # Standardize terminology
        if verbose:
            print("  Standardizing terminology...")
        results['standardized_uses'] = self.standardize_uses()
        
        # Add missing categories
        if verbose:
            print("  Adding missing categories...")
        results['added_categories'] = self.add_missing_categories()
        
        # Merge duplicates
        if verbose:
            print("  Merging duplicates...")
        results['merged_duplicates'] = self.merge_duplicates()
        
        # Fill missing fields
        if verbose:
            print("  Filling missing fields...")
        results['filled_fields'] = self.fill_missing_fields()
        
        # Validate completeness
        if verbose:
            print("  Validating completeness...")
        results['completeness'] = self.validate_completeness()
        
        if verbose:
            print("\nEnrichment complete!")
            print(f"  - Standardized {results['standardized_uses']} use terms")
            print(f"  - Added {results['added_categories']} categories")
            print(f"  - Merged {results['merged_duplicates']} duplicates")
            print(f"  - Completeness: {results['completeness']['complete']}/{results['completeness']['total']} medicines")
        
        return results
