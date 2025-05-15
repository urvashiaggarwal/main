import re
import pandas as pd

def clean_floor_plan(text):
    # Split on " | " to handle multiple units in one cell
    units = text.split(" | ")
    cleaned_units = []

    for unit in units:
        # Find pattern like: "3 BHK 1359 Sq. Ft." or "4 BHK 2780 Sq. Ft."
        match = re.match(r"(\d+\s*BHK)\s+\d+\s*Sq\.\s*Ft\.\s*(.*)", unit)
        if match:
            bhk = match.group(1)
            rest = match.group(2)
            cleaned_unit = f"{bhk} {rest}"
            cleaned_units.append(cleaned_unit)
        else:
            cleaned_units.append(unit)  # In case no match, keep it as-is

    return " | ".join(cleaned_units)

    # Load data from CSV
data = pd.read_csv("square_final.csv")

df = pd.DataFrame(data)

# Apply cleaner function
df["Floor Plan"] = df["Floor Plan"].apply(clean_floor_plan)

# Output
print(df)

# Optional: Save to CSV
df.to_csv("cleaned_floor_plans.csv", index=False)
