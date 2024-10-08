import os
import urllib
import pandas as pd

input_folder = "data/summary/"
output_folder = "data/summary/"

# Load CSV files into pandas DataFrames
df1 = pd.read_csv(f"{input_folder}case_metadata.csv")
df2 = pd.read_csv(f"{input_folder}determination_details.csv")


# Function to extract and decode filenames
def normalize_filenames(name):
    if isinstance(name, str):  # Check if the value is a string
        # Extract filename and decode URL-encoded characters
        filename = urllib.parse.unquote_plus(name.split("/")[-1])
        # Remove file extension for join by filename
        filename_without_extension = os.path.splitext(os.path.basename(filename))[0]
        return filename_without_extension.strip()  # Strip leading/trailing whitespace
    else:
        return ""  # Return empty string


# Extract and decode filenames in both DataFrames
df1["Determination Filename Decoded"] = df1["Determination PDF"].apply(
    normalize_filenames
)
df2["Text Filename Decoded"] = df2["Text Filename"].apply(normalize_filenames)

# Merge DataFrames based on file name of downloaded determination order text file
merged_df = pd.merge(
    df1,
    df2,
    left_on="Determination Filename Decoded",
    right_on="Text Filename Decoded",
    how="left",
)

# Drop the extra columns created during merge
merged_df.drop("Determination Filename Decoded", axis=1, inplace=True)
merged_df.drop("Text Filename Decoded", axis=1, inplace=True)

# Reorder columns, moving "Comments" column to the end
columns = list(merged_df.columns)
columns.remove("Comments")
columns.append("Comments")
merged_df = merged_df[columns]

# Write merged DataFrame to a new CSV file
merged_df.to_csv(f"{output_folder}merged_summary_report.csv", index=False)
