from pydantic import BaseModel, ValidationError
from typing import Union, List
import os
import json
import time
import pandas as pd
from google import genai
from google.genai import types
import dotenv
import gspread
from google.oauth2.service_account import Credentials


# Pydantic model
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


class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='config_prompts.json'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set or is empty.")
        self.__client = genai.Client(api_key=api_key)
        self.__model_name = model_name
        self.__prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.__prompt_path, 'r') as file:
            data = json.load(file)
        if prompt_key not in data:
            raise KeyError(f"Prompt key '{prompt_key}' not found in prompt file.")
        return data[prompt_key]

    def get_scores(self, input_df: pd.DataFrame) -> List[ConfigPriceScore]:

        prompt = self.__load_prompt("data_point_evaluator")

        contents = [
            types.Content(role="user", parts=[
                types.Part(text=input_df.to_json(orient='records'))
            ])
        ]

        config = types.GenerateContentConfig(
            temperature=0.8,
            response_mime_type="application/json",
            system_instruction=[types.Part(text=prompt)],
            response_schema=list[ConfigPriceScore]
        )

        response = self.__client.models.generate_content(
            model=self.__model_name,
            contents=contents,
            config=config
        )

        raw_text = response.candidates[0].content.parts[0].text.strip()
        print(f"Raw response:\n{raw_text}")

        if not raw_text:
            print("Gemini returned an empty response for this batch. Skipping.")
            return []

        try:
            parsed_json = json.loads(raw_text)
            validated = []
            for item in parsed_json:
                try:
                    validated.append(ConfigPriceScore(**item))
                except ValidationError as e:
                    print(f"Skipping invalid entry: {item}, error: {e}")
            return validated
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            raise


class SheetDataProcessor:
    def __init__(self, sheet, gemini_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.gemini_client = gemini_client

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
                scores = self.gemini_client.get_scores(batch_df)
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


if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(
        "fresh-circle-449810-r1-3b72a51ca318.json", scopes=SCOPES
    )
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("testconfig")

    client = GeminiClient()
    processor = SheetDataProcessor(sheet, client)
    processor.process_batches()
