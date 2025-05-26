import gspread
from google.oauth2.service_account import Credentials
from pydantic import BaseModel
from typing import List, Union
import pandas as pd
import re
import json
import google.generativeai as genai
import time


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1ydIkGOMUGesNd4tiM7ZH9SRObGoaJShYxDt_1mxUZyU").worksheet("92 data")

df = pd.DataFrame(sheet.get_all_records())

genai.configure(api_key="AIzaSyCwBsHGSRiV-RUEWIfgqaU_4l6VvRJTOYc")
model = genai.GenerativeModel("gemini-2.0-flash")


class DataPointScore(BaseModel):
    data_point_name: str
    index: int
    score: int
    den: int
    consensus_value: Union [str,int,None] 
    consensus_score: int

    @property
    def consensus_value_str(self):
        return str(self.consensus_value) if self.consensus_value is not None else ""


def extract_json_from_response(response_text: str):
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


def process_data_point(df: pd.DataFrame, model, data_point_name: str, instruction: str) -> List[DataPointScore]:
    filtered_df = df[
        (df['data_point_name'] == data_point_name) &
        (
            df['score'].isna() |
            df['score'].astype(str).isin(['', 'N/A', 'NA'])
        )
    ]

    if filtered_df.empty:
        print(f" No unscored rows found for {data_point_name}. Skipping.")
        return []

    data_records = filtered_df.to_dict(orient='records')

    prompt = f"""
We will provide you data in the form of a json in which Index will be the unique identifier.
data_point_name is the header of the values and the data has been fetched from different sources, namely 99acres, Comp 1, Comp 2, Comp 3.
The first data point in every row is the reference value (called ref value) the source of which is 99acres which needs to be compared against the following 3 data points in the same row (called comparables) which is the data sourced from Comp 1, Comp 2, Comp 3 to generate a matching score.
Matching score is the number of data points to which the first data point matches.
Matches can be exact or approximate.

If a particular comparable is 'Not Available or N/A or NA', then the match against the value should be ignored
If a ref value is 'Not Available or N/A or NA', then match is 0. 

Please produce a matching score for each of the data points.

Specific instructions for this data point are:
{instruction}

Also calculate a value called Den. Den is count of all comparables (data sourced from Comp 1, Comp 2, Comp 3) which are not "Not Available, N/A, Not found or NA".
Consensus value is the mode value among the comparables.
Consensus score is the number of times Consensus value occurs in the comparables.

Give the output as a JSON list with:
- data_point_name
- index
- score
- den
- consensus_value
- consensus_score

Here is the data:
{data_records}
"""
    response = model.generate_content([prompt])  # Generate content using the model
    json_data = extract_json_from_response(response.text)  # Use the updated function
    return [DataPointScore(**entry) for entry in json_data]


def write_scores_to_sheet(sheet, scores: List[DataPointScore]):
    # Read headers and records
    headers = sheet.row_values(1)
    records = sheet.get_all_records()
    
    try:
        score_col = headers.index("score") + 1
        den_col = headers.index("den") + 1
        consensus_col = headers.index("consensus_value") + 1
        consensus_col_score = headers.index("consensus_score") + 1
    except ValueError as e:
        print(" Column not found in sheet headers:", e)
        return

    # Build row index map
    row_map = {
        (record["Index"], record["data_point_name"]): idx + 2
        for idx, record in enumerate(records)
    }

    # Write data
    for result in scores:
        key = (result.index, result.data_point_name)
        row_num = row_map.get(key)
        if row_num:
            sheet.update_cell(row_num, score_col, result.score)
            time.sleep(1)  
            sheet.update_cell(row_num, den_col, result.den)
            time.sleep(1)
            sheet.update_cell(row_num, consensus_col, result.consensus_value_str)
            time.sleep(1)
            sheet.update_cell(row_num, consensus_col_score, result.consensus_score)
            time.sleep(1)
        else:
            print(f" Row not found for index {result.index} and data_point_name {result.data_point_name}")

