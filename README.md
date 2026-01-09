# ML-Based Medicine Recommendation System

A Python application that uses machine learning (content-based filtering) to recommend similar medicines based on use cases and active ingredients/components. The system uses TF-IDF vectorization and cosine similarity to find medicines with similar therapeutic profiles.

## Features

### Recommendation System
- **ML-Based Recommendations**: Uses TF-IDF vectorization and cosine similarity for intelligent medicine matching
- **Multi-Factor Analysis**: Considers both use cases (diseases treated) and active ingredients/components
- **Ranked Results**: Provides similarity scores (0.0 to 1.0) for each recommendation
- **Detailed Comparison**: Shows shared uses and components between medicines
- **Case-Insensitive Search**: Flexible medicine name matching

### Data Collection System
- **OpenFDA API Integration**: Automatically fetch medicine data from FDA Drug Label API
- **Manual Curation Tool**: Interactive interface for manually adding medicines
- **Data Enrichment**: Automatically standardize terminology, add missing categories, merge duplicates
- **Data Validation**: Comprehensive quality checks and validation reports
- **Backup System**: Automatic backups before major operations

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   - Python 3.7 or higher
   - scikit-learn >= 1.0.0
   - numpy >= 1.21.0
   - requests >= 2.28.0
   - python-dotenv >= 0.19.0

## Usage

### Using the Recommendation System

1. **Run the recommendation application:**
   ```bash
   python main.py
   ```

2. **Enter a medicine name** when prompted (e.g., "Paracetamol", "Ibuprofen")

3. **Specify number of recommendations** (default: 5)

4. **View results** showing:
   - Original medicine details
   - Top similar medicines with similarity scores
   - Shared uses and components
   - Detailed comparison

5. **Type 'quit'** to exit

### Using the Data Collection System

1. **Run the data collection tool:**
   ```bash
   python collect_medicines.py
   ```

2. **Choose from menu options:**
   - **Option 1**: Fetch 100-500 medicines from OpenFDA API (automated)
   - **Option 2**: Add medicine manually (interactive)
   - **Option 3**: Enrich existing data (standardize, add categories, merge duplicates)
   - **Option 4**: Validate database quality
   - **Option 5**: View database statistics
   - **Option 6**: Export/backup database
   - **Option 7**: Exit

3. **Example workflow:**
   ```bash
   # First, fetch medicines from API
   python collect_medicines.py
   # Select option 1, enter 200 medicines
   
   # Then enrich the data
   # Select option 3
   
   # Validate quality
   # Select option 4
   ```

## Example

```
Enter medicine name (or 'quit' to exit): Paracetamol
Number of recommendations (default: 5): 3

======================================================================
ORIGINAL MEDICINE: Paracetamol
======================================================================
Category: Analgesic
Uses: fever, pain, headache, arthritis
Components: acetaminophen
Description: Common pain reliever and fever reducer

======================================================================
RECOMMENDED SIMILAR MEDICINES (Top 3)
======================================================================

1. Ibuprofen (Similarity: 0.632)
   Category: NSAID
   Uses: pain, inflammation, arthritis, fever
   Components: ibuprofen
   Shared Uses: pain, fever, arthritis
   Description: Non-steroidal anti-inflammatory drug
...
```

## How It Works

1. **Feature Extraction**: Combines medicine uses and components into text features
2. **Vectorization**: Uses TF-IDF to convert text to numerical vectors
3. **Similarity Calculation**: Computes cosine similarity between medicine vectors
4. **Ranking**: Returns top N medicines sorted by similarity score

## Data Structure

The `medicines.json` file contains medicine data with the following structure:

```json
{
  "medicines": [
    {
      "name": "Medicine Name",
      "uses": ["disease1", "disease2"],
      "components": ["ingredient1", "ingredient2"],
      "category": "therapeutic_category",
      "description": "optional description"
    }
  ]
}
```

## File Structure

```
projcursor/
├── medicine_recommender.py    # ML-based recommendation engine
├── main.py                    # Recommendation system entry point
├── collect_medicines.py       # Data collection system orchestrator
├── fda_api_fetcher.py         # OpenFDA API integration
├── manual_curator.py          # Manual data entry tool
├── data_enricher.py           # Data enrichment utilities
├── data_validator.py          # Data validation tools
├── config.py                  # Configuration settings
├── medicines.json             # Medicine database
├── requirements.txt           # Python dependencies
├── backups/                   # Database backups (auto-created)
└── README.md                  # This file
```

## Adding New Medicines

### Method 1: Using Data Collection System (Recommended)
```bash
python collect_medicines.py
# Select option 1 to fetch from API, or option 2 to add manually
```

### Method 2: Manual JSON Editing
Edit `medicines.json` and add new entries following the existing structure. The model will automatically retrain when you restart the application.

### Method 3: Programmatic Addition
```python
from manual_curator import ManualCurator

curator = ManualCurator()
medicine = {
    "name": "Medicine Name",
    "uses": ["use1", "use2"],
    "components": ["component1"],
    "category": "Category"
}
curator.add_medicine_from_dict(medicine)
```

## Technical Details

- **Algorithm**: Content-Based Filtering
- **Vectorization**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Similarity Metric**: Cosine Similarity
- **Feature Engineering**: Combines uses and components with n-gram analysis (1-2 grams)

## Data Collection Features

### OpenFDA API Integration
- Fetches real medicine data from FDA Drug Label API
- Supports fetching 100-500 medicines
- Automatic rate limiting and error handling
- Transforms FDA data to our JSON format

### Manual Curation
- Interactive step-by-step data entry
- Duplicate detection and prevention
- Category auto-suggestion based on uses
- Data validation before saving

### Data Enrichment
- Standardizes terminology (e.g., "fever" vs "pyrexia")
- Adds missing categories based on uses
- Merges duplicate entries
- Fills missing optional fields

### Data Validation
- Structure validation (JSON schema)
- Required fields checking
- Duplicate detection
- Data type validation
- Completeness analysis
- Quality score calculation

## Future Enhancements

### Recommendation System
- Hybrid scoring with weighted uses vs components
- Sentence transformers for better semantic understanding
- Fuzzy matching for medicine name typos
- Category-based filtering
- Export results to file
- REST API endpoint

### Data Collection
- Multiple API sources (DrugBank, RxNorm)
- Automated scheduled updates
- Data visualization dashboard
- Export to different formats (CSV, Excel)

## License

This project is provided as-is for educational and demonstration purposes.
