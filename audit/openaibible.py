from pydantic import BaseModel, ValidationError
from typing import Union, List
import os
import json
import time
import pandas as pd
import dotenv
import gspread
import requests
from google.oauth2.service_account import Credentials


# Pydantic model 
class DataPointScore(BaseModel):
    index: int
    data_point_name: str
    matching_score: Union[int, str]

class OpenAIClient:
    def __init__(self, endpoint_url: str, prompt_path='bible_prompts.json'):
        self.endpoint_url = endpoint_url
        self.prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.prompt_path, 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data.get(prompt_key, "")

    def get_scores(self, input_df: pd.DataFrame, data_point: str, instruction: str) -> List[DataPointScore]:

        prompt = self.__load_prompt("data_point_evaluator").format(instruction=instruction)

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_df.to_json(orient='records')}
        ]

        # API payload
        payload = {
            "messages": messages,
            "temperature": 0.8,
            "keyType": "MINI"  
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.endpoint_url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            print(f"Raw response for {data_point}: {json.dumps(result, indent=2)}")

            if isinstance(result, dict) and "result" in result:
                parsed = json.loads(result["result"])
            elif isinstance(result, list):
                parsed = result
            elif isinstance(result, dict) and "choices" in result:
                parsed = json.loads(result["choices"][0]["message"]["content"])
            else:
                raise ValueError("Unexpected response format")

            validated = []
            for item in parsed:
                try:
                    validated.append(DataPointScore(**item))
                except ValidationError as e:
                    print(f"Skipping invalid entry: {item}, error: {e}")
            return validated

        except Exception as e:
            print(f"Error in API request for '{data_point}': {e}")
            return []


# Sheet processor class
class SheetDataProcessor:
    def __init__(self, sheet, llm_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.client = llm_client

    def process_data_point(self, data_point_name, instruction) -> List[DataPointScore]:
        # Filter unscored rows for the current data point
        unscored_df = self.df[
            (self.df["data_point_name"] == data_point_name) &
            (self.df["score"].astype(str).isin(["", "NA", "N/A"]))
        ]
        if unscored_df.empty:
            print(f"No unscored rows for: {data_point_name}")
            return []

        return self.client.get_scores(unscored_df, data_point_name, instruction)

    def write_scores(self, results: List[DataPointScore]):
        headers = self.sheet.row_values(1)
        records = self.sheet.get_all_records()

        row_map = {(r["Index"], r["data_point_name"]): i + 2 for i, r in enumerate(records)}
        col_map = {"score": headers.index("score") + 1}

        for r in results:
            row = row_map.get((r.index, r.data_point_name))
            if row:
                try:
                    self.sheet.update_cell(row, col_map["score"], r.matching_score)
                    print(f"Updated score for index {r.index}, {r.data_point_name}: {r.matching_score}")
                    time.sleep(1)
                except Exception as e:
                    print(f"Failed to update row {row}: {e}")


# Main execution
if __name__ == "__main__":
    dotenv.load_dotenv()

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("Sheet22")

    custom_endpoint = "http://new99acresposting:6009/api/analyze"

    client = OpenAIClient(endpoint_url=custom_endpoint)
    processor = SheetDataProcessor(sheet, client)

    with open("bible_instructions.json", "r", encoding="utf-8") as f:
        instructions = json.load(f)

    for dp, rule in instructions.items():
        print(f"\nProcessing: {dp}")
        try:
            scores = processor.process_data_point(dp, rule)
            if scores:
                processor.write_scores(scores)
        except Exception as e:
            print(f"Error in {dp}: {e}")
