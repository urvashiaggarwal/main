import pandas as pd

# Load your CSV file
df = pd.read_csv("missing_floorplans.csv")

# Drop rows where the second column has missing values
second_col = df.columns[1]
df_cleaned = df.dropna(subset=[second_col])

# Save the cleaned CSV
df_cleaned.to_csv("cleaned_floorplans.csv", index=False)
