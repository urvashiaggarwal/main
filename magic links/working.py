import pandas as pd

# Input and output file paths
input_csv = "MAgicbricks_links.csv"  # Replace with your actual input file
output_csv = "workable_links_magicbricks.csv"

# Read the CSV file
df = pd.read_csv(input_csv)

# Ensure the necessary columns exist
required_columns = {"XID", "Project Name", "City", "Magicbricks.com Link"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"CSV file must contain the following columns: {required_columns}")

# Filter rows where 'URL' contains 'pdpid'
filtered_df = df[df["Magicbricks.com Link"].str.contains("pdpid", na=False)]

# Select required columns
filtered_df = filtered_df[["XID", "Project Name", "City", "Magicbricks.com Link"]]

# Save to a new CSV file
filtered_df.to_csv(output_csv, index=False)

print(f"Filtered links saved to {output_csv}")
