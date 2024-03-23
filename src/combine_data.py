import pandas as pd

input_folder = "data/summary/"

output_folder = "data/summary/"

# Load CSV files into pandas DataFrames
df1 = pd.read_csv("case_metadata.csv")
df2 = pd.read_csv("case_details.csv")

# Merge DataFrames based on unique IDs
merged_df = pd.merge(df1, df2, on="unique_id", how="inner")

# Write merged DataFrame to a new CSV file
merged_df.to_csv("merged_summary_report.csv", index=False)
