from pydantic import BaseModel, ValidationError
from typing import Union, List
import os
import json
import time
import pandas as pd
from google import genai
from google.genai import types
import dotenv
import mysql.connector


# Pydantic model
class ConfigPriceScore(BaseModel):
    index: int
    data_point_name: str
    ref_value: str
    comparable_row: str
    option_matching_score: int
    price_matching_score: int

class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='config_prompts_bible.json'):
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


class MySQLConfigProcessor:
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            connection_timeout=5,
            use_pure=True
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def fetch_unscored_rows(self):
        query = """
            SELECT * FROM bible_config_data
            WHERE `option_matching_score` IS NULL 
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def update_config_price_scores(self, scores: List[ConfigPriceScore]):
        if not scores:
            return

        for score in scores:
            update_query = """
                UPDATE bible_config_data
                SET comparable_row = %s,
                    option_matching_score = %s,
                    price_matching_score = %s
                WHERE `index` = %s AND data_point_name = %s and 99acres = %s
            """
            try:
                self.cursor.execute(update_query, (
                    score.comparable_row,
                    score.option_matching_score,
                    score.price_matching_score,
                    score.index,
                    score.data_point_name,
                    score.ref_value
                ))
                self.conn.commit()
                print(f"Updated row with index {score.index}: {score.ref_value}")
            except Exception as e:
                print(f"Failed to update row with index {score.index}: {e}")
                self.conn.rollback()

    def process_batches(self) -> List[ConfigPriceScore]:
        unscored_rows = self.fetch_unscored_rows()
        
        if not unscored_rows:
            print("No unscored rows found.")
            return []

        unscored_df = pd.DataFrame(unscored_rows)
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
                    self.update_config_price_scores(scores)
                    all_scores.extend(scores)
            except Exception as e:
                print(f"Error processing batch {start}-{start + batch_size}: {e}")

        return all_scores

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close_connection()


if __name__ == "__main__":
    dotenv.load_dotenv(".env")

    try:
        client = GeminiClient()
        with MySQLConfigProcessor(client) as processor:
            processor.process_batches()
    except Exception as e:
        print(f"Error in main execution: {e}")