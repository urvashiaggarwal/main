import pandas as pd

input_csv = "Magicbricks_links.csv"  
output_csv = "workable_links_magicbricks.csv"

df = pd.read_csv(input_csv)

required_columns = {"XID", "Project Name", "City", "Magicbricks.com Link"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"CSV file must contain the following columns: {required_columns}")

# Filter rows where 'URL' contains 'pdpid'
filtered_df = df[df["Magicbricks.com Link"].str.contains("pdpid", na=False)]
filtered_df = filtered_df[["XID", "Project Name", "City", "Magicbricks.com Link"]]

filtered_df.to_csv(output_csv, index=False)

print(f"Filtered links saved to {output_csv}")
