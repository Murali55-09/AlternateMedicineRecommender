"""
ML-Based Medicine Recommendation System
Uses TF-IDF vectorization and cosine similarity to recommend similar medicines
based on use cases and active ingredients/components.
"""

import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MedicineRecommender:
    """ML-based medicine recommendation system using content-based filtering."""
    
    def __init__(self, database_path='medicines.json'):
        """
        Initialize the medicine recommender.
        
        Args:
            database_path: Path to the JSON file containing medicine data
        """
        self.database_path = database_path
        self.medicines = []
        self.vectorizer = None
        self.feature_vectors = None
        self.medicine_index_map = {}  # Maps medicine name to index
        
    def load_database(self):
        """Load medicines from JSON database file."""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.medicines = data.get('medicines', [])
            
            # Create index map for quick lookup
            self.medicine_index_map = {
                med['name'].lower(): idx 
                for idx, med in enumerate(self.medicines)
            }
            
            print(f"Loaded {len(self.medicines)} medicines from database.")
            return True
        except FileNotFoundError:
            print(f"Error: Database file '{self.database_path}' not found.")
            return False
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in '{self.database_path}'.")
            return False
    
    def prepare_features(self, medicine):
        """
        Combine uses and components into a single feature text string.
        
        Args:
            medicine: Dictionary containing medicine data
            
        Returns:
            Combined feature string
        """
        uses = medicine.get('uses', [])
        components = medicine.get('components', [])
        
        # Combine uses and components into a single string
        feature_text = ' '.join(uses) + ' ' + ' '.join(components)
        return feature_text.strip()
    
    def build_vectorizer(self):
        """Initialize TF-IDF vectorizer."""
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer='word',
            ngram_range=(1, 2),  # Include unigrams and bigrams
            min_df=1,  # Include terms that appear in at least 1 document
            max_df=0.95  # Exclude terms that appear in more than 95% of documents
        )
    
    def train_model(self):
        """
        Fit the vectorizer on all medicine features.
        This creates the feature vectors for all medicines.
        """
        if not self.medicines:
            print("Error: No medicines loaded. Please load database first.")
            return False
        
        if self.vectorizer is None:
            self.build_vectorizer()
        
        # Prepare features for all medicines
        feature_texts = [self.prepare_features(med) for med in self.medicines]
        
        # Fit and transform to create feature vectors
        self.feature_vectors = self.vectorizer.fit_transform(feature_texts)
        
        print(f"Model trained on {len(self.medicines)} medicines.")
        print(f"Feature space: {self.feature_vectors.shape[1]} dimensions.")
        return True
    
    def find_medicine(self, name):
        """
        Search for a medicine by name (case-insensitive).
        
        Args:
            name: Medicine name to search for
            
        Returns:
            Medicine dictionary if found, None otherwise
        """
        name_lower = name.lower().strip()
        
        # Direct lookup
        if name_lower in self.medicine_index_map:
            idx = self.medicine_index_map[name_lower]
            return self.medicines[idx]
        
        # Fuzzy search (partial match)
        for med in self.medicines:
            if name_lower in med['name'].lower():
                return med
        
        return None
    
    def recommend_similar(self, medicine_name, top_n=5, exclude_self=True):
        """
        Recommend similar medicines based on use cases and components.
        
        Args:
            medicine_name: Name of the medicine to find similar ones for
            top_n: Number of recommendations to return
            exclude_self: Whether to exclude the input medicine from results
            
        Returns:
            List of tuples: (medicine_dict, similarity_score)
        """
        if self.feature_vectors is None:
            print("Error: Model not trained. Please call train_model() first.")
            return []
        
        # Find the input medicine
        input_medicine = self.find_medicine(medicine_name)
        if input_medicine is None:
            print(f"Error: Medicine '{medicine_name}' not found in database.")
            return []
        
        # Get index of input medicine
        input_idx = self.medicine_index_map[input_medicine['name'].lower()]
        
        # Get feature vector for input medicine
        input_vector = self.feature_vectors[input_idx]
        
        # Calculate cosine similarity with all medicines
        similarities = cosine_similarity(input_vector, self.feature_vectors).flatten()
        
        # Get indices sorted by similarity (descending)
        similar_indices = np.argsort(similarities)[::-1]
        
        # Build results list
        recommendations = []
        for idx in similar_indices:
            if exclude_self and idx == input_idx:
                continue
            
            similarity_score = float(similarities[idx])
            recommendations.append((self.medicines[idx], similarity_score))
            
            if len(recommendations) >= top_n:
                break
        
        return recommendations
    
    def get_recommendation_details(self, original_medicine, recommendations):
        """
        Format recommendation results with detailed comparison.
        
        Args:
            original_medicine: The input medicine dictionary
            recommendations: List of (medicine_dict, similarity_score) tuples
            
        Returns:
            Formatted string with recommendation details
        """
        output = []
        output.append("=" * 70)
        output.append(f"ORIGINAL MEDICINE: {original_medicine['name']}")
        output.append("=" * 70)
        output.append(f"Category: {original_medicine.get('category', 'N/A')}")
        output.append(f"Uses: {', '.join(original_medicine.get('uses', []))}")
        output.append(f"Components: {', '.join(original_medicine.get('components', []))}")
        if original_medicine.get('description'):
            output.append(f"Description: {original_medicine['description']}")
        
        output.append("\n" + "=" * 70)
        output.append(f"RECOMMENDED SIMILAR MEDICINES (Top {len(recommendations)})")
        output.append("=" * 70)
        
        for rank, (med, score) in enumerate(recommendations, 1):
            output.append(f"\n{rank}. {med['name']} (Similarity: {score:.3f})")
            output.append(f"   Category: {med.get('category', 'N/A')}")
            output.append(f"   Uses: {', '.join(med.get('uses', []))}")
            output.append(f"   Components: {', '.join(med.get('components', []))}")
            
            # Show shared uses
            original_uses = set(original_medicine.get('uses', []))
            med_uses = set(med.get('uses', []))
            shared_uses = original_uses.intersection(med_uses)
            if shared_uses:
                output.append(f"   Shared Uses: {', '.join(shared_uses)}")
            
            # Show shared components
            original_components = set(original_medicine.get('components', []))
            med_components = set(med.get('components', []))
            shared_components = original_components.intersection(med_components)
            if shared_components:
                output.append(f"   Shared Components: {', '.join(shared_components)}")
            
            if med.get('description'):
                output.append(f"   Description: {med['description']}")
        
        return "\n".join(output)
