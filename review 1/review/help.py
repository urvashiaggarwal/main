import pandas as pd
from collections import defaultdict
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
import re
from itertools import product

# Load API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Common profanity words to filter out
PROFANITY_WORDS = {
    'cheat', 'fraud', 'scam', 'cheater', 'fraudster',
    'scammer', 'thief', 'steal', 'stolen', 'lie', 'liar', 'lying',
    'fake', 'false', 'dishonest', 'untrustworthy', 'unreliable'
}

def contains_profanity(text):
    """Check if text contains profanity or inappropriate words"""
    text_lower = text.lower()
    # Check for exact word matches to avoid partial matches
    words = set(text_lower.split())
    return any(word in PROFANITY_WORDS for word in words)

def clean_review_text(review):
    """Clean review text by removing timestamps and extra whitespace"""
    review = re.sub(r'\d+\s+years?\s+ago', '', review)
    review = ' '.join(review.split())
    return review.strip()

def analyze_review(review, rating):
    """Use Gemini to analyze a review and determine if it should be rejected"""
    try:
        prompt = f"""
        Analyze this real estate review and determine if it should be rejected based on the following criteria:

        For reviews with rating >= 3:
        - Reject if overly positive with excessive praise
        - Reject if mainly about construction progress/status
        - Reject if contains unrealistic claims
        - Accept if balanced and focuses on actual living experience

        For reviews with rating < 3:
        - Reject if mainly discusses construction status/progress
        - Reject if focuses on delivery timelines
        - Reject if about builder/developer issues
        - Reject if about sales/marketing concerns
        - Reject if about payment/refund issues
        - Accept if focuses on actual living experience, amenities, or community

        Review: "{review}"
        Rating: {rating}

        Return 'true' if the review should be rejected, 'false' if it should be accepted.
        Return only 'true' or 'false'.
        """
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        time.sleep(5)  # Rate limiting
        return response.text.strip().lower() == 'true'
    except Exception as e:
        print(f"Error in analyze_review: {str(e)}")
        # Default to false if API call fails
        return False

def contains_sales_team_mention(review):
    """Check if review mentions anything about sales team"""
    sales_team_keywords = [
        'sales team', 'salesperson', 'sales executive', 'sales representative',
        'sales staff', 'sales department', 'sales office', 'sales process',
        'sales experience', 'sales service', 'sales management', 'sales handling',
        'sales approach', 'sales pitch', 'sales call', 'sales visit',
        'sales people', 'sales personnel', 'sales associate', 'sales consultant'
    ]
    review_lower = review.lower()
    return any(keyword in review_lower for keyword in sales_team_keywords)

def get_rejection_reason(review, rating):
    """Determine the specific reason for rejecting a review"""
    reasons = []
    
    if contains_profanity(review):
        reasons.append("Contains inappropriate language or offensive words")
    
    if contains_sales_team_mention(review):
        reasons.append("Focuses on sales team/process rather than actual living experience")
    
    if rating >= 3 and analyze_review(review, rating):
        reasons.append("Review is overly positive with excessive praise or focuses on construction status")
    
    if rating < 3 and analyze_review(review, rating):
        reasons.append("Review focuses on construction/delivery/builder issues rather than actual living experience")
    
    return "; ".join(reasons) if reasons else "Unknown reason"

