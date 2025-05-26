from pydantic import BaseModel, ValidationError
from typing import Union, List
import os
import json
import time
import pandas as pd
import requests
import dotenv
import gspread
from google.oauth2.service_account import Credentials
import re

# Pydantic model
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


# OpenAI-compatible Client
class OpenAIClient:
    def __init__(self, endpoint: str, prompt_path: str = 'gemini_prompts.json'):
        self.endpoint = endpoint
        self.prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.prompt_path, 'r') as file:
            data = json.load(file)
        return data.get(prompt_key, "")

    def get_scores(self, input_df: pd.DataFrame, data_point: str, instruction: str) -> List[DataPointScore]:
        prompt = self.__load_prompt("data_point_evaluator").format(instruction=instruction)

        payload = {
            "model": "gpt-4o-mini",
            "keyType": "MINI",
            "temperature": 0.8,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_df.to_json(orient='records')}
            ]
        }

        try:
            response = requests.post(self.endpoint, json=payload)
            response.raise_for_status()
            raw_json = response.json()

            print(f"Raw response for {data_point}: {raw_json}")

            #Handle the "result" string case
            if isinstance(raw_json, dict) and "result" in raw_json:
                result_str = raw_json["result"]
                result_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_str.strip(), flags=re.IGNORECASE)
                parsed = json.loads(result_str)
            elif isinstance(raw_json, list):
                parsed = raw_json
            elif isinstance(raw_json, dict) and "choices" in raw_json:
                parsed = json.loads(raw_json["choices"][0]["message"]["content"])
            else:
                raise ValueError("Expected a list in response")

            validated = []
            for item in parsed:
                try:
                    validated.append(DataPointScore(**item))
                except ValidationError as e:
                    print(f"Skipping invalid entry: {item}, error: {e}")
            return validated
        except Exception as e:
            print(f"Error querying model for '{data_point}': {e}")
            return []

# Sheet Processor 
class SheetDataProcessor:
    def __init__(self, sheet, llm_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.client = llm_client

    def process_data_point(self, data_point_name, instruction) -> List[DataPointScore]:
        unscored_df = self.df[(self.df["data_point_name"] == data_point_name) &
                              (self.df["score"].astype(str).isin(["", "NA", "N/A"]))]
        if unscored_df.empty:
            return []

        return self.client.get_scores(unscored_df, data_point_name, instruction)

    def write_scores(self, results: List[DataPointScore]):
        headers = self.sheet.row_values(1)
        records = self.sheet.get_all_records()
        row_map = {(r["Index"], r["data_point_name"]): i + 2 for i, r in enumerate(records)}

        col_map = {
            "score": headers.index("score") + 1,
            "den": headers.index("den") + 1,
            "consensus_value": headers.index("consensus_value") + 1,
            "consensus_score": headers.index("consensus_score") + 1,
        }

        for r in results:
            row = row_map.get((r.index, r.data_point_name))
            if row:
                self.sheet.update_cell(row, col_map["score"], r.score)
                time.sleep(1)
                self.sheet.update_cell(row, col_map["den"], r.den)
                time.sleep(1)
                self.sheet.update_cell(row, col_map["consensus_value"], r.consensus_value_str)
                time.sleep(1)
                self.sheet.update_cell(row, col_map["consensus_score"], r.consensus_score)
                time.sleep(1)


# Main execution
if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file("fresh-circle-449810-r1-3b72a51ca318.json", scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("Sheet22")

    endpoint = "http://new99acresposting:6009/api/analyze"
    client = OpenAIClient(endpoint=endpoint)
    processor = SheetDataProcessor(sheet, client)

    with open("data_point_instructions.json", "r", encoding="utf-8") as file:
        instructions = json.load(file)

    for dp, rule in instructions.items():
        print(f"Processing: {dp}")
        try:
            scores = processor.process_data_point(dp, rule)
            if scores:
                processor.write_scores(scores)
        except Exception as e:
            print(f"Error in {dp}: {e}")
