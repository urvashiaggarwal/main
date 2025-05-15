import pandas as pd

# Load the CSV file
df = pd.read_csv("squareyards_links.csv")  # Replace with your actual filename

# Drop rows where 'Squareyards.com Link' does NOT end with '/project'
df_cleaned = df[df['Squareyards.com Link'].str.strip().str.endswith('/project', na=False)]

# Save the cleaned data
df_cleaned.to_csv("cleaned_file.csv", index=False)