def process_review(review, rating, pos_review=None, neg_review=None):
    """Use Gemini to analyze a review or generate a merged review"""
    try:
        if pos_review and neg_review:
            # Generate merged review
            prompt = f"""
            Create a balanced review for a real estate project that includes the following information:

            What I like about the project:
            [Write a paragraph about positive aspects from the provided positive review. Do not add anything new.]

            What I don't like:
            [Write a paragraph about negative aspects from the provided negative review. Do not add anything new.]

            Rules:
            1. Only use information from the provided reviews
            2. Keep the language simple and conversational
            3. Ensure pros and cons don't contradict
            4. Avoid construction/delivery/builder content
            5. Focus on actual living experience
            6. Keep each section brief and specific
            7. Include a natural mention of how long you've stayed
            8. Make it sound like a genuine resident's review
            9. If any review contains profane words, don't consider that statement
            10. Give Likes and Dislikes in paragraph, not in pointers
            11. Create a review of about 300 words

            Positive review: "{pos_review}"
            Negative review: "{neg_review}"

            Generate the review in the exact format shown above, with "What I like about the project:" and "What I don't like:" as section headers.
            """
        else:
            # Analyze single review
            prompt = f"""
            Analyze this real estate review and determine if it should be rejected based on the following criteria:

            For reviews with rating >= 3:
            - Reject if overly positive with excessive praise
            - Reject if mainly about construction progress/status
            - Reject if contains unrealistic claims
            - Accept if balanced and focuses on actual living experience

            For reviews with rating < 3:
            - Reject if mainly discusses construction status/progress
            - Reject if focuses on delivery timelines
            - Reject if about builder/developer issues
            - Reject if about sales/marketing concerns
            - Reject if about payment/refund issues
            - Accept if focuses on actual living experience, amenities, or community

            Review: "{review}"
            Rating: {rating}

            Return 'true' if the review should be rejected, 'false' if it should be accepted.
            Return only 'true' or 'false'.
            """
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        time.sleep(5)  # Rate limiting
        return response.text.strip()
    except Exception as e:
        print(f"Error in process_review: {str(e)}")
        # Return empty string for generation, false for analysis
        return "" if pos_review and neg_review else "false"

def load_and_categorize_reviews(csv_path):
    """Load reviews and categorize them into top-rated and overall reviews"""
    df = pd.read_csv(csv_path)
    required_cols = ['xid', 'Project Name', 'Review', 'Google rating']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df['Google rating'] = pd.to_numeric(df['Google rating'], errors='coerce')
    
    grouped_reviews = defaultdict(lambda: {
        "top_rated": [],  # Top 10 highest rated reviews
        "overall": []     # Top 10 overall reviews
    })
    
    # Track used reviews across all XIDs
    used_reviews = set()
    
    # Track rejected reviews
    rejected_reviews = []
    
    # Track API errors
    api_errors = []
    
    for xid, group in df.groupby('xid'):
        # Get top 10 highest rated reviews
        top_rated = group.nlargest(10, 'Google rating')
        # Get top 10 overall reviews
        overall = group.head(10)
        
        for _, row in top_rated.iterrows():
            try:
                review = clean_review_text(str(row['Review']))
                rating = float(row['Google rating'])
                
                # Basic checks first
                if (not review or review in used_reviews or 
                    contains_profanity(review) or 
                    contains_sales_team_mention(review)):
                    rejected_reviews.append({
                        "Project Name": row['Project Name'],
                        "XID No.": xid,
                        "Review": review,
                        "Google Rating": rating,
                        "Rejection Reason": get_rejection_reason(review, rating)
                    })
                    continue
                
                # AI-based check with error handling
                try:
                    if process_review(review, rating).lower() == 'true':
                        rejected_reviews.append({
                            "Project Name": row['Project Name'],
                            "XID No.": xid,
                            "Review": review,
                            "Google Rating": rating,
                            "Rejection Reason": get_rejection_reason(review, rating)
                        })
                        continue
                except Exception as e:
                    api_errors.append({
                        "Project Name": row['Project Name'],
                        "XID No.": xid,
                        "Review": review,
                        "Error": str(e)
                    })
                    # Continue processing without AI check
                    pass
                
                review_entry = {
                    "review": review,
                    "rating": rating,
                    "project_name": row['Project Name']
                }
                
                if rating >= 3:
                    grouped_reviews[xid]["top_rated"].append(review_entry)
                    used_reviews.add(review)
                else:
                    grouped_reviews[xid]["top_rated"].append(review_entry)
                    used_reviews.add(review)
                    
            except Exception as e:
                print(f"Error processing review: {str(e)}")
                continue
                
        # Similar processing for overall reviews...
        for _, row in overall.iterrows():
            try:
                review = clean_review_text(str(row['Review']))
                rating = float(row['Google rating'])
                
                # Basic checks first
                if (not review or review in used_reviews or 
                    contains_profanity(review) or 
                    contains_sales_team_mention(review)):
                    rejected_reviews.append({
                        "Project Name": row['Project Name'],
                        "XID No.": xid,
                        "Review": review,
                        "Google Rating": rating,
                        "Rejection Reason": get_rejection_reason(review, rating)
                    })
                    continue
                
                # AI-based check with error handling
                try:
                    if process_review(review, rating).lower() == 'true':
                        rejected_reviews.append({
                            "Project Name": row['Project Name'],
                            "XID No.": xid,
                            "Review": review,
                            "Google Rating": rating,
                            "Rejection Reason": get_rejection_reason(review, rating)
                        })
                        continue
                except Exception as e:
                    api_errors.append({
                        "Project Name": row['Project Name'],
                        "XID No.": xid,
                        "Review": review,
                        "Error": str(e)
                    })
                    # Continue processing without AI check
                    pass
                
                review_entry = {
                    "review": review,
                    "rating": rating,
                    "project_name": row['Project Name']
                }
                
                if rating >= 3:
                    grouped_reviews[xid]["overall"].append(review_entry)
                    used_reviews.add(review)
                else:
                    grouped_reviews[xid]["overall"].append(review_entry)
                    used_reviews.add(review)
                    
            except Exception as e:
                print(f"Error processing review: {str(e)}")
                continue
    
    # Save rejected reviews to CSV
    if rejected_reviews:
        rejected_df = pd.DataFrame(rejected_reviews)
        rejected_df.to_csv("rejected_reviews.csv", index=False)
        print(f"[+] Saved {len(rejected_reviews)} rejected reviews to: rejected_reviews.csv")
    
    # Save API errors to CSV
    if api_errors:
        errors_df = pd.DataFrame(api_errors)
        errors_df.to_csv("api_errors.csv", index=False)
        print(f"[!] Saved {len(api_errors)} API errors to: api_errors.csv")
                
    return grouped_reviews

