import pandas as pd

# Load the uploaded CSV file
df = pd.read_csv("square_final.csv")

# Define the formatting function with correct structure
def format_floor_plan(cell):
    try:
        plans = eval(cell)
        result = []
        for plan in plans:
            if len(plan) == 5:
                type1 = plan[0].strip()
                bhk_details = plan[1].strip()  # e.g., '3 BHK 1900 Sq. Ft. Apartment'
                bhk_parts = bhk_details.split(' ', 2)  # ['3', 'BHK', '1900 Sq. Ft. Apartment']
                if len(bhk_parts) == 3:
                    bhk = bhk_parts[0]
                    unit_type = bhk_parts[2]
                    formatted = f"{bhk} BHK {unit_type}, {type1}, {bhk_parts[2].split()[0]} {bhk_parts[2].split()[1]}, {plan[2].strip('()')}, {plan[3]}, {plan[4]}"
                    result.append(formatted)
        return " | ".join(result)
    except Exception as e:
        return f"Error parsing: {e}"

# Apply to the 2nd column (index 1), assuming it's the floor plans
df['Floor Plan'] = df.iloc[:, 1].apply(format_floor_plan)

# Return a preview of the formatted results
df[['Floor Plan']].head()
# Save the formatted results to a new CSV file
df.to_csv("formatted_square_yards.csv", index=False)
