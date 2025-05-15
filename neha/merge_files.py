import pandas as pd

# Load all three CSVs
housing_df = pd.read_csv("housing data noida 1.csv")
magicbricks_df = pd.read_csv("magicbricks_manual.csv")
squareyards_df = pd.read_csv("squareyards.csv")

# Add prefixes
housing_df = housing_df.add_prefix('Housing_')
magicbricks_df = magicbricks_df.add_prefix('MB_')
squareyards_df = squareyards_df.add_prefix('SY_')

# Rename XID and Phase columns for alignment
housing_df = housing_df.rename(columns={'Housing_XID number': 'XID', 'Housing_Phase': 'Phase'})
magicbricks_df = magicbricks_df.rename(columns={'MB_XID': 'XID', 'MB_Phase': 'Phase'})
squareyards_df = squareyards_df.rename(columns={'SY_XID': 'XID', 'SY_Phase': 'Phase'})

# Normalize Phase values: extract numeric part (e.g., "Phase 1" → "1")
for df in [housing_df, magicbricks_df, squareyards_df]:
    df['Phase'] = df['Phase'].astype(str).str.extract(r'(\d+)', expand=False)

# Merge on XID and Phase
merged_df = housing_df.merge(magicbricks_df, on=['XID', 'Phase'], how='outer')
merged_df = merged_df.merge(squareyards_df, on=['XID', 'Phase'], how='outer')

squareyards_df['SY_Amenities Combined'] = squareyards_df[
    ['SY_Sports Amenities', 'SY_Convenience Amenities', 'SY_Safety Amenities',
     'SY_Environment Amenities', 'SY_Leisure Amenities']
].fillna('').agg(' | '.join, axis=1).str.strip(' | ')

housing_df = housing_df.drop_duplicates(subset=['XID'])
magicbricks_df = magicbricks_df.drop_duplicates(subset=['XID'])
squareyards_df = squareyards_df.drop_duplicates(subset=['XID'])
# Define comparison fields
data_points = {
    "Name": ["Housing_Project Name", "MB_Name", "SY_Project Name"],
    "Location": ["Housing_Address", "MB_Address", "SY_Location"],
    "Builder Name": ["Housing_Builder Name", "MB_Builder", "SY_Builder"],
    "Price Range": ["Housing_Price Range", "MB_Price", "SY_Price Range"],
    "Price per Sq.Ft": ["Housing_Price per Sq.Ft", "MB_Price per Sq.Ft", "SY_Price per Sqft"],
    "BHK": ["Housing_Configurations", "MB_Flat Type", "SY_Configurations"],
    "Property Type": ["Housing_Property Type", "MB_Property Type", "SY_Property Type"],
    "Project Status": ["Housing_Status", "MB_Status", "SY_Project Status"],
    "Launch Date": ["Housing_Launch Date", "MB_Launch Date", "SY_Launch Date"],
    "Possession Date": ["Housing_Possession Starts", "MB_Possession Date", "SY_Completion Date"],
    "Total Units": ["Housing_Projec Size", "MB_Total Units", "SY_Total Number of Units"],
    "Project Size (Acres)": ["Housing_Project Area", "MB_Project Size", "SY_Project Size"],
    "Amenities Count": ["Housing_Amenity Count", "MB_Amenity Count", "SY_Amenities Count"],
    "USP": ["Housing_USP", "MB_USP", "SY_USP"],
    "Builder Experience": ["Housing_Experience", "MB_Experience", "SY_Builder Experience"],
    "Total Towers": ["Housing_Total Towers", "MB_Total Towers", "SY_Total Towers"],
    "Rera Number": ["Housing_RERA Number", "MB_RERA Number", "SY_RERA Number"],
    "Specifications":["Housing_Specifications", "MB_Specifications", "SY_Specifications"],
    "Amenities":["Housing_Amenities","MB_Amenities" , "SY_Amenities Combined"],
}

# Create comparison rows
comparison_rows = []
for _, row in merged_df.iterrows():
    xid = row['XID']
    phase = row['Phase']
    for dp, cols in data_points.items():
        comparison_rows.append({
            "XID": xid,
            "Phase": phase,
            "Data Point": dp,
            "Housing": row.get(cols[0], ""),
            "MagicBricks": row.get(cols[1], ""),
            "SquareYards": row.get(cols[2], "")
        })

comparison_df = pd.DataFrame(comparison_rows)
comparison_df = comparison_df.drop_duplicates()


# Export to CSV
comparison_df.to_csv("project_comparison_by_xid_phase.csv", index=False)
print("✅ Final comparison with normalized phases created successfully!")