def generate_review_combinations(grouped_reviews, max_options=3):
    """Generate 3 distinct review combinations for each XID"""
    all_combinations = []
    
    # Track used reviews across all XIDs
    used_reviews = set()
    
    for xid, reviews in grouped_reviews.items():
        # Get positive and negative reviews from both top-rated and overall
        positives = [r for r in reviews["top_rated"] + reviews["overall"] 
                    if r["rating"] >= 3 and r["review"] not in used_reviews]
        negatives = [r for r in reviews["top_rated"] + reviews["overall"] 
                    if r["rating"] < 3 and r["review"] not in used_reviews]
        
        # Generate unique combinations
        combinations = []
        
        for _ in range(min(max_options, len(positives), len(negatives))):
            if not positives or not negatives:
                break
                
            # Select first unused reviews
            pos = positives[0]
            neg = negatives[0]
            
            # Mark as used
            used_reviews.add(pos["review"])
            used_reviews.add(neg["review"])
            
            # Remove from available lists
            positives = positives[1:]
            negatives = negatives[1:]
            
            combination = {
                "Project Name": pos["project_name"],
                "XID No.": xid,
                "Positive Review": pos["review"],
                "Negative Review": neg["review"],
                "Overall Google Rating": (pos["rating"] + neg["rating"]) / 2
            }
            combinations.append(combination)
            
        all_combinations.extend(combinations)
            
    return all_combinations

