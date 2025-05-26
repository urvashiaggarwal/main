import gspread
import json
import pandas as pd
from typing import List, Dict, Any
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import re
from collections import defaultdict
 
# Gemini model client wrapper
class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash", generation_config: Dict[str, Any] = None):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
 
    def generate(self, prompt: str) -> str:
        response = self.model.generate_content([prompt])
        return response.text
 
# Pydantic model for structured response
class ConfigPriceScore(BaseModel):
    index: int
    data_point_name: str
    ref_value: str  # 99acres_value
    comparable_source: str
    comparable_row: str
    option_matching_score: int
    price_matching_score: int
 
# Main processor class
class ConfigPriceProcessor:
    def __init__(self, sheet, gemini_client: GeminiClient):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.gemini_client = gemini_client
 
    def extract_json_from_response(self, response_text: str):
        try:
            if not response_text.strip():
                print("Empty response received from Gemini client.")
                return []
            cleaned_response = re.sub(r"```(?:python|json)?", "", response_text).strip()
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            print("Cleaned response was:", cleaned_response)
            return []
 
    def process_config_price(self) -> List[ConfigPriceScore]:
        required_columns = ["Index", "data_point_name", "99acres", "Comp 1", "Comp 2", "Comp 3"]
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
 
        data_records = self.df.to_dict(orient='records')
 
        prompt = f"""
        You are provided real estate configuration data as JSON.  
        Process "Config price" data from a Google Sheet (identified by "Index" and "data_point_name"). The "99acres" value is the reference; compare it against "Comp 1/ C1," "Comp 2/ C2," and "Comp 3/ C3" for the same "Index" to generate matching scores.
        Config price strings follow the format: "Configuration (ex- 2 BHK) & Property Type (ex- Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse) – Area Type (Carpet, Super area, Built up area) – Area (ex- 1850 sq ft, 700 sq mt) – Price (can be in Lacs/ Lakhs/ Lakh/ L or Crores/ Cr/ C)".
        Details from "Configuration & Property Type- Area Type- Area" is called "Option Data".
 
        Comparable cells can have multiple strings. Each row will have multiple strings of data separated by "|".
        Configuration might be missing for some property types; assume "Apartment" for Comp 1/ C1 when area type is absent but configuration exists.
        In Comp 3/ C3, we will give you two "area type- area" details in the same string of data. In this case, first compare the "area type- area" details that matches with ref. If no area type matches with ref, in that case, compare the area detail with ref, irrespective of area type mismatch, to assign a matching score.
 
        Task:
1. For each reference row, find a matching data string from each comparable source, by matching "Configuration & Property Type- Area Type- Area" in the same order, following the below mentioned conditions:
a) Configuration (2 BHK, 3 BHK, etc). If the configuration is in decimals, round it down to lower absolute number (ex- 3.5 BHK should be taken as 3 BHK)
b) Property Type (Note the below to be synonyms- Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse)
c) Area Type (Carpet, Super area, Built up area)
d) Area (ex- 1850 sq ft, 700 sq mt). Standardize Area to sq ft before comparison. Give a matching score of 0 even if the "Area" value in reference and comparable differ by +/-1.
The above will give you "Option Matching Score" (1 if "Option Data" in a comparable matches reference, 0 otherwise)
2. Then calculate "Price Matching Score" (1 if the price of the above matched string is +/- 5% of reference price, 0 otherwise).
 
Comparable Rows (comma separated data string from each comparable row with which reference value matches, from each Comparable Source in a single cell), Sum of Option Matching score, Sum of Price Matching score. 
Give output of all comparables against a reference row in one row only. In Comparable Sources, give the name of only those sources against which a reference match was found. 
Include those reference rows in the output where the Matching score of option is 0. 
Give "NA" as output in Comparable source and Comparable row column, where their is no match against reference.
Do not give codes.
 
        Output Format:
        - Index
        - data_point_name
        - 99acres_value
        - Comparable Source (Comp 1, Comp 2, Comp 3)
        - Comparable Rows        
        - Sum of Option Matching score
        - Sum of Price Matching score

        Include rows where the Option Matching Score is 0. Do not include any additional text or explanation.

        Here is the data:
        {json.dumps(data_records)}
        """
 
        try:
            response_text = self.gemini_client.generate(prompt)
            print("Raw response from Gemini client:", response_text)
            json_data = self.extract_json_from_response(response_text)
        except Exception as e:
            print(f"Error generating or parsing response: {e}")
            return []
 
        grouped = defaultdict(lambda: {
            "index": None,
            "data_point_name": None,
            "ref_value": None,
            "comparable_sources": [],
            "comparable_rows": [],
            "option_matching_score": 0,
            "price_matching_score": 0
        })
 
        for entry in json_data:
            # Replace missing fields with default values
            entry["Index"] = entry.get("Index") or "No Index"
            entry["data_point_name"] = entry.get("data_point_name") or "No data point name"
            entry["99acres_value"] = entry.get("99acres") or "No 99acres value"
            entry["comparable_source"] = entry.get("Comparable Source") or "No comparable source"
            entry["comparable_row"] = entry.get("Comparable Row") or entry.get("Comparable Rows") or "No comparable row"
            entry["option_matching_score"] = entry.get("Sum of Option Matching score", 0)
            entry["price_matching_score"] = entry.get("Sum of Price Matching score", 0)

            if all(k in entry for k in ["Index", "data_point_name", "99acres_value", "comparable_source", "comparable_row", "option_matching_score", "price_matching_score"]):
                key = entry["99acres_value"]
                group = grouped[key]
                group["index"] = entry["Index"]
                group["data_point_name"] = entry["data_point_name"]
                group["ref_value"] = key
                group["comparable_sources"].append(entry["comparable_source"])
                group["comparable_rows"].append(entry["comparable_row"])
                group["option_matching_score"] += entry["option_matching_score"]
                group["price_matching_score"] += entry["price_matching_score"]
            else:
                print(f"Invalid entry detected and skipped: {entry}")
 
        # Convert grouped results into ConfigPriceScore objects
        result_scores = []
        for group in grouped.values():
            result_scores.append(ConfigPriceScore(
                index=group["index"],
                data_point_name=group["data_point_name"],
                ref_value=group["ref_value"],
                comparable_source=", ".join(group["comparable_sources"]),
                comparable_row="; ".join(group["comparable_rows"]),
                option_matching_score=group["option_matching_score"],
                price_matching_score=group["price_matching_score"]
            ))
 
        return result_scores
 
    def write_config_price_scores(self, scores: List[ConfigPriceScore]):
        rows = [
            [score.ref_value, score.comparable_source, score.comparable_row, score.option_matching_score, score.price_matching_score]
            for score in scores
        ]
 
        start_row = 2  
        end_row = start_row + len(rows) - 1
        range_name = f"G{start_row}:K{end_row}"  
 
        try:
            self.sheet.update(values=rows, range_name=range_name)
        except Exception as e:
            print(f"Error writing scores to Google Sheet: {e}")
 
# Google Sheets setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
 
creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("config")
 
# Init Gemini client
gemini_client = GeminiClient(
    api_key="AIzaSyCwBsHGSRiV-RUEWIfgqaU_4l6VvRJTOYc",
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 0.8
        # "top_k": 40,
        # "top_p": 0.9
    }
)
 

processor = ConfigPriceProcessor(sheet, gemini_client)
scores = processor.process_config_price()
processor.write_config_price_scores(scores)