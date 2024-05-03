import urllib
import pandas as pd
import numpy as np

input_folder = "data/summary/"
output_folder = "data/summary/"

# Load CSV files into pandas DataFrames
df1 = pd.read_csv(f"{input_folder}case_metadata.csv")
df2 = pd.read_csv(f"{input_folder}case_details.csv")

# Preprocess Input Filename in df2
df2["Input Filename"] = df2["Input Filename"].apply(
    lambda x: urllib.parse.unquote_plus(x.split("DR")[-1])
)


# Function to extract filename from URL
def extract_filename(url):
    if isinstance(url, str):  # Check if the value is a string
        return url.split("/")[-1]
    else:
        return np.nan  # Return NaN if the value is not a string


# Extract filename from Determination PDF URLs
df1["Determination PDF Filename"] = df1["Determination PDF"].apply(extract_filename)

# Merge DataFrames based on Determination order
merged_df = pd.merge(
    df1,
    df2,
    left_on="Determination PDF Filename",
    right_on="Input Filename",
    how="left",
)

# Drop the extra column created during merge
merged_df.drop("Determination PDF Filename", axis=1, inplace=True)

# Reorder columns, moving "Comments" column to the end
columns = list(merged_df.columns)
columns.remove("Comments")
columns.append("Comments")
merged_df = merged_df[columns]

# Write merged DataFrame to a new CSV file
merged_df.to_csv(f"{output_folder}merged_summary_report.csv", index=False)
