import gspread
import json
import re
import time
import pandas as pd
from typing import List, Union, Optional, Dict, Any
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
import google.generativeai as genai

#llm is not wrong the way we are calling it is wrong
# send in form of rows according to data frame
#read gemini models class
#json define here
#part from text to json
#define client after this,only define api key and model name ,generation config not here
#use json.loads to load json data
class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash",
        generation_config: Optional[Dict[str, Any]] = None
    ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )

    def generate(self, prompt: str, custom_config: Optional[Dict[str, Any]] = None) -> str:
        response = self.model.generate_content([prompt], generation_config=custom_config)
        return response.text


# Pydantic model for structured response
class DataPointScore(BaseModel):
    data_point_name: str
    index: int
    score: int
    den: int
    consensus_value: Union[str, int, None]
    consensus_score: int

    @property
    def consensus_value_str(self):
        return str(self.consensus_value) if self.consensus_value is not None else ""


# Main processor class
class SheetDataProcessor:
    def __init__(self, sheet, gemini_client: GeminiClient):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.gemini_client = gemini_client

    def extract_json_from_response(self, response_text: str):
        try:
        # Remove code block formatting if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()

            # Attempt to parse the cleaned JSON
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            print("Raw response:", response_text)

            # Attempt to recover from incomplete JSON
            try:
                # Find the start of the JSON array
                start_index = response_text.find("[")
                if start_index == -1:
                    print("No JSON array found in response.")
                    return []

                # Extract the valid portion of the JSON array
                partial_json = response_text[start_index:]
                partial_json = partial_json.rstrip(",")  # Remove trailing commas
                partial_json += "]"  # Close the JSON array

                # Parse the partial JSON
                return json.loads(partial_json)
            except Exception as recovery_error:
                print("Recovery failed:", recovery_error)
                return []

    def process_data_point(self, data_point_name: str, instruction: str) -> List[DataPointScore]:
        filtered_df = self.df[
            (self.df['data_point_name'] == data_point_name) &
            (
                self.df['score'].isna() |
                self.df['score'].astype(str).isin(['', 'N/A', 'NA'])
            )
        ]
        if filtered_df.empty:
            print(f" No unscored rows found for {data_point_name}. Skipping.")
            return []

        data_records = filtered_df.to_dict(orient='records')
        system_instructions = """
    We will provide you data in the form of a JSON in which 'index' is the unique identifier.
    'data_point_name' is the header of the values, and the data has been fetched from different sources: 99acres, Comp 1, Comp 2, Comp 3.
    The first value in every row is the reference value (ref) from 99acres. The following 3 values are comparables from the other sources.

    Specific instructions for this data point are:
    {instruction}

    Also calculate:
    - Den = count of valid comparables (not NA)
    - Consensus value = mode value among comparables
    - Consensus score = times consensus value appears

    Return a JSON list with:
    - data_point_name
    - index
    - score
    - den
    - consensus_value
    - consensus_score

    Ensure the JSON is complete and properly formatted. Do not include markdown, code fences, or explanation.
    """
        
        #contents send data,prompt send specific instruction and system instruction whole 
        prompt = system_instructions.format(instruction=instruction) + f"\nHere is the data:\n{data_records}"
        response_text = self.gemini_client.generate(prompt)
        json_data = self.extract_json_from_response(response_text)

        # Validate and filter incomplete or invalid entries
        valid_data = []
        for entry in json_data:
            # Provide default values for invalid fields
            if isinstance(entry.get("score"), str) and entry["score"].strip() == "":
                entry["score"] = 0  # Default score to 0 if it's an empty string
            entry.setdefault("den", 0)  # Default den to 0 if missing
            entry.setdefault("consensus_value", None)  # Default consensus_value to None
            entry.setdefault("consensus_score", 0)  # Default consensus_score to 0

            # Validate required fields
            if all(
                key in entry and entry[key] not in [None, "", "N/A", "NA"]
                for key in ["thoughts", "data_point_name", "index", "score", "den", "consensus_value", "consensus_score"]
            ):
                valid_data.append(entry)
            else:
                print(f"Incomplete or invalid entry detected and skipped: {entry}")

        # Convert valid entries to DataPointScore objects
        return [DataPointScore(**entry) for entry in valid_data]

    def write_scores_to_sheet(self, scores: List[DataPointScore]):
        headers = self.sheet.row_values(1)
        records = self.sheet.get_all_records()

        try:
            score_col = headers.index("score") + 1
            den_col = headers.index("den") + 1
            consensus_col = headers.index("consensus_value") + 1
            consensus_col_score = headers.index("consensus_score") + 1
        except ValueError as e:
            print(" Column not found in sheet headers:", e)
            return

        row_map = {
            (record["Index"], record["data_point_name"]): idx + 2
            for idx, record in enumerate(records)
        }

        for result in scores:
            key = (result.index, result.data_point_name)
            row_num = row_map.get(key)
            if row_num:
                self.sheet.update_cell(row_num, score_col, result.score)
                time.sleep(1)
                self.sheet.update_cell(row_num, den_col, result.den)
                time.sleep(1)
                self.sheet.update_cell(row_num, consensus_col, result.consensus_value_str)
                time.sleep(1)
                self.sheet.update_cell(row_num, consensus_col_score, result.consensus_score)
                time.sleep(1)
            else:
                print(f" Row not found for index {result.index} and data_point_name {result.data_point_name}")



SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("92test")

# Init Gemini client
gemini_client = GeminiClient(
    api_key="AIzaSyCwBsHGSRiV-RUEWIfgqaU_4l6VvRJTOYc",
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 0.8,
        "top_k": 40,
        "top_p": 0.9
       #response mime type define here 
    }
)

# Init processor
processor = SheetDataProcessor(sheet, gemini_client)


# Load data point instructions from JSON file
with open("data_point_instructions.json", "r", encoding="utf-8") as file:
    data_point_instructions = json.load(file)

# Process each data point
all_scores = []
for dp_name, rule in data_point_instructions.items():
    print(f"\n Processing: {dp_name}")
    try:
        scores = processor.process_data_point(dp_name, rule)
        if scores:
            processor.write_scores_to_sheet(scores)
            all_scores.extend(scores)
    except Exception as e:
        print(f" Error processing {dp_name}: {e}")
