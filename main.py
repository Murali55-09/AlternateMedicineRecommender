"""
Main application entry point for Medicine Recommendation System.
Provides CLI interface for users to search medicines and get ML-based recommendations.
"""

from medicine_recommender import MedicineRecommender


def main():
    """Main application loop."""
    print("=" * 70)
    print("ML-Based Medicine Recommendation System")
    print("=" * 70)
    print()
    
    # Initialize recommender
    recommender = MedicineRecommender()
    
    # Load database
    if not recommender.load_database():
        print("Failed to load database. Exiting.")
        return
    
    # Train the ML model
    print("\nTraining recommendation model...")
    if not recommender.train_model():
        print("Failed to train model. Exiting.")
        return
    
    print("\nModel ready! You can now search for medicines.\n")
    
    # Main interaction loop
    while True:
        print("-" * 70)
        medicine_name = input("Enter medicine name (or 'quit' to exit): ").strip()
        
        if medicine_name.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using Medicine Recommendation System!")
            break
        
        if not medicine_name:
            print("Please enter a valid medicine name.")
            continue
        
        # Get number of recommendations
        try:
            top_n_input = input("Number of recommendations (default: 5): ").strip()
            top_n = int(top_n_input) if top_n_input else 5
            if top_n < 1:
                top_n = 5
        except ValueError:
            top_n = 5
        
        print("\n" + "=" * 70)
        print("Searching...")
        print("=" * 70)
        
        # Get recommendations
        recommendations = recommender.recommend_similar(medicine_name, top_n=top_n)
        
        if recommendations:
            # Get original medicine for comparison
            original_medicine = recommender.find_medicine(medicine_name)
            if original_medicine:
                # Display formatted results
                results = recommender.get_recommendation_details(
                    original_medicine, 
                    recommendations
                )
                print("\n" + results)
            else:
                print(f"Error: Could not find original medicine '{medicine_name}'.")
        else:
            print(f"\nNo recommendations found for '{medicine_name}'.")
            print("The medicine might not exist in the database.")
        
        print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
