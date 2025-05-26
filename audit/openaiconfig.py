from pydantic import BaseModel, ValidationError
from typing import Union, List
import os
import json
import time
import pandas as pd
import dotenv
import requests
import gspread
from google.oauth2.service_account import Credentials

class ConfigPriceScore(BaseModel):
    index: int
    data_point_name: str
    ref_value: str
    comparable_source: str
    comparable_row: str
    option_matching_score: int
    price_matching_score: int
    v1: Union[float, str] = 0.0
    v2: Union[float, str] = 0.0
    v3: Union[float, str] = 0.0


class CustomGPTClient:
    def __init__(self, endpoint_url: str, prompt_path='config_prompts.json'):
        self.endpoint_url = endpoint_url
        self.prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.prompt_path, 'r') as file:
            data = json.load(file)
        if prompt_key not in data:
            raise KeyError(f"Prompt key '{prompt_key}' not found in prompt file.")
        return data[prompt_key]

    def get_scores(self, input_df: pd.DataFrame) -> List[ConfigPriceScore]:
        system_instruction = self.__load_prompt("data_point_evaluator")
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": input_df.to_json(orient="records")}
        ]

        payload = {
            "messages": messages,
            "temperature": 0.8,
            "keyType": "MINI"
        }

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(self.endpoint_url, headers=headers, json=payload)
            response.raise_for_status()
            raw_text = response.json()

            print(f"Raw response:\n{json.dumps(raw_text, indent=2)}")

            # --- Handle the "result" string case ---
            if isinstance(raw_text, dict) and "result" in raw_text:
                parsed_json = json.loads(raw_text["result"])
            elif isinstance(raw_text, list):
                parsed_json = raw_text
            elif isinstance(raw_text, dict) and "choices" in raw_text:
                parsed_json = json.loads(raw_text["choices"][0]["message"]["content"])
            else:
                raise ValueError("Unexpected response format.")

            validated = []
            for item in parsed_json:
                try:
                    mapped_item = map_api_keys_to_model_keys(item)
                    validated.append(ConfigPriceScore(**mapped_item))
                except ValidationError as e:
                    print(f"Skipping invalid entry: {item}, error: {e}")
            return validated

        except Exception as e:
            print(f"Custom GPT API error: {e}")
            return []


class SheetDataProcessor:
    def __init__(self, sheet, llm_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.llm_client = llm_client

    def process_batches(self) -> List[ConfigPriceScore]:
        unscored_df = self.df[self.df["Sum-of_option_matching_score"].astype(str).isin(["", "NA", "N/A"])]
        if unscored_df.empty:
            print("No unscored rows found.")
            return []

        batch_size = 2
        all_scores = []

        for start in range(0, len(unscored_df), batch_size):
            batch_df = unscored_df.iloc[start:start + batch_size]
            print(f"Processing batch {start}-{start + batch_size} with {len(batch_df)} rows.")
            if batch_df.empty:
                continue
            try:
                scores = self.llm_client.get_scores(batch_df)
                if scores:
                    self.write_config_price_scores(scores)
                    all_scores.extend(scores)
            except Exception as e:
                print(f"Error processing batch {start}-{start + batch_size}: {e}")

        return all_scores

    def write_config_price_scores(self, scores: List[ConfigPriceScore]):
        if not scores:
            return

        all_sheet_data = self.sheet.get_all_records()
        updated_rows = []

        for i, row in enumerate(all_sheet_data):
            for score in scores:
                if int(row.get("Index", -1)) == score.index and row.get("99acres") == score.ref_value:
                    updated_rows.append((
                        i + 2,
                        [
                            score.ref_value,
                            score.comparable_source,
                            score.comparable_row,
                            score.option_matching_score,
                            score.price_matching_score,
                            score.v1,
                            score.v2,
                            score.v3
                        ]
                    ))

        for row_num, values in updated_rows:
            start_col = "G"
            end_col = chr(ord(start_col) + len(values) - 1)
            range_name = f"{start_col}{row_num}:{end_col}{row_num}"
            try:
                self.sheet.update(values=[values], range_name=range_name)
                print(f"Updated row {row_num}: {values}")
                time.sleep(1)
            except Exception as e:
                print(f"Failed to update row {row_num}: {e}")


def map_api_keys_to_model_keys(item):
    return {
        "index": item.get("Index"),
        "data_point_name": item.get("data_point_name"),
        "ref_value": item.get("99acres"),
        "comparable_source": item.get("Comparable Source"),
        "comparable_row": item.get("Comparable Rows"),
        "option_matching_score": item.get("Sum of Option Matching Score"),
        "price_matching_score": item.get("Sum of Price Matching Score"),
        "v1": item.get("V1"),
        "v2": item.get("V2"),
        "v3": item.get("V3"),
    }


if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(
        "fresh-circle-449810-r1-3b72a51ca318.json", scopes=SCOPES
    )
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("Sheet22")

    endpoint = "http://new99acresposting:6009/api/analyze"
    client = CustomGPTClient(endpoint_url=endpoint)
    processor = SheetDataProcessor(sheet, client)
    processor.process_batches()
