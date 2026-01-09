"""
Main Data Collection Orchestrator
Menu-driven interface for collecting, curating, and managing medicine data.
"""

import os
import json
import shutil
from datetime import datetime
from fda_api_fetcher import FDAMedicineFetcher
from manual_curator import ManualCurator
from data_enricher import DataEnricher
from data_validator import DataValidator
from config import MEDICINES_DB_PATH, BACKUP_DIR, DEFAULT_FETCH_LIMIT, MIN_FETCH_LIMIT, MAX_FETCH_LIMIT


def create_backup():
    """Create backup of current database."""
    if not os.path.exists(MEDICINES_DB_PATH):
        return False
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"medicines_backup_{timestamp}.json")
    
    try:
        shutil.copy2(MEDICINES_DB_PATH, backup_path)
        print(f"✓ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ Backup failed: {e}")
        return False


def fetch_from_api():
    """Fetch medicines from OpenFDA API."""
    print("\n" + "=" * 70)
    print("FETCH MEDICINES FROM OPENFDA API")
    print("=" * 70)
    
    # Get fetch limit
    while True:
        try:
            limit_input = input(f"\nNumber of medicines to fetch ({MIN_FETCH_LIMIT}-{MAX_FETCH_LIMIT}, default: {DEFAULT_FETCH_LIMIT}): ").strip()
            limit = int(limit_input) if limit_input else DEFAULT_FETCH_LIMIT
            
            if MIN_FETCH_LIMIT <= limit <= MAX_FETCH_LIMIT:
                break
            else:
                print(f"Please enter a number between {MIN_FETCH_LIMIT} and {MAX_FETCH_LIMIT}")
        except ValueError:
            print("Please enter a valid number")
    
    # Create backup
    print("\nCreating backup...")
    create_backup()
    
    # Fetch medicines
    fetcher = FDAMedicineFetcher()
    print(f"\nFetching {limit} medicines from OpenFDA API...")
    print("This may take several minutes. Please wait...\n")
    
    medicines = fetcher.fetch_popular_medicines(limit=limit)
    
    if not medicines:
        print("\n✗ No medicines were fetched. Please try again.")
        return
    
    # Load existing database
    try:
        with open(MEDICINES_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing_medicines = data.get('medicines', [])
    except FileNotFoundError:
        existing_medicines = []
    
    # Merge with existing (avoid duplicates)
    existing_names = {m.get('name', '').lower() for m in existing_medicines}
    new_medicines = [m for m in medicines if m.get('name', '').lower() not in existing_names]
    
    # Combine
    all_medicines = existing_medicines + new_medicines
    
    # Save
    data = {"medicines": all_medicines}
    with open(MEDICINES_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Successfully added {len(new_medicines)} new medicines")
    print(f"  Total medicines in database: {len(all_medicines)}")
    print(f"  (Skipped {len(medicines) - len(new_medicines)} duplicates)")


def add_manually():
    """Add medicine manually."""
    curator = ManualCurator()
    curator.add_medicine_interactive()


def enrich_data():
    """Enrich existing data."""
    print("\n" + "=" * 70)
    print("ENRICH EXISTING DATA")
    print("=" * 70)
    
    # Create backup
    print("\nCreating backup...")
    create_backup()
    
    enricher = DataEnricher()
    enricher.enrich_medicines(verbose=True)


def validate_database():
    """Validate database quality."""
    validator = DataValidator()
    validator.print_quality_report()


def view_statistics():
    """View database statistics."""
    curator = ManualCurator()
    stats = curator.get_statistics()
    
    print("\n" + "=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)
    print(f"\nTotal Medicines: {stats['total_medicines']}")
    print(f"Total Uses: {stats['total_uses']}")
    print(f"Total Components: {stats['total_components']}")
    print(f"Average Uses per Medicine: {stats['avg_uses_per_medicine']:.1f}")
    print(f"Average Components per Medicine: {stats['avg_components_per_medicine']:.1f}")
    
    print("\nCategories:")
    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {category}: {count}")
    
    print("\n" + "=" * 70)


def export_backup():
    """Export/backup database."""
    if create_backup():
        print("\n✓ Backup completed successfully")
    else:
        print("\n✗ Backup failed")


def main_menu():
    """Display main menu and handle user input."""
    while True:
        print("\n" + "=" * 70)
        print("MEDICINE DATA COLLECTION SYSTEM")
        print("=" * 70)
        print("\n1. Fetch medicines from OpenFDA API (100-500)")
        print("2. Add medicine manually")
        print("3. Enrich existing data")
        print("4. Validate database")
        print("5. View statistics")
        print("6. Export/backup database")
        print("7. Exit")
        
        choice = input("\nSelect an option (1-7): ").strip()
        
        if choice == '1':
            fetch_from_api()
        elif choice == '2':
            add_manually()
        elif choice == '3':
            enrich_data()
        elif choice == '4':
            validate_database()
        elif choice == '5':
            view_statistics()
        elif choice == '6':
            export_backup()
        elif choice == '7':
            print("\nThank you for using Medicine Data Collection System!")
            break
        else:
            print("\nInvalid option. Please select 1-7.")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
