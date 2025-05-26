import gspread
import json
import pandas as pd
from typing import List, Dict, Any, Union
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import re
from collections import defaultdict
import time
 
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
   v1: Union[float, str] = 0.0  # Allow float or 'NA'
   v2: Union[float, str] = 0.0  # Allow float or 'NA'
   v3: Union[float, str] = 0.0  # Allow float or 'NA'
 
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
 
   def process_and_write_batches(self):
       grouped = self.df.groupby("Index")
       for index_value, group_df in grouped:
           print(f"Processing Index: {index_value}")
           records = group_df.to_dict(orient='records')
 
           prompt = f"""
You are provided real estate configuration data as JSON.  
Process "Config price" data from a Google Sheet (identified by "Index" and "data_point_name"). The "99acres" value is the reference; compare it against "Comp 1/ C1," "Comp 2/ C2," and "Comp 3/ C3" for the same "Index" to generate matching scores.
Config price strings follow the format: "Configuration (ex- 2 BHK) & Property Type (ex- Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse) – Area Type (Carpet, Super area, Built up area) – Area (ex- 1850 sq ft, 700 sq mt) – Price (can be in Lacs/ Lakhs/ Lakh/ L or Crores/ Cr/ C)".
Details from "Configuration & Property Type- Area Type- Area" is called "Option Data".
Comparable cells will have multiple strings of data separated by "|".
In some data strings, Configuration might be missing for some property types; assume "Apartment" for Comp 1/ C1 when area type is absent but configuration exists.
In Comp 3 (C3), the data string may include two "area type-area" entries. In such cases, first check for a non-saleable area type (e.g., Carpet area, Built-up area). If the non-saleable area type in the comparable matches the reference, use that for comparison and scoring.
If no matching non-saleable area type is found, then compare the reference's "area type-area" with the Saleable area in the comparable for scoring purposes.
For example:
If the reference is "Carpet area - 1850 sq ft" and Comp 3 contains "Carpet area - 1850 sq ft - Saleable area - 2500 sq ft", compare the Carpet area values.
If the reference is "Carpet area - 1850 sq ft" and Comp 3 contains "Saleable area - 1850 sq ft - Saleable area - 1850 sq ft", compare the reference's Carpet area with the Saleable area in Comp 3, since no Carpet area is provided there.
       Task:
1. For each reference row, find a matching data string from each comparable source, by matching "Configuration & Property Type- Area Type- Area" in the same order, following the below mentioned conditions:
a) Configuration (2 BHK, 2.5 BHK, etc). If the configuration is in decimals, round it down to lower absolute number (ex- 3.5 BHK should be taken as 3 BHK)
b) Property Type (here, Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse)
c) Area Type (Carpet, Super area, Built up area)
d) Area (ex- 1850 sq ft, 700 sq mt). Standardize Area to sq ft before comparison. No variation in value of "area" is allowed. If "Area" value in reference and comparable is not an exact match, "Option Matching Score" would be "NA". The "Option Matching Score" would be 1 if "Option Data" in a comparable matches reference, 0 otherwise.
2. Then calculate "Price Matching Score" (1 if the price of the above matched string is +/- 5% of reference price, 0 if the comparable price is more than +/- 5% of reference price).
3. If price in Reference is "0", Sum of Price Matching Score would be "NA".
4. Calculate the variation in price in % for each comparable source (Comp 1, Comp 2, Comp 3) as V1, V2, V3 and it should be given for comparables which are present in comparable source else it should be NA. The variation is calculated as (Price of Reference - Price of Comparable)/Price of Reference * 100.
Comparable Rows are those comma separated data string/strings from each comparable row with which "Option Data" of reference value matches, from each Comparable Source in a single cell, Sum of Option Matching score, Sum of Price Matching score.
Give output of all comparables against a reference row in one row only. In Comparable Sources, give the name of only those sources against which a reference match was found.
Include those reference rows in the output where the Matching score of option is 0.
Give "NA" as output in Comparable source and Comparable row column, where there is no match against reference.
Do not give codes.
 
       Output Format:
       - Index
       - data_point_name
       - 99acres_value
       - Comparable Source (Comp 1, Comp 2, Comp 3)
       - Comparable Rows        
       - Sum of Option Matching score
       - Sum of Price Matching score
       - V1 (variation in % for Comp 1)
       - V2 (variation in % for Comp 2)
       - V3 (variation in % for Comp 3)
 
 
       Include rows where the Option Matching Score is 0. Do not include any additional text or explanation.
 
Here is the data:
{json.dumps(records)}
           """
 
           try:
               response_text = self.gemini_client.generate(prompt)
               print("Raw response:", response_text)
               json_data = self.extract_json_from_response(response_text)
           except Exception as e:
               print(f"Error during Gemini response processing: {e}")
               continue
 
           scores = []
           for entry in json_data:
               try:
# Safely handle non-numeric values for V1, V2, and V3
                   v1 = entry.get("V1", 0)
                   v2 = entry.get("V2", 0)
                   v3 = entry.get("V3", 0)
 
# Convert to numeric if possible, otherwise leave as-is
                   v1 = round(float(v1)) if isinstance(v1, (int, float)) or str(v1).replace('.', '', 1).isdigit() else v1
                   v2 = round(float(v2)) if isinstance(v2, (int, float)) or str(v2).replace('.', '', 1).isdigit() else v2
                   v3 = round(float(v3)) if isinstance(v3, (int, float)) or str(v3).replace('.', '', 1).isdigit() else v3
 
                   score = ConfigPriceScore(
                       index=entry.get("Index") or entry.get("index"),
                       data_point_name=entry.get("data_point_name") or entry.get("data_point_name"),
                       ref_value=entry.get("99acres_value") or entry.get("99acres") or "No 99acres value",
                       comparable_source=entry.get("comparable_source") or entry.get("Comparable Source") or "NA",
                       comparable_row=entry.get("comparable_row") or entry.get("Comparable Rows") or "NA",
                       option_matching_score=entry.get("option_matching_score") or entry.get("Sum of Option Matching score") or 0,
                       price_matching_score=entry.get("price_matching_score") or entry.get("Sum of Price Matching score") or 0,
                       v1=v1,
                       v2=v2,
                       v3=v3
                   )
                   scores.append(score)
               except Exception as e:
                   print(f"Error parsing entry: {entry}, error: {e}")
 
           self.write_config_price_scores(scores)
 
   def write_config_price_scores(self, scores: List[ConfigPriceScore]):
       if not scores:
           return
       all_sheet_data = self.sheet.get_all_records()
       updated_rows = []
 
       for i, row in enumerate(all_sheet_data):
           for score in scores:
               if row.get("Index") == score.index and row.get("99acres") == score.ref_value:
                   updated_rows.append((
                       i + 2,  # +2 because sheet is 1-indexed and header is row 1
                       [
                           score.ref_value,
                           score.comparable_source,
                           score.comparable_row,
                           score.option_matching_score,
                           score.price_matching_score,
                           score.v1,  # Variation for Comp 1
                           score.v2,  # Variation for Comp 2
                           score.v3   # Variation for Comp 3
                       ]
                   ))
 
       for row_num, values in updated_rows:
# Dynamically calculate the range based on the number of columns in `values`
           start_col = "G"
           end_col = chr(ord(start_col) + len(values) - 1)  # Calculate the ending column dynamically
           range_name = f"{start_col}{row_num}:{end_col}{row_num}"
           try:
               self.sheet.update(values=[values], range_name=range_name)
               print(f"Updated row {row_num}: {values}")
               time.sleep(1)
           except Exception as e:
               print(f"Failed to update row {row_num}: {e}")
 
# Google Sheets setup
SCOPES = [
   'https://www.googleapis.com/auth/spreadsheets',
   "https://spreadsheets.google.com/feeds",
   "https://www.googleapis.com/auth/drive"
]
 
creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("testconfig")
 
# Init Gemini client
gemini_client = GeminiClient(
   api_key="AIzaSyDEAog7IQdnC65ELQvV3tZq4p-KCmX5CPk",
   model_name="gemini-2.0-flash",
   generation_config={"temperature": 0.8}
)
 
processor = ConfigPriceProcessor(sheet, gemini_client)
processor.process_and_write_batches()
