import os
import json
import mysql.connector
import pandas as pd
from pydantic import BaseModel
from typing import Union, List, Optional
from google import genai
from google.genai import types
import dotenv
import re
from collections import Counter

dotenv.load_dotenv()

# Pydantic Class
class DataPointScore(BaseModel):
    data_point_name: str
    index: int
    ref_normalised: Optional[str]
    c1_normalised: Optional[str]
    c2_normalised: Optional[str]
    c3_normalised: Optional[str]

class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='gemini_prompts.json'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        self.__client = genai.Client(api_key=api_key)
        self.__model_name = model_name
        self.__prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.__prompt_path, 'r') as file:
            data = json.load(file)
        return data.get(prompt_key, "")

    def get_norm_values(self, input_df: pd.DataFrame, data_point: str, instruction: str) -> List[DataPointScore]:
        prompt = self.__load_prompt("data_point_normalizer")
       
        contents = [
            types.Content(role="user", parts=[
                types.Part.from_text(text=instruction)
            ]),
            types.Content(role="user", parts=[
                types.Part.from_text(text=input_df.to_json(orient='records'))
            ])
        ]

        config = types.GenerateContentConfig(
            temperature=0.8,
            response_mime_type="application/json",
            response_schema=list[DataPointScore],
            system_instruction=[types.Part.from_text(text=prompt)],
        )

        response = self.__client.models.generate_content(
            model=self.__model_name,
            contents=contents,
            config=config
        )

        raw_text = response.candidates[0].content.parts[0].text.strip()

        if not raw_text:
            raise ValueError(f"Empty response for {data_point}")

        try:
            parsed = json.loads(raw_text)
            return [DataPointScore(**item) for item in parsed]
        except Exception as e:
            print(f"Validation failed: {e}")
            raise

