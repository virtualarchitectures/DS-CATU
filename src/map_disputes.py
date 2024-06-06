import os
import folium
from folium.plugins import MarkerCluster
import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv("data/summary/geocoded_summary_report.csv")

# Ensure the CSV has 'Latitude', 'Longitude', and 'Address' columns
required_columns = ["Latitude", "Longitude", "Address"]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"CSV file must contain '{col}' column.")

# Remove rows with NaN values in 'Latitude', 'Longitude', or 'Address'
df = df.dropna(subset=required_columns)

# Ensure there are still rows left after removing NaNs
if df.empty:
    raise ValueError(
        "No valid rows found after removing NaNs in 'Latitude', 'Longitude', or 'Address' columns."
    )

# Create a map centered around the average of the Latitude and Longitude values
center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

# Add a marker cluster to the map
marker_cluster = MarkerCluster().add_to(m)

# Add points to the marker cluster with customized popups
for index, row in df.iterrows():
    popup_text = f"""
    <b>DR No.:</b> {row['DR No.']}<br>
    <b>Address:</b> {row['Address']}<br>
    <b>Date:</b> {row['Determination Date']}<br>
    <b>Landlord Name(s):</b> {row['Landlord Name(s)']}<br>
    <b>Landlord Role:</b> {row['Landlord Role']}<br>
    """
    if pd.notna(row["Determination PDF"]) and row["Determination PDF"].strip() != "":
        popup_text += f'<b>Link:</b> <a href="{row["Determination PDF"]}" target="_blank">Determination Order PDF</a><br>'
    if pd.notna(row["Tribunal PDF"]) and row["Tribunal PDF"].strip() != "":
        popup_text += f'<b>Link:</b> <a href="{row["Tribunal PDF"]}" target="_blank">Tribunal Report PDF</a>'

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=folium.Popup(popup_text, max_width=300),
    ).add_to(marker_cluster)

# Define the output folder and file name
output_folder = "map"
output_file = "RTB-Disputes-Map.html"

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Save the map to an HTML file using os.path.join
output_path = os.path.join(output_folder, output_file)
m.save(output_path)

print(f"Map has been saved to {output_path}")