# Instructions per Data Point
data_point_instructions = {
   "Project Name": """
Ignore spaces and capitalization in both ref and comparable values.
If they match, score is 1, else 0.
Den = count of valid comparables (not NA).
Consensus value = mode value among comparables.
Consensus score = times consensus value appears.
""",
    "Builder Name": """
Ignore spacing and capitalization for matching.
Ignore words like Builders, Developers, realtors, LLP, Pvt, Ltd, Limited.
If ref and comparable match, score is 1, else 0.
""",
    "Project Address": """
Reference value will have locality and a city name separated by a comma.
For matching project address, see if the same locality and city name exist in the compared values ignoring stop characters (spaces, comma, hyphen, full-stop).
If they exist, then match is 1, else 0.
""",
    "Avg Price psft Type": """
Detect if the values are in a range or a point to form a 'Price Type'.
If the comparables are the same 'Price Type' as the reference value, then score is 1, else 0.
""",
    "Avg Price psft": """
The comparable prices can be an absolute amount or a range.
If the comparable is in the form of a range and the reference value falls within that range, then the score is 1, else 0.
If the comparable is an absolute amount, and the comparable value is +/- 500 of the reference value, then the match score is 1, else 0.
""",
    "Property Type": """
Ignore configs and compare the property type only, i.e., Apartment, flat, villas, studio apartments, etc.
If the property type in the reference value matches with the value of the comparable, the score is 1, otherwise score will be 0.
""",
    "Completion date": """
For Completion date, reference and comparable values are different format of month, date and year of completion. Convert all values in MMM-YYYY format to form Converted Date. If the ref value and comparables have the same converted date, then match is 1 else 0.
""",
    "Project Area": """
Area will be a measure and a unit. Units can be in different formats like acres, hectare, sq ft, sq yards.
Convert all values into acres for comparison.
Match the unit in the reference value to units in the compared values up to one decimal place.
Round to 2 digits of decimal places. If they are the same, then match is 1, else 0.
""",
    "RERA": """
Each value will be a sequence of numbers, alphabets, and special characters (e.g., GGM/831/563/2024/58).
Compare the numbers in the reference value to numbers in the compared values.
If they are the same, then match is 1, else 0.
""",
    "Project Size - Tower Count": """
Each value will be a number.
Compare the numbers in the reference value to numbers in the compared values.
Ignore suffixes like tower, building, twr, bldg.
If they are the same, then match is 1, else 0.
""",
    "Project Size - Unit Count": """
Each value is a number. The number can contain suffixes like unit, units which should be ignored.
If the reference value is the same as the comparable, the match is 1, else 0.
""",
    "Configs": """
Each value will be a set of numbers and units (e.g., 2 BHK / 3 BHK / 5 BHK).
Unit will be BHK or bhk. If any number is a decimal, round it down to the nearest whole number (e.g., 3.5 BHK should be rounded down to 3 BHK).
Compare the numbers in the reference value to numbers in the compared values.
If they are the same, irrespective of the order of numbers, then match is 1, else 0.
""",
    "Amenities - Count": """
Each value is a number.
Compare the numbers in the reference value to numbers in the compared values.
If the reference value is greater than or equal to the comparable, then the match is 1, else 0.
""",
    "Photos": """
Each value is a number.
Compare the numbers in the reference value to numbers in the compared values.
If the reference value is greater than or equal to the comparable value, the match is 1, else 0.
""",
    "Videos": """
Value is a number (e.g., 8).
Compare the numbers in the reference value to numbers in the compared values.
If the reference value is greater than the comparable, then match is 1, else 0.
""",
    "Review Count": """
Value is a number (e.g., 8).
Compare the numbers in the reference value to numbers in the compared values.
If the reference value is greater than or equal to the comparable value, the match is 1, else 0.
""",
    "Builder-Established Date": """
Reference and compared values are years of establishment.
Year can be in a contracted form ('29). If the compared value is in the format " + years/year", extract the number of years from the format.
Subtract it from the current year (2025) to create the comparable year (e.g., 11+ years would be 2025-11=2014).
If the year in the reference and compared year is the same, then match is 1, else 0.
""",
    "Builder-Project Count": """
Value will be a number (e.g., 8).
Compare the numbers in the reference value to numbers in the compared values.
If the reference value is greater than or equal to the comparables, then match is 1, else 0.
""",
    "Possession Status": """
The value will be the possession status of the project: Ready to Move (R2M/RTM), Under Construction (UC), New Launch (NL).
Ignore special characters if any.
Compare the value in the reference with the comparable.
If the possession status in the reference matches with the possession status in the comparable, then match is 1, else 0.
""",
"Price Range": """
For Project price range, we will give you price range. The price range in reference and comparable will have varied formats (Cr/ C/ Crores, ₹/Rs, L/ lakhs/ lacs/Lac). 
Convert the data of reference and comparable to one format (Ex- Convert 100 L to Cr before comparison) and then compare only the value 
(ex- 100 L - 2.1 Cr should be first converted to same format, i.e., 1 Cr- 2.1 Cr. Now, compare the price range). 
If the reference value is an absolute amount and if it falls in the range of comparable, the matching score would be 1, else 0.
If the values in the reference matches that of comparable, the matching score is 1 else 0. 
"""
   
}


all_scores = []
for dp_name, rule in data_point_instructions.items():
    print(f"\n Processing: {dp_name}")
    try:
        scores = process_data_point(df, model, dp_name, rule)
        if scores:
            write_scores_to_sheet(sheet, scores)
            all_scores.extend(scores)
    except Exception as e:
        print(f" Error processing {dp_name}: {e}")