class ScoreCalculator:
    def __init__(self):
        pass
    
    def normalize_value(self, value):

        if value is None or pd.isna(value):
            return None
        
        str_val = str(value).strip().lower()
        
        # Check for N/A variants
        na_variants = ['not available', 'n/a', 'na', 'not found', 'null', 'none', '']
        if str_val in na_variants:
            return None
            
        # Removing special characters and spaces 
        normalized = re.sub(r'[^\w.]', '', str_val)
        return normalized if normalized else None
    
    def is_numeric(self, value):

        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def exact_string_match(self, ref_val, comp_val):

        ref_norm = self.normalize_value(ref_val)
        comp_norm = self.normalize_value(comp_val)
        
        if ref_norm is None or comp_norm is None:
            return False
            
        return ref_norm == comp_norm
    
    def numeric_gte_match(self, ref_val, comp_val):

        ref_norm = self.normalize_value(ref_val)
        comp_norm = self.normalize_value(comp_val)
        
        if ref_norm is None or comp_norm is None:
            return False
        
        if not (self.is_numeric(ref_norm) and self.is_numeric(comp_norm)):
            return False
            
        try:
            return float(ref_norm) >= float(comp_norm)
        except (ValueError, TypeError):
            return False
    
    def rera_number_match(self, ref_val, comp_val):
       
        ref_norm = self.normalize_value(ref_val)
        comp_norm = self.normalize_value(comp_val)

        if ref_norm is None or comp_norm is None:
            return False

        if ',' in comp_norm:
            comp_norm_parts = comp_norm.split(',')
            if len(comp_norm_parts) == 2:
                comp_1= comp_norm_parts[0].strip()
                comp_2 = comp_norm_parts[1].strip()
                return ref_norm == comp_1 or ref_norm == comp_2
            else:
                return False
        else :   
            return ref_norm == comp_norm
        return ref_norm in comp_norm or comp_norm in ref_norm
    
    def project_area_match(self, ref_val, comp_val):

        ref_norm = self.normalize_value(ref_val)
        comp_norm = self.normalize_value(comp_val)

        if ref_norm is None or comp_norm is None:
            return False

        if not (self.is_numeric(ref_norm) and self.is_numeric(comp_norm)):
            return False

        try:
            ref_num = float(ref_norm)
            comp_num = float(comp_norm)
            lower = round(ref_num * 0.9, 2)
            upper = round(ref_num * 1.1,2)
            return lower <= comp_num <= upper
        except (ValueError, TypeError):
            return False
        
    def avg_price_psft_match(self, ref_val, comp_val):
        print(f"Comparing ref_val: {ref_val} with comp_val: {comp_val}")
        if ref_val is None or comp_val is None:
            return False

        if '-' in comp_val and '-' in ref_val:
            comp_parts = comp_val.split('-')
            ref_parts = ref_val.split('-')
            if len(comp_parts) == 2 and len(ref_parts) == 2:
                try:
                    comp_min = float(comp_parts[0].strip())
                    comp_max = float(comp_parts[1].strip())
                    ref_min = float(ref_parts[0].strip())
                    ref_max = float(ref_parts[1].strip())
                    # Check if ranges match exactly
                    return comp_min == ref_min and comp_max == ref_max
                except ValueError:
                    return False
            else:
                return False
        elif '-' in comp_val:
            parts = comp_val.split('-')
            if len(parts) == 2:
                try:
                    comp_norm_min = float(parts[0].strip())
                    comp_norm_max = float(parts[1].strip())
                    ref_num = float(ref_val)
                    print(f"Comparing {ref_num} with range {comp_norm_min} - {comp_norm_max}")
                    return comp_norm_min <= ref_num <= comp_norm_max
                except ValueError:
                    return False
            else:
                return False
        elif '-' in ref_val:
            parts = ref_val.split('-')
            if len(parts) == 2:
                try:
                    ref_norm_min = float(parts[0].strip())
                    ref_norm_max = float(parts[1].strip())
                    comp_num = float(comp_val)
                    print(f"Comparing {comp_num} with range {ref_norm_min} - {ref_norm_max}")
                    return ref_norm_min <= comp_num <= ref_norm_max
                except ValueError:
                    return False
            else:
                return False
        else:
            # Single value comparison
            try:
                ref_num = float(ref_val)
                comp_num = float(comp_val)
                return abs(ref_num - comp_num) <= 500
            except ValueError:
                return False
            
    def project_price_range_match(self, ref_val, comp_val):
 
        print(f"Comparing ref_val: {ref_val} with comp_val: {comp_val}")
        if ref_val is None or comp_val is None:
            return False

        if '-' in comp_val and '-' in ref_val:
            comp_parts = comp_val.split('-')
            ref_parts = ref_val.split('-')
            if len(comp_parts) == 2 and len(ref_parts) == 2:
                try:
                    comp_min = float(comp_parts[0].strip())
                    comp_max = float(comp_parts[1].strip())
                    ref_min = float(ref_parts[0].strip())
                    ref_max = float(ref_parts[1].strip())
                    # Check if ranges match exactly
                    return comp_min == ref_min and comp_max == ref_max
                except ValueError:
                    return False
            else:
                return False
        elif '-' in comp_val:
            parts = comp_val.split('-')
            if len(parts) == 2:
                try:
                    comp_norm_min = float(parts[0].strip())
                    comp_norm_max = float(parts[1].strip())
                    ref_num = float(ref_val)
                    print(f"Comparing {ref_num} with range {comp_norm_min} - {comp_norm_max}")
                    return comp_norm_min <= ref_num <= comp_norm_max
                except ValueError:
                    return False
            else:
                return False
        elif '-' in ref_val:
            parts = ref_val.split('-')
            if len(parts) == 2:
                try:
                    ref_norm_min = float(parts[0].strip())
                    ref_norm_max = float(parts[1].strip())
                    comp_num = float(comp_val)
                    print(f"Comparing {comp_num} with range {ref_norm_min} - {ref_norm_max}")
                    return ref_norm_min <= comp_num <= ref_norm_max
                except ValueError:
                    return False
            else:
                return False
        else:
            # Single value comparison
            try:
                return float(ref_val) == float(comp_val)
            except ValueError:
                return False
        
    def numeric_exact_match(self, ref_val, comp_val):

        ref_norm = self.normalize_value(ref_val)
        comp_norm = self.normalize_value(comp_val)
        
        if ref_norm is None or comp_norm is None:
            return False
        
        if not (self.is_numeric(ref_norm) and self.is_numeric(comp_norm)):
            return False
            
        try:
            return float(comp_norm) == float(ref_norm)
        except (ValueError, TypeError):
            return False
    
    def calculate_consensus(self, comparables):
        #Calculate consensus value and score
        valid_comparables = []
        
        for comp in comparables:
            normalized = self.normalize_value(comp)
            if normalized is not None:
                valid_comparables.append(comp)  
        
        if not valid_comparables:
            return None, 0
        
        # Count occurrences
        normalized_counts = Counter()
        value_map = {}  # Map normalized -> original
        
        for val in valid_comparables:
            norm_val = self.normalize_value(val)
            if norm_val:
                normalized_counts[norm_val] += 1
                if norm_val not in value_map:
                    value_map[norm_val] = val
        
        if not normalized_counts:
            return None, 0
        
        # Find mode
        max_count = max(normalized_counts.values())
        consensus_score = max_count
        
        # Get consensus value 
        consensus_normalized = max(normalized_counts, key=normalized_counts.get)
        consensus_value = value_map[consensus_normalized]
        
        # Return N/A if consensus score is 0 or 1
        if consensus_score <= 1:
            return "N/A", consensus_score
            
        return consensus_value, consensus_score
    
    def calculate_score(self, row, data_point_name):
        # Calculating score for a each row
        ref_val = row['ref_normalised']
        comparables = [row['c1_normalised'], row['c2_normalised'], row['c3_normalised']]
        
        if any(keyword in data_point_name for keyword in ['Project Size - Unit Count', 'Project Size - Tower Count','Builder Established Date']):
            match_method = 'numeric_exact'
        elif any(keyword in data_point_name for keyword in ['Photos', 'Videos', 'Review Count', 'Builder Project Count', 'Amenities Count']):
            match_method = 'numeric_gte'
        elif any(keyword in data_point_name for keyword in ['Project Name', 'Completion date', 'RERA', 'Possession Status','Property Type','Configs','Avg Price psft Type','Builder Name','Project Address']):
            match_method = 'exact_string'
        elif any(keyword in data_point_name for keyword in ['Project Area']):
            match_method = 'project_area_match'
        elif 'Avg Price psft' in data_point_name:
            match_method = 'avg_price_psft_match'
        elif 'Price Range' in data_point_name:
            match_method = 'project_price_range_match'
        elif 'RERA Number' in data_point_name:
            match_method = 'rera_number_match'
        else:
            match_method = 'exact_string'
        
        # Check if ref value is N/A
        if self.normalize_value(ref_val) is None:
            score = 0
        else:
            score = 0
            for comp_val in comparables:
                if self.normalize_value(comp_val) is not None:  
                    if match_method == 'exact_string':
                        if self.exact_string_match(ref_val, comp_val):
                            score += 1
                    elif match_method == 'numeric_gte':
                        if self.numeric_gte_match(ref_val, comp_val):
                            score += 1
                    elif match_method == 'numeric_exact':
                        if self.numeric_exact_match(ref_val, comp_val):
                            score += 1
                    elif match_method == 'project_area_match':
                        if self.project_area_match(ref_val, comp_val):
                            score += 1
                    elif match_method == 'avg_price_psft_match':
                        if self.avg_price_psft_match(ref_val, comp_val):
                            score += 1
                    elif match_method == 'project_price_range_match':
                        if self.project_price_range_match(ref_val, comp_val):
                            score += 1
        
        # Calculating den 
        den = sum(1 for comp in comparables if self.normalize_value(comp) is not None)
        
        # Calculating consensus
        consensus_value, consensus_score = self.calculate_consensus(comparables)
        
        return {
            'data_point_name': data_point_name,
            'index': row['index_value'],
            'score': score,
            'den': den,
            'consensus_value': consensus_value,
            'consensus_score': consensus_score
        }

