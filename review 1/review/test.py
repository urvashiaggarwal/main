# import os
# import pandas as pd
# from collections import defaultdict
# from dotenv import load_dotenv
# import google.generativeai as genai

# # Load environment variables
# load_dotenv()

# # Configure Gemini
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = genai.GenerativeModel('gemini-2.0-flash')

# def load_and_preprocess(csv_path):
#     """Load CSV and handle missing/duplicate data"""
#     df = pd.read_csv(csv_path)
    
#     # Clean data
#     df = df.dropna(subset=['Xid'])  # Remove rows missing project IDs
#     df['Positive review'] = df['Positive review'].fillna('')
#     df['Negative Review'] = df['Negative Review'].fillna('')
    
#     # Convert ratings to numeric
#     df['Google Ratings'] = pd.to_numeric(df['Google Ratings'], errors='coerce').fillna(0)
    
#     return df

# def organize_reviews(df):
#     """Group reviews by Xid and sentiment"""
#     projects = defaultdict(lambda: {'positive': [], 'negative': []})
    
#     for _, row in df.iterrows():
#         xid = row['Xid']
#         review_text = f"Rating: {row['Google Ratings']} - {row['Positive review']} {row['Negative Review']}".strip()
        
#         if row['Google Ratings'] >= 4:  # Positive
#             projects[xid]['positive'].append(review_text)
#         else:  # Negative
#             projects[xid]['negative'].append(review_text)
    
#     return projects

# def generate_summary(positive_batch, negative_batch):
#     """Generate professional summary using Gemini"""
#     prompt = f"""
#     Create a concise real estate review summary for a property management team.
#     Focus on actionable insights from these guest reviews:

#     POSITIVE FEEDBACK:
#     {chr(10).join(positive_batch)}

#     NEGATIVE FEEDBACK:
#     {chr(10).join(negative_batch)}

#     Format exactly as:
#     === SUMMARY ===
#     Strengths:
#     - [Most praised aspect 1]
#     - [Notable positive 2]
    
#     Improvement Areas:
#     - [Critical issue 1]
#     - [Frequent complaint 2]
    
#     """
    
    
    
#     try:
#         response = model.generate_content(prompt)
#         return response.text
#     except Exception as e:
#         return f"Summary generation error: {str(e)}"

# def process_reviews(csv_path, batch_size=5):
#     """Full processing pipeline"""
#     df = load_and_preprocess(csv_path)
#     projects = organize_reviews(df)
#     results = {}
    
#     for xid, reviews in projects.items():
#         # Create balanced batches
#         pos_batches = [reviews['positive'][i:i + batch_size] 
#                       for i in range(0, len(reviews['positive']), batch_size)]
#         neg_batches = [reviews['negative'][i:i + batch_size] 
#                       for i in range(0, len(reviews['negative']), batch_size)]
        
#         # Process matched batches
#         summaries = []
#         for i in range(min(len(pos_batches), len(neg_batches))):
#             summary = generate_summary(pos_batches[i], neg_batches[i])
#             summaries.append(summary)
        
#         # Process remaining reviews
#         if len(pos_batches) > len(neg_batches):
#             for batch in pos_batches[len(neg_batches):]:
#                 summaries.append(generate_summary(batch, ["No negative reviews in this batch"]))
#         elif len(neg_batches) > len(pos_batches):
#             for batch in neg_batches[len(pos_batches):]:
#                 summaries.append(generate_summary(["No positive reviews in this batch"], batch))
        
#         results[xid] = {
#             'project_name': df[df['Xid'] == xid]['Project Name'].iloc[0],
#             'summaries': summaries,
#             'total_reviews': len(reviews['positive']) + len(reviews['negative'])
#         }
    
#     return results

# def save_results(results, output_file='review_summaries.csv'):
#     """Save summaries to CSV"""
#     output_data = []
    
#     for xid, data in results.items():
#         for i, summary in enumerate(data['summaries'], 1):
#             output_data.append({
#                 'Xid': xid,
#                 'Project Name': data['project_name'],
#                 'Batch': i,
#                 'Summary': summary,
#                 'Total Reviews': data['total_reviews']
#             })
    
#     pd.DataFrame(output_data).to_csv(output_file, index=False)
#     print(f"Results saved to {output_file}")

