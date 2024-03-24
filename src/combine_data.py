import urllib
import pandas as pd

input_folder = "data/summary/"
output_folder = "data/summary/"

# Load CSV files into pandas DataFrames
df1 = pd.read_csv(f"{input_folder}case_metadata.csv")
df2 = pd.read_csv(f"{input_folder}case_details.csv")

# Preprocess Input Filename in df2
df2["Input Filename"] = df2["Input Filename"].apply(
    lambda x: urllib.parse.unquote_plus(x.split("DR")[-1].split(".")[0])
)

# Merge DataFrames based on custom condition
merged_df = pd.merge(
    df1,
    df2[df2["Input Filename"].isin(df1["DR No."])],
    left_on="DR No.",
    right_on="Input Filename",
    how="inner",
)

# Write merged DataFrame to a new CSV file
merged_df.to_csv(f"{output_folder}merged_summary_report.csv", index=False)