class MySQLProcessor:
    def __init__(self, gemini_client):
        self.client = gemini_client
        self.score_calculator = ScoreCalculator()
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            connection_timeout=5,
            use_pure=True
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def fetch_unscored_rows(self, data_point_name):
        query = """
            SELECT * FROM op_audit_data
            WHERE data_point_name = %s AND is_scored = 0
        """
        self.cursor.execute(query, (data_point_name,))
        return self.cursor.fetchall()
    
    def fetch_normalized_unscored_rows(self, data_point_name):
        # Fetch rows that are normalized but not scored
        query = """
            SELECT * FROM op_audit_data
            WHERE data_point_name = %s AND is_scored = 1 AND score IS NULL
        """
        self.cursor.execute(query, (data_point_name,))
        return self.cursor.fetchall()

    def update_normalization_values(self, results: List[DataPointScore]):
        for r in results:
            update_query = """
                UPDATE op_audit_data
                SET ref_normalised = %s, c1_normalised = %s, c2_normalised = %s, c3_normalised = %s, is_scored = 1
                WHERE index_value = %s AND data_point_name = %s
            """
            self.cursor.execute(update_query, (
                r.ref_normalised,
                r.c1_normalised,
                r.c2_normalised,
                r.c3_normalised,
                r.index,
                r.data_point_name
            ))
            self.conn.commit()
    
    def update_scoring_values(self, results: list):
        #Update database with scores
        for r in results:
            update_query = """
                UPDATE op_audit_data
                SET score = %s, den = %s, consensus_value = %s, consensus_score = %s
                WHERE index_value = %s AND data_point_name = %s
            """
            self.cursor.execute(update_query, (
                r['score'],
                r['den'],
                r['consensus_value'],
                r['consensus_score'],
                r['index'],
                r['data_point_name']
            ))
            self.conn.commit()

    def process_normalization(self, data_point, instruction):

        rows = self.fetch_unscored_rows(data_point)
        if not rows:
            return
        df = pd.DataFrame(rows)
        results = self.client.get_norm_values(df, data_point, instruction)
        self.update_normalization_values(results)
    
    def process_scoring(self, data_point):

        rows = self.fetch_normalized_unscored_rows(data_point)
        if not rows:
            print(f"No normalized rows found for scoring: {data_point}")
            return
        
        results = []
        for row in rows:
            try:
                score_result = self.score_calculator.calculate_score(row, data_point)
                results.append(score_result)
            except Exception as e:
                print(f"Error calculating score for row {row.get('index_value')}: {e}")
        
        if results:
            self.update_scoring_values(results)
            print(f"Updated {len(results)} scoring records for {data_point}")

    def process_data_point_complete(self, data_point, instruction):
    #Complete processing for a data point
        print(f"Processing normalization for: {data_point}")
        self.process_normalization(data_point, instruction)
        
        print(f"Processing scoring for: {data_point}")
        self.process_scoring(data_point)

if __name__ == "__main__":
    client = GeminiClient()
    processor = MySQLProcessor(client)
    
    with open("operation_prompts.json", "r", encoding="utf-8") as file:
        instructions = json.load(file)

    for dp, rule in instructions.items():
        print(f"Processing: {dp}")
        try:
            processor.process_data_point_complete(dp, rule)
        except Exception as e:
            print(f"Error processing {dp}: {e}")