# if __name__ == "__main__":
#     # Example usage
#     input_csv = "test_reviews.csv"  # Your input file
#     output_csv = "summaries.csv"  # Output file
    
#     print(f"Processing {input_csv}...")
#     results = process_reviews(input_csv)
#     save_results(results, output_csv)
    
#     # Print sample output
#     print("\nSample Summary:")
#     first_xid = next(iter(results))
#     print(results[first_xid]['summaries'][0])


































import os
import pandas as pd
import time
from collections import defaultdict
from dotenv import load_dotenv
import google.generativeai as genai
import json
from pathlib import Path

# Configuration
load_dotenv()
CACHE_FILE = "review_cache.json"
RATE_LIMIT_DELAY = 5  # seconds between API calls
MAX_RETRIES = 3

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

def load_cache():
    """Load cached summaries to avoid reprocessing"""
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save processed summaries to cache"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def safe_generate_summary(prompt, cache_key=None):
    """Generate summary with rate limit handling and caching"""
    cache = load_cache()
    
    # Check cache first
    if cache_key and cache_key in cache:
        return cache[cache_key]
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = model.generate_content(prompt)
            result = response.text
            
            # Cache the result
            if cache_key:
                cache[cache_key] = result
                save_cache(cache)
                
            return result
            
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                wait_time = RATE_LIMIT_DELAY * (retries + 1)
                print(f"Rate limit hit. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
            else:
                return f"Summary generation error: {str(e)}"
    
    return "Failed to generate summary after multiple retries"

def generate_summary(positive_batch, negative_batch, xid, batch_num):
    """Generate professional summary with caching"""
    cache_key = f"{xid}_batch_{batch_num}"
    prompt = f"""
    Create a concise real estate review summary for property management.
    Focus on actionable insights from these resident reviews:
    
    POSITIVE FEEDBACK:
    {chr(10).join(positive_batch)}

    NEGATIVE FEEDBACK:
    {chr(10).join(negative_batch)}

    Format as:
    === SUMMARY ===
    Strengths:
    - [Key positive 1]
    - [Key positive 2]
    
    Improvement Areas:
    - [Main issue 1]
    - [Secondary issue 2]
    
    (Max 3 bullet points per section)
    """
    
    return safe_generate_summary(prompt, cache_key)

def process_reviews(csv_path, batch_size=5):
    """Full processing pipeline with enhanced error handling"""
    df = pd.read_csv(csv_path)
    projects = defaultdict(lambda: {'positive': [], 'negative': []})
    
    # Organize reviews
    for _, row in df.iterrows():
        xid = row['Xid']
        rating = row['Google Ratings']
        combined_review = f"{row['Positive review']} {row['Negative Review']}".strip()
        
        if rating >= 4:
            projects[xid]['positive'].append(combined_review)
        else:
            projects[xid]['negative'].append(combined_review)
    
    results = []
    for xid, reviews in projects.items():
        project_name = df[df['Xid'] == xid]['Project Name'].iloc[0]
        total_reviews = len(reviews['positive']) + len(reviews['negative'])
        
        # Create balanced batches
        pos_batches = [reviews['positive'][i:i + batch_size] 
                      for i in range(0, len(reviews['positive']), batch_size)]
        neg_batches = [reviews['negative'][i:i + batch_size] 
                      for i in range(0, len(reviews['negative']), batch_size)]
        
        # Process batches
        for i in range(max(len(pos_batches), len(neg_batches))):
            pos_batch = pos_batches[i] if i < len(pos_batches) else ["No positive reviews"]
            neg_batch = neg_batches[i] if i < len(neg_batches) else ["No negative reviews"]
            
            summary = generate_summary(pos_batch, neg_batch, xid, i+1)
            
            results.append({
                'Xid': xid,
                'Project Name': project_name,
                'Batch': i+1,
                'Summary': summary,
                'Total Reviews': total_reviews
            })
            
            # Respect rate limits
            time.sleep(RATE_LIMIT_DELAY)
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    input_csv = "test_reviews.csv"
    output_csv = "summaries_enhanced.csv"
    
    print(f"Processing {input_csv} ")
    results_df = process_reviews(input_csv)
    results_df.to_csv(output_csv, index=False)
    
    print(f"\nSample Output:")
    print(results_df.head(3).to_string(index=False))