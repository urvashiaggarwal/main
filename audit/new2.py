import gspread
from google.oauth2.service_account import Credentials
from pydantic import BaseModel
from typing import List
import pandas as pd
import re
import json
from datetime import datetime
import google.generativeai as genai


# Load credentials and initialize gspread
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',"https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("thematic-center-456905-p2-9fe58916a625.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("Audit").worksheet("Sheet3")  # adjust if needed

# Load data into DataFrame
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Initialize Gemini
genai.configure(api_key="AIzaSyCtdSkArjhNZNd1UcGPB671eKFiX1OK-Qk")
model = genai.GenerativeModel("gemini-2.0-flash")

# Class Definition for Structured Output
class DataPointScore(BaseModel):
    data_point_name: str
    index: int
    score: int
    den: int
    consensus_value: str
    consensus_score: int    

# Extract JSON from Gemini response
def extract_json_from_response(response_text: str):
    try:
        json_string = re.search(r'\[.*\]', response_text, re.DOTALL).group(0)
        return json.loads(json_string)
    except Exception as e:
        print("Error parsing JSON:", e)
        return []

# Project Name Processor
def process_project_name(df: pd.DataFrame, model) -> List[DataPointScore]:
    filtered_df = df[df['data_point_name'] == 'Project Name']
    filtered_df=filtered_df[0:10]
    data_records = filtered_df.to_csv(index=False, header=False)

    prompt = f"""
We will provide you data in the form of a google sheet in which Index will be the unique identifier.
data_point_name is the header of the values and the data has been fetched from different sources, namely 99acres, Comp 1, Comp 2, Comp 3.
The first data point in every row is the refrence value (called ref value) the source of which is 99acres which needs to be compared against the following 3 data points in the same row (called comparables) which is the data sourced from Comp 1, Comp 2, Comp 3 to generate a matching score.
Matching score is the number of data points to which the first data point matches.
Matches can be exact or approximate.

If a particlar comparable is 'Not Available or N/A or NA', then the match against the value should be ignored
If a ref value is 'Not Available or N/A or NA', then match is 0. 

Pls produce a matching score for each of the data points.
Specific instructions for each data point name are:

1. For Project Name, ignore spaces and capitalization in both ref and comparable values for matching. If they match, score is 1, otherwise score will be 0. Ignore singular and plural in project name. Convert the romans to numerals before comparsion.Ignore singular and plurals.


Also calculate a value called Den. Den is count of all comparables (data sourced from Comp 1, Comp 2, Comp 3) which are not "Not Available, N/A, Not found or NA". Consensus value is the mode value among the comparables (data sourced from Comp 1, Comp 2, Comp 3) in each data_point_name. Consensus score is the number of times Consensus value occurs in the comparables. Give the output in the form of a structured comma separated table with columns- index, data_point_name, matching score, Den, Consensus value, Consensus score. 
For calculating matching score make sure to check the data_point_name and follow Specific instruction of that particular data_point_name only.

Do not use your own logic.
Return the output as a JSON list with fields: 
- thoughts in 75 characters
- data_point_name
- index (same as Index from sheet)
- score (integer)
- den (integer)
- consensus_value (string )
- consensus_score (integer)
Here is the data:
{data_records}
"""
    response = model.generate_content([prompt])
    json_data = extract_json_from_response(response.text)
    print(json_data)
    return [DataPointScore(**entry) for entry in json_data]

#Builer Name Processor

def process_builder_name(df: pd.DataFrame, model) -> List[DataPointScore]:
    filtered_df = df[df['data_point_name'] == 'Builder Name']
    filtered_df = filtered_df[:] # For testing small block
    data_records=filtered_df.to_csv(index=False, header=False)

    prompt = f"""
We will provide you data in the form of a google sheet in which Index will be the unique identifier.
data_point_name is the header of the values and the data has been fetched from different sources, namely 99acres, Comp 1, Comp 2, Comp 3.
The first data point in every row is the refrence value (called ref value) the source of which is 99acres which needs to be compared against the following 3 data points in the same row (called comparables) which is the data sourced from Comp 1, Comp 2, Comp 3 to generate a matching score.
Matching score is the number of data points to which the first data point matches.

If a particlar comparable is 'Not Available or N/A or NA', then the match against the value should be ignored
If a ref value is 'Not Available or N/A or NA', then match is 0. 

Pls produce a matching score for Builder Name.

Specific instructions for Builder Name:
- Ignore spacing and capitalization in both ref and comparable values.
- Ignore words like Builders, Developers, Realtors, LLP, Pvt, Ltd, Limited in both ref and comparable values.
- If the cleaned values match, score is 1, else 0.

Do not use your logic.
Also calculate a value called Den. Den is count of all comparables (data sourced from Comp 1, Comp 2, Comp 3) which are not "Not Available, N/A, Not found or NA". Consensus value is the mode value among the comparables (data sourced from Comp 1, Comp 2, Comp 3) in each data_point_name. Consensus score is the number of times Consensus value occurs in the comparables. Give the output in the form of a structured comma separated table with columns- index, data_point_name, matching score, Den, Consensus value, Consensus score. Also, give your thoughts in 75 characters.

Return the output as a JSON list with fields: 
- thoughts in 75 characters
- data_point_name
- index (same as Index from sheet)
- score (integer)
- den (integer)
- consensus_value (string )
- consensus_score (integer)

Here is the data:
{data_records}
"""
    response = model.generate_content([prompt])
    json_data = extract_json_from_response(response.text)
    return [DataPointScore(**entry) for entry in json_data]


#  Write Results Back to Sheet
def write_scores_to_sheet(sheet, scores: List[DataPointScore]):
    # Read the sheet again to get the row data
    all_rows = sheet.get_all_values()
    headers = all_rows[0]
    data_rows = all_rows[1:]

    # Find column indexes
    index_col = headers.index("Index")
    dp_name_col = headers.index("data_point_name")
    score_col = headers.index("score") + 1
    den_col = headers.index("den") + 1
    consensus_col = headers.index("consensus_value") + 1
    consensus_col_score = headers.index("consensus_score") + 1

    for result in scores:
        for i, row in enumerate(data_rows):
            row_index = row[index_col]
            row_dp_name = row[dp_name_col]

            if str(row_index) == str(result.index) and row_dp_name.strip().lower() == result.data_point_name.strip().lower():
                row_num = i + 2  # account for header row and 1-based indexing
                sheet.update_cell(row_num, score_col, result.score)
                sheet.update_cell(row_num, den_col, result.den)
                sheet.update_cell(row_num, consensus_col, result.consensus_value)
                sheet.update_cell(row_num, consensus_col_score, result.consensus_score)
                break

#Run for Project Name and Builder Name
# scores = process_project_name(df, model)
# print("Scores for Project Name:", scores)
# write_scores_to_sheet(sheet, scores)
builder_scores = process_builder_name(df, model)
print("Scores for Builder Name:", builder_scores)
write_scores_to_sheet(sheet, builder_scores)