def generate_merged_review(pos_review, neg_review):
    """Generate a balanced review using Gemini"""
    try:
        prompt = f"""
        Create a balanced review for a real estate project that includes the following information:

        What I like about the project:
        [Write a paragraph about positive aspects from the provided positive review. Do not add anything new.]

        What I don't like:
        [Write a paragraph about negative aspects from the provided negative review. Do not add anything new.]

        Rules:
        1. Only use information from the provided reviews
        2. Keep the language simple and conversational
        3. Ensure pros and cons don't contradict
        4. Avoid construction/delivery/builder content
        5. Focus on actual living experience
        6. Keep each section brief and specific
        7. Include a natural mention of how long you've stayed
        8. Make it sound like a genuine resident's review
        9. If any review contains profane words, don't consider that statement
        10. Give Likes and Dislikes in paragraph, not in pointers
        11. Create a review of about 300 words

        Positive review: "{pos_review}"
        Negative review: "{neg_review}"

        Generate the review in the exact format shown above, with "What I like about the project:" and "What I don't like:" as section headers.
        """
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        time.sleep(5)  # Rate limiting
        return response.text.strip()
    except Exception as e:
        print(f"Error generating merged review: {str(e)}")
        # Return empty string if API call fails
        return ""

def is_similar_review(review1, review2, threshold=0.7):
    """Check if two reviews are too similar"""
    # Simple similarity check based on common words
    words1 = set(review1.lower().split())
    words2 = set(review2.lower().split())
    
    common_words = words1.intersection(words2)
    similarity = len(common_words) / max(len(words1), len(words2))
    
    return similarity > threshold

def process_review_combinations(combinations):
    """Process each combination to generate 3 distinct merged reviews"""
    processed_reviews = defaultdict(lambda: {
        "Project Name": "",
        "XID No.": "",
        "Merged Review 1": "",
        "Merged Review 2": "",
        "Merged Review 3": ""
    })
    
    # Track API errors
    api_errors = []
    
    for xid, group in pd.DataFrame(combinations).groupby("XID No."):
        # Get all combinations for this XID
        xid_combinations = group.to_dict('records')
        
        # Generate reviews and ensure they are distinct
        generated_reviews = []
        for combo in xid_combinations:
            try:
                merged_review = process_review(
                    None,  # No single review to analyze
                    None,  # No rating to check
                    combo["Positive Review"],
                    combo["Negative Review"]
                )
                
                if not merged_review:  # Skip if review generation failed
                    continue
                
                # Check if this review is too similar to any previously generated review
                is_distinct = True
                for existing_review in generated_reviews:
                    if is_similar_review(merged_review, existing_review):
                        is_distinct = False
                        break
                
                if is_distinct:
                    generated_reviews.append(merged_review)
                    
                    # Store in the appropriate column
                    review_num = len(generated_reviews)
                    if review_num <= 3:
                        processed_reviews[xid][f"Merged Review {review_num}"] = merged_review
                        if review_num == 1:  # First review, store project info
                            processed_reviews[xid]["Project Name"] = combo["Project Name"]
                            processed_reviews[xid]["XID No."] = xid
            except Exception as e:
                api_errors.append({
                    "Project Name": combo["Project Name"],
                    "XID No.": xid,
                    "Positive Review": combo["Positive Review"],
                    "Negative Review": combo["Negative Review"],
                    "Error": str(e)
                })
                continue
    
    # Save API errors to CSV
    if api_errors:
        errors_df = pd.DataFrame(api_errors)
        errors_df.to_csv("review_generation_errors.csv", index=False)
        print(f"[!] Saved {len(api_errors)} review generation errors to: review_generation_errors.csv")
        
    return list(processed_reviews.values())

def save_processed_reviews(reviews, output_path):
    """Save the processed reviews to CSV"""
    df = pd.DataFrame(reviews)
    df.to_csv(output_path, index=False)
    print(f"[+] Saved {len(reviews)} processed reviews to: {output_path}")

def main():
    input_csv_path = "input.csv"
    output_csv_path = "processed_reviews.csv"

    print("Loading and categorizing reviews...")
    grouped = load_and_categorize_reviews(input_csv_path)
    
    print("Generating review combinations...")
    combinations = generate_review_combinations(grouped)
    
    print("Processing review combinations...")
    processed_reviews = process_review_combinations(combinations)
    
    print("Saving results...")
    save_processed_reviews(processed_reviews, output_csv_path)
    
    print("Process completed successfully!")

if __name__ == "__main__":
    main()
