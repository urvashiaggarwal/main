import gspread
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time


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


class DataPointScore(BaseModel):
    index: int
    data_point_name: str
    matching_score: int


class SheetDataProcessor:
    def __init__(self, sheet, gemini_client: GeminiClient):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.gemini_client = gemini_client

    def extract_json_from_response(self, response_text: str):
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.removeprefix("```json").removesuffix("```").strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print("Error parsing JSON:", e)
            print("Raw response:", response_text)

            try:
                start_index = response_text.find("[")
                if start_index == -1:
                    print("No JSON array found in response.")
                    return []

                partial_json = response_text[start_index:]
                partial_json = partial_json.rstrip(",")  
                partial_json += "]"  

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
            print(f"No unscored rows found for {data_point_name}. Skipping.")
            return []

        data_records = filtered_df.to_dict(orient='records')
        prompt = f"""
We will provide you data in the form of a Json in which 'Index' is the unique identifier.
'data_point_name' is the header of the values, and the data has been fetched from different sources: 99acres, Primary Source, and Secondary Source.
The first value in every row is the reference value (ref) from 99acres, and the following 2 values are comparables from the other sources.

Specific instructions for this data point are:
{instruction}

Also calculate:
- Matching score = number of data points that match between the reference and comparables.

Return a JSON list with:
- index
- data_point_name
- matching_score

Ensure the JSON is complete and properly formatted. Do not include markdown, code fences, or explanation.
Here is the data:
{data_records}
"""
        response_text = self.gemini_client.generate(prompt)
        json_data = self.extract_json_from_response(response_text)

        valid_data = []
        for entry in json_data:
            if all(key in entry for key in ["index", "data_point_name", "matching_score"]):
                valid_data.append(entry)
            else:
                print(f"Incomplete or invalid entry detected and skipped: {entry}")

        return [DataPointScore(**entry) for entry in valid_data]

    def write_scores_to_sheet(self, scores: List[DataPointScore]):
        headers = self.sheet.row_values(1)
        records = self.sheet.get_all_records()

        try:
            score_col = headers.index("score") + 1
        except ValueError as e:
            print("Column not found in sheet headers:", e)
            return

        row_map = {
            (record["Index"], record["data_point_name"]): idx + 2
            for idx, record in enumerate(records)
        }

        for result in scores:
            key = (result.index, result.data_point_name)
            row_num = row_map.get(key)
            if row_num:
                self.sheet.update_cell(row_num, score_col, result.matching_score)
                time.sleep(1)
            else:
                print(f"Row not found for index {result.index} and data_point_name {result.data_point_name}")


# Initialize Google Sheets connection
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("bible_new")

# Initialize Gemini client
gemini_client = GeminiClient(
    api_key="AIzaSyDEAog7IQdnC65ELQvV3tZq4p-KCmX5CPk",
    model_name="gemini-2.0-flash",
    generation_config={
        # "temperature": 
        # "top_k": 40,
        # "top_p": 0.9
    }
)

# Initialize SheetDataProcessor
processor = SheetDataProcessor(sheet, gemini_client)

# Load prompts from JSON file
with open("bible_instructions.json", "r", encoding="utf-8") as file:
    data_point_instructions = json.load(file)

# Process each data point and generate matching scores
all_scores = []
for dp_name, rule in data_point_instructions.items():
    print(f"\nProcessing: {dp_name}")
    try:
        scores = processor.process_data_point(dp_name, rule)
        if scores:
            processor.write_scores_to_sheet(scores)
            all_scores.extend(scores)
    except Exception as e:
        print(f"Error processing {dp_name}: {e}")

# Optionally: output all scores as a DataFrame
df_scores = pd.DataFrame([score.dict() for score in all_scores])
df_scores.to_csv("output_matching_scores.csv", index=False)
print("Matching scores have been saved to 'output_matching_scores.csv'.")
