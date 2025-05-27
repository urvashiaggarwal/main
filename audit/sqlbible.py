import os
import json
import mysql.connector
import pandas as pd
from pydantic import BaseModel
from typing import Union, List
from google import genai
from google.genai import types
import dotenv

dotenv.load_dotenv()

# Pydantic model 
class DataPointScore(BaseModel):
    data_point_name: str
    index: int
    score: int


#Gemini Client
class GeminiClient:
    def __init__(self, model_name='gemini-2.5-flash-preview-04-17', prompt_path='bible_prompts.json'):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
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

        if not raw_text:
            raise ValueError(f"Empty response for {data_point}")

        try:
            parsed = json.loads(raw_text)
            return [DataPointScore(**item) for item in parsed]
        except Exception as e:
            print(f"Validation failed: {e}")
            raise


# MySQL Processor
class MySQLProcessor:
    def __init__(self, gemini_client):
        self.client = gemini_client
        self.conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            connection_timeout=5,
            use_pure=True
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def fetch_unscored_rows(self, data_point_name):
        query = """
            SELECT * FROM bible_data
            WHERE data_point_name = %s AND is_scored = 0
        """
        self.cursor.execute(query, (data_point_name,))
        return self.cursor.fetchall()

    def update_scores(self, results: List[DataPointScore]):
        for r in results:
            update_query = """
                UPDATE bible_data
                SET score = %s,  is_scored = 1
                WHERE index_value = %s AND data_point_name = %s
            """
            self.cursor.execute(update_query, (
                r.score,
                r.index,
                r.data_point_name
            ))
            self.conn.commit()

    def process_data_point(self, data_point, instruction):
        rows = self.fetch_unscored_rows(data_point)
        if not rows:
            return
        df = pd.DataFrame(rows)
        results = self.client.get_scores(df, data_point, instruction)
        self.update_scores(results)


if __name__ == "__main__":
    client = GeminiClient()
    processor = MySQLProcessor(client)
    with open("bible_instructions.json", "r", encoding="utf-8") as file:
        instructions = json.load(file)

    for dp, rule in instructions.items():
        print(f"Processing: {dp}")
        try:
            processor.process_data_point(dp, rule)
        except Exception as e:
            print(f"Error processing {dp}: {e}")


