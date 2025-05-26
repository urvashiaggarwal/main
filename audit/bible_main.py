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


# Pydantic model for output validation
class DataPointScore(BaseModel):
    index: int
    data_point_name: str
    matching_score: Union[int, str]


class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='bible_prompts.json'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set or is empty.")


        # Initialize the genai.Client with the API key
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
            system_instruction=[types.Part.from_text(text=prompt)],
            response_schema=list[DataPointScore]
        )

        # Generate content
        response = self.__client.models.generate_content(
            model=self.__model_name,
            contents=contents,
            config=config
        )

        raw_text = response.candidates[0].content.parts[0].text.strip()

        # Validate and parse the JSON response
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


# Sheet processor class
class SheetDataProcessor:
    def __init__(self, sheet, gemini_client):
        self.sheet = sheet
        self.df = pd.DataFrame(sheet.get_all_records())
        self.client = gemini_client

    def process_data_point(self, data_point_name, instruction) -> List[DataPointScore]:
            # Filtering data for data point and where score is missing or NA
            unscored_df = self.df[(self.df["data_point_name"] == data_point_name) & 
                                (self.df["score"].astype(str).isin([""]))]
            if unscored_df.empty:
                return []

            return self.client.get_scores(unscored_df, data_point_name, instruction)
    
    def write_scores(self, results: List[DataPointScore]):
        headers = self.sheet.row_values(1)
        records = self.sheet.get_all_records()
        row_map = {(r["Index"], r["data_point_name"]): i + 2 for i, r in enumerate(records)}

        col_map = {
            "score": headers.index("score") + 1
        }

        for r in results:
            row = row_map.get((r.index, r.data_point_name))
            if row:
                self.sheet.update_cell(row, col_map["score"], r.matching_score)
                time.sleep(1)

if __name__ == "__main__":
    dotenv.load_dotenv()

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(os.getenv("SHEET_ID")).worksheet("Sheet21")

    client = GeminiClient()
    processor = SheetDataProcessor(sheet, client)

    with open("bible_instructions.json", "r", encoding="utf-8") as f:
        instructions = json.load(f)

        for dp, rule in instructions.items():
            print(f"Processing: {dp}")
            try:
                scores = processor.process_data_point(dp, rule)
                if scores:
                    processor.write_scores(scores)
            except Exception as e:
                print(f"Error in {dp}: {e}")
