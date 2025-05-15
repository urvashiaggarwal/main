import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Use creds to create a client to interact with the Google Drive API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(r"c:\Users\urvashi.aggarwal\Downloads\thematic-center-456905-p2-9fe58916a625.json", scope)
client = gspread.authorize(creds)

# Open a spreadsheet by name
sheet=client.open_by_key
sheet = client.open("Audit").sheet1

# Get all values
data = sheet.get_all_records()  # returns a list of dictionaries
print(data)

# Get value from cell
print(sheet.cell(1, 1).value)  # row 1, col 1

# Update a cell
sheet.update_cell(1, 2, "Hello!")

# Add a new row
sheet.append_row(["Name", "Age", "Location"])
