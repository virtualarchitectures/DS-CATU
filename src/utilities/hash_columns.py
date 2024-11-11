import os
import pandas as pd
import hashlib

input_folder = "data/summary/"
output_folder = "data/summary/"

# Load CSV files into pandas DataFrames
df = pd.read_csv(f"{input_folder}case_metadata.csv")

# Define columns to hash
columns_to_hash = ["Title", "DR No."]


def hash_columns(df, columns_to_hash):
    # Add a new column for the hashed values
    df.insert(0, "hash_id", "")

    # Iterate through each row
    for index, row in df.iterrows():
        # Initialize an empty string to store the concatenated values
        concatenated_values = ""

        # Iterate through each column to hash
        for column in columns_to_hash:
            # Get the value from the current cell
            value = str(row[column])

            # Concatenate the value with a delimiter
            concatenated_values += value + "|"

        # Remove the trailing delimiter
        concatenated_values = concatenated_values[:-1]

        # Hash the concatenated values using SHA-256
        hashed_value = hashlib.sha256(concatenated_values.encode()).hexdigest()

        # Update the "hash_id" column with the hashed value
        df.at[index, "hash_id"] = hashed_value

    # Write hashed DataFrame to a new CSV file
    df.to_csv(f"{output_folder}hashed_data.csv", index=False)


hash_columns(df, columns_to_hash)
