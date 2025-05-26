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


# DataPointScore Model
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


# Gemini Client 
class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='gemini_prompts.json'):
      
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set or is empty.")

        self.__client = genai.Client(api_key=api_key)
        self.__model_name = model_name
        self.__prompt_path = prompt_path

    def __load_prompt(self, prompt_key: str) -> str:
        with open(self.__prompt_path, 'r') as file:
            data = json.load(file)
        return data.get(prompt_key, "")

    def get_scores(self, input_df: pd.DataFrame, data_point: str, instruction: str) -> List[DataPointScore]:
        prompt = self.__load_prompt("data_point_evaluator").format(instruction=instruction)

        contents = [
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

        print(f"Raw response for {data_point}: {raw_text}")

        # Validate JSON response
        if not raw_text:
            raise ValueError(f"Empty response received for data point: {data_point}")

        try:
            parsed_json = json.loads(raw_text)
            validated = []
            for item in parsed_json:
                try:
                    validated.append(DataPointScore(**item))
                except ValidationError as e:
                    print(f"Skipping invalid entry: {item}, error: {e}")
            return validated
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response for data point '{data_point}': {e}")
            raise

# Google Sheets Processor
class SheetDataProcessor:
    def __init__(self, sheet, gemini_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.client = gemini_client

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

if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file("fresh-circle-449810-r1-3b72a51ca318.json", scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("test2")

    client = GeminiClient()
    processor = SheetDataProcessor(sheet, client)

    with open("data_point_instructions.json", "r", encoding="utf-8") as file:
        instructions = json.load(file)

    # Process each data point as per the instructions
    for dp, rule in instructions.items():
        print(f"Processing: {dp}")
        try:
            scores = processor.process_data_point(dp, rule)
            if scores:
                processor.write_scores(scores)
        except Exception as e:
            print(f"Error in {dp}: {e}")
