"""
OpenFDA API Integration for Medicine Data Collection
Fetches medicine data from FDA Drug Label API and transforms it to our format.
"""

import json
import time
import requests
from typing import List, Dict, Optional
from config import (
    FDA_API_BASE_URL,
    FDA_API_TIMEOUT,
    FDA_API_RATE_LIMIT_DELAY,
    CATEGORY_MAPPINGS
)


class FDAMedicineFetcher:
    """Fetches medicine data from OpenFDA API."""
    
    def __init__(self):
        """Initialize the FDA API fetcher."""
        self.base_url = FDA_API_BASE_URL
        self.timeout = FDA_API_TIMEOUT
        self.rate_limit_delay = FDA_API_RATE_LIMIT_DELAY
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """
        Make API request with error handling.
        
        Args:
            params: Query parameters for API request
            
        Returns:
            JSON response or None if error
        """
        try:
            time.sleep(self.rate_limit_delay)  # Respect rate limits
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"Error: API request timed out")
            return None
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"Error: Rate limit exceeded. Waiting...")
                time.sleep(5)
                return None
            print(f"Error: HTTP {response.status_code} - {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed - {e}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON response")
            return None
    
    def fetch_medicine_by_name(self, name: str) -> Optional[Dict]:
        """
        Fetch medicine data by brand or generic name.
        
        Args:
            name: Medicine name to search for
            
        Returns:
            Transformed medicine data or None
        """
        # Try brand name first
        params = {
            "search": f"openfda.brand_name:{name}",
            "limit": 1
        }
        response = self._make_request(params)
        
        if response and response.get("results"):
            return self._parse_fda_response(response["results"][0])
        
        # Try generic name
        params = {
            "search": f"openfda.generic_name:{name}",
            "limit": 1
        }
        response = self._make_request(params)
        
        if response and response.get("results"):
            return self._parse_fda_response(response["results"][0])
        
        return None
    
    def fetch_medicines_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        Fetch medicines by therapeutic category.
        
        Args:
            category: Therapeutic category
            limit: Maximum number of results
            
        Returns:
            List of transformed medicine data
        """
        # Search by product type or indication
        params = {
            "search": f"openfda.product_type:{category}",
            "limit": limit
        }
        response = self._make_request(params)
        
        if response and response.get("results"):
            medicines = []
            for result in response["results"]:
                medicine = self._parse_fda_response(result)
                if medicine:
                    medicines.append(medicine)
            return medicines
        
        return []
    
    def fetch_popular_medicines(self, limit: int = 200) -> List[Dict]:
        """
        Fetch popular/common medicines.
        
        Args:
            limit: Maximum number of medicines to fetch
            
        Returns:
            List of transformed medicine data
        """
        # Common medicine names to search
        common_medicines = [
            "aspirin", "ibuprofen", "acetaminophen", "paracetamol",
            "amoxicillin", "azithromycin", "penicillin", "cephalexin",
            "metformin", "insulin", "atorvastatin", "simvastatin",
            "lisinopril", "amlodipine", "losartan", "metoprolol",
            "omeprazole", "pantoprazole", "ranitidine", "famotidine",
            "loratadine", "cetirizine", "diphenhydramine", "fexofenadine",
            "sertraline", "fluoxetine", "citalopram", "escitalopram",
            "albuterol", "salbutamol", "fluticasone", "budesonide",
            "levothyroxine", "synthroid", "prednisone", "hydrocortisone"
        ]
        
        medicines = []
        for med_name in common_medicines[:limit]:
            medicine = self.fetch_medicine_by_name(med_name)
            if medicine:
                medicines.append(medicine)
                print(f"✓ Fetched: {medicine['name']}")
            else:
                print(f"✗ Not found: {med_name}")
        
        return medicines
    
    def _parse_fda_response(self, fda_data: Dict) -> Optional[Dict]:
        """
        Parse FDA API response and extract relevant fields.
        
        Args:
            fda_data: Raw FDA API response data
            
        Returns:
            Transformed medicine dictionary or None
        """
        try:
            # Extract name (prefer brand, fallback to generic)
            openfda = fda_data.get("openfda", {})
            brand_names = openfda.get("brand_name", [])
            generic_names = openfda.get("generic_name", [])
            
            name = None
            if brand_names:
                name = brand_names[0]
            elif generic_names:
                name = generic_names[0]
            
            if not name:
                return None
            
            # Extract uses/indications
            uses = []
            indications = fda_data.get("indications_and_usage", [])
            if indications:
                # Split by common delimiters and clean
                for indication in indications:
                    # Split by periods, semicolons, commas
                    parts = indication.replace(".", ",").replace(";", ",").split(",")
                    for part in parts:
                        part = part.strip().lower()
                        if part and len(part) > 3:  # Filter out very short strings
                            uses.append(part)
            
            # Extract active ingredients
            components = []
            active_ingredient = fda_data.get("active_ingredient", [])
            if active_ingredient:
                components = [ing.lower().strip() for ing in active_ingredient]
            
            # If no active ingredient found, try openfda
            if not components:
                substances = openfda.get("substance_name", [])
                if substances:
                    components = [sub.lower().strip() for sub in substances]
            
            # Determine category from uses
            category = self._infer_category(uses)
            
            # Get description
            description = fda_data.get("description", [])
            description_text = description[0] if description else ""
            
            # Build medicine dictionary
            medicine = {
                "name": name.title(),  # Capitalize properly
                "uses": list(set(uses))[:10] if uses else [],  # Remove duplicates, limit to 10
                "components": list(set(components)) if components else [],
                "category": category,
                "description": description_text[:200] if description_text else ""  # Limit length
            }
            
            # Validate required fields
            if not medicine["uses"] and not medicine["components"]:
                return None
            
            return medicine
            
        except Exception as e:
            print(f"Error parsing FDA response: {e}")
            return None
    
    def _infer_category(self, uses: List[str]) -> str:
        """
        Infer therapeutic category from uses.
        
        Args:
            uses: List of use cases/indications
            
        Returns:
            Category name or "Unknown"
        """
        from config import CATEGORY_MAPPINGS
        
        use_text = " ".join(uses).lower()
        
        # Check each mapping
        for use_term, category in CATEGORY_MAPPINGS.items():
            if use_term.lower() in use_text:
                return category
        
        return "Unknown"
    
    def batch_fetch(self, medicine_list: List[str]) -> List[Dict]:
        """
        Fetch multiple medicines in batch.
        
        Args:
            medicine_list: List of medicine names to fetch
            
        Returns:
            List of successfully fetched medicines
        """
        medicines = []
        total = len(medicine_list)
        
        print(f"Fetching {total} medicines from OpenFDA API...")
        
        for idx, med_name in enumerate(medicine_list, 1):
            print(f"[{idx}/{total}] Fetching: {med_name}...", end=" ")
            medicine = self.fetch_medicine_by_name(med_name)
            if medicine:
                medicines.append(medicine)
                print(f"✓ Success")
            else:
                print(f"✗ Not found")
        
        print(f"\nSuccessfully fetched {len(medicines)} out of {total} medicines.")
        return medicines
    
    def transform_to_our_format(self, fda_data: Dict) -> Dict:
        """
        Transform FDA data to our JSON format (alias for _parse_fda_response).
        
        Args:
            fda_data: Raw FDA API response
            
        Returns:
            Transformed medicine dictionary
        """
        return self._parse_fda_response(fda_data)
