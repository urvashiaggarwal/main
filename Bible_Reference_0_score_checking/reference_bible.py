import os
import json
import pandas as pd
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types
import dotenv
import chardet

dotenv.load_dotenv()

# Pydantic model for LLM response
class ScoreAnalysis(BaseModel):
    index: str
    data_point_name: str
    sentence: str
    source: str
    value: str

class BibleScoreChecker:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='biblehhhh_prompts.json'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.__client = genai.Client(api_key=api_key)
        self.__model_name = model_name
        self.__prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        try:
            with open(self.__prompt_path, 'r') as file:
                data = json.load(file)
            return data.get(prompt_key, "")
        except FileNotFoundError:
            # Default prompt if file doesn't exist
            return """
          You will be given the data in the form of a list having columns- index, data_point_name, reference_text.
The data_point_name will be:
1. Project Name is the name of the project
2. Builder Name also known as Builder, Developer
3. Project Address also known as Locality or city
4. Amenities also known as Facilities
5. Completion date also known as Possession date
6. Possession Status also known as Possession. It can be Ready to Move (Also known as R2M, RTM, Ready), Under Construction (Also known as UC, ongoing), New Launch (Also known as NL, new), Partial Ready to move , etc.
7. RERA
8. Property Type can be Apartment (also called as Flat, Penthouse, Pentsuites), Villas (also called as villa, row houses), Studio Apartment (also called as 1 RK, studio, serviced apartments, bed studio), independent floor (also called as ind floor, builder floor), land (also called as plot, residential plot), etc.
9. Project Area also known as area. It can be in different formats like- acres/acre, hectare, sq ft, sq yards.
10. Configs also known as Config, Configuration. It is in BHK, RK, Beds, Bed, etc
11. Project Size - Tower Count also known as Tower, Building, buildings
12. Project Size - Unit Count also known as Unit, Units
13. Option and Price also known as Option, FP, Floor Plans
Your task:
You task is to read reference_text for given data_point_name and quote the sentence around the given data_point_name from the reference_text.
Then analyze the sentence and give in the next column the source(like URLs,builder webite,sales,email,field,website name,builder,listings,RERA etc) for the given data_point_name .
Also give the value as per the sentence for the given data_point_name.
If there is nothing present about the data_point_name in the reference_text, give the output "NA".
Output-
Return your output in the specified JSON format.					"""

    def load_csv_files(self, reference_csv_path: str, score_csv_path: str):
      
        try:
          

            with open(reference_csv_path, "rb") as f:
                result = chardet.detect(f.read())
            reference_df = pd.read_csv(reference_csv_path, encoding=result['encoding'])
            
           
            with open(score_csv_path, "rb") as f:
                result = chardet.detect(f.read())
            score_df = pd.read_csv(score_csv_path, encoding=result['encoding'])
            
            required_ref_cols = ['index', 'reference_text']
            required_score_cols = ['index', 'data_point_name', 'bible_score']
            
            # Validate columns
            if not all(col in reference_df.columns for col in required_ref_cols):
                raise ValueError(f"Reference CSV must contain columns: {required_ref_cols}")
            
            if not all(col in score_df.columns for col in required_score_cols):
                raise ValueError(f"Score CSV must contain columns: {required_score_cols}")
            
            return reference_df, score_df
            
        except Exception as e:
            raise ValueError(f"Error loading CSV files: {e}")

    def get_zero_score_data(self, reference_df: pd.DataFrame, score_df: pd.DataFrame):
      
        # Filter for zero scores
        zero_scores = score_df[score_df['bible_score'] == 0]
        
        if zero_scores.empty:
            print("No records found with bible_score = 0")
            return pd.DataFrame()
        
        
        combined_df = zero_scores.merge(
            reference_df[['index', 'reference_text']], 
            on='index', 
            how='left'
        )
        
      
        missing_refs = combined_df[combined_df['reference_text'].isna()]
        if not missing_refs.empty:
            print(f"Warning: {len(missing_refs)} records have missing reference texts")
        
        # Remove rows with missing reference text
        combined_df = combined_df.dropna(subset=['reference_text'])
    
        
        return combined_df[['index', 'data_point_name', 'reference_text']]

    def analyze_zero_scores(self, zero_score_df: pd.DataFrame) -> List[ScoreAnalysis]:
      
        if zero_score_df.empty:
            return []
        
        prompt = self.__load_prompt("zero_score_analyzer")
        
    
        data_for_llm = zero_score_df.to_json(orient='records')
        
        contents = [
            types.Content(role="user", parts=[
            types.Part.from_text(text=data_for_llm)
            ])
        ]

        config = types.GenerateContentConfig(
            temperature=1.0,  
            response_mime_type="application/json",
            response_schema=list[ScoreAnalysis],
            system_instruction=[types.Part.from_text(text=prompt)],
        )

        try:
            response = self.__client.models.generate_content(
                model=self.__model_name,
                contents=contents,
                config=config
            )

            raw_text = response.candidates[0].content.parts[0].text.strip()

            if not raw_text:
                raise ValueError("Empty response from LLM")

            parsed = json.loads(raw_text)
            return [ScoreAnalysis(**item) for item in parsed]
            
        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            raise

    def save_results_to_csv(self, results: List[ScoreAnalysis], output_path: str):
       
        if not results:
            print("No results to save")
            return
        
        # Convert to DataFrame
        results_data = []
        for result in results:
            results_data.append({
                'index': result.index,
                'data_point_name': result.data_point_name,
                'sentence': result.sentence,
                'source': result.source,
                'value': result.value
            })
        
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}")

    def process_zero_scores(self, reference_csv_path: str, score_csv_path: str, output_csv_path: str):
     
        print("Loading CSV files...")
        reference_df, score_df = self.load_csv_files(reference_csv_path, score_csv_path)
        
        print("Filtering zero score records...")
        zero_score_df = self.get_zero_score_data(reference_df, score_df)
    
        if zero_score_df.empty:
            print("No zero score records to process")
            return
        
        print(f"Found {len(zero_score_df)} records with zero scores")
        print("Zero score records to be analyzed:")
        print(zero_score_df)
        print("Sending to LLM for analysis...")
        
        results = self.analyze_zero_scores(zero_score_df)
        
        print("Saving results...")
        self.save_results_to_csv(results, output_csv_path)
        
        print("Process completed successfully!")


def main():

    checker = BibleScoreChecker()
    

    reference_csv = "reference_data.csv"  # CSV with xid, reference_text
    score_csv = "score_data.csv"          # CSV with xid, data_point_name, bible_score
    output_csv = "zero_score_analysis.csv"  # Output CSV
    
    try:
        checker.process_zero_scores(reference_csv, score_csv, output_csv)
    except Exception as e:
        print(f"Error in processing: {e}")


if __name__ == "__main__":
    main()