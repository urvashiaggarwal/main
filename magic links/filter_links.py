import pandas as pd

# Load the CSV files
small_df = pd.read_csv("Magicbricks_links_updated.csv")  # CSV with 800 entries
large_df = pd.read_csv("MagicBricks_links.csv")  # CSV with 2300 entries

# Extract XIDs from the small CSV
existing_xids = set(small_df["XID"])

# Filter out rows where XID is in existing_xids
filtered_large_df = large_df[~large_df["XID"].isin(existing_xids)]

# Save the filtered data
filtered_large_df.to_csv("filtered_large.csv", index=False)

print(f"Filtered CSV saved with {len(filtered_large_df)} records.")
