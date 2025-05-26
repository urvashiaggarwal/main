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

    def process_and_write_batches(self):
        grouped = self.df.groupby("Index")
        for index_value, group_df in grouped:
            print(f"Processing Index: {index_value}")
            records = group_df.to_dict(orient='records')

            prompt = f"""
        You are provided real estate configuration data as JSON.  
        Process "Config price" data from a Google Sheet (identified by "Index" and "data_point_name"). The "99acres" value is the reference; compare it against "Bible" for the same "Index" to generate matching scores.
        Config price strings follow the format: "Configuration (ex- 2 BHK) & Property Type (ex- Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse) – Area Type (Carpet, Super area, Built up area) – Area (ex- 1850 sq ft, 700 sq mt) – Price (can be in Lacs/ Lakhs/ Lakh/ L or Crores/ Cr/ C)".
        Details from "Configuration & Property Type- Area Type- Area" is called "Option Data".

        Comparable cells can have multiple strings. Each row will have multiple strings of data separated by "|".
        Configuration might be missing for some property types; assume "Apartment" for Bible when area type is absent but configuration exists.

        Task:
        1. For each reference row, find a matching data string from the Bible field, by matching "Configuration & Property Type- Area Type- Area" in the same order, following the below mentioned conditions:
        a) Configuration (2 BHK, 3 BHK, etc). If the configuration is in decimals, round it down to lower absolute number (ex- 3.5 BHK should be taken as 3 BHK)
        b) Property Type (Note the below to be synonyms- Apartment=Flat; Villa; Plot=Residential Plot=Land; Studio Apartment=Studio=1 RK; Retail Shop=Shop; Penthouse)
        c) Area Type (Carpet, Super area, Built up area)
        d) Area (ex- 1850 sq ft, 700 sq mt). Standardize Area to sq ft before comparison. Give a matching score of 0 even if the "Area" value in reference and comparable differ by +/-1.
        The above will give you "Option Matching Score" (1 if "Option Data" in a comparable matches reference, 0 otherwise)
        2. Then calculate "Price Matching Score" (1 if the price of the above matched string is +/- 5% of reference price, 0 otherwise).
        3. Give "0" as Sum of Price Matching Score where the price in Reference is "0".
        Comparable Rows (comma separated data string from the Bible field with which reference value matches), Sum of Option Matching score, Sum of Price Matching score. 
        Include those reference rows in the output where the Matching score of option is 0. 
        Give "NA" as output in Comparable row column, where there is no match against reference.
        Do not give codes.

        Output Format:
        - Index
        - data_point_name
        - 99acres_value
        - Comparable Rows (from Bible field)
        - Sum of Option Matching score
        - Sum of Price Matching score

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
                    score = ConfigPriceScore(
                        index=entry.get("Index") or entry.get("index"),
                        data_point_name=entry.get("data_point_name") or entry.get("data_point_name"),
                        ref_value=entry.get("99acres_value") or entry.get("99acres") or "No 99acres value",
                        comparable_source="Bible",  # Fixed to "Bible"
                        comparable_row=entry.get("comparable_row") or entry.get("Comparable Rows") or "NA",
                        option_matching_score=entry.get("option_matching_score") or entry.get("Sum of Option Matching score") or 0,
                        price_matching_score=entry.get("price_matching_score") or entry.get("Sum of Price Matching score") or 0
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
                            score.comparable_row,  # Only Bible rows
                            score.option_matching_score,
                            score.price_matching_score
                        ]
                    ))

        for row_num, values in updated_rows:
            range_name = f"G{row_num}:J{row_num}"  # Adjusted range for fewer columns
            try:
                self.sheet.update(values=[values], range_name=range_name)
                print(f"Updated row {row_num}: {values}")
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
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("config")

# Init Gemini client
gemini_client = GeminiClient(
    api_key="AIzaSyDEAog7IQdnC65ELQvV3tZq4p-KCmX5CPk",
    model_name="gemini-2.0-flash",
    generation_config={"temperature": 0.8}
)

processor = ConfigPriceProcessor(sheet, gemini_client)
processor.process_and_write_batches()
