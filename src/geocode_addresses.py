import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def geocode_address(api_key, address, county_code):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key,
        "components": f"country:{country_code}",
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            print(f"{address}: {location['lat']},{location['lng']}")
            return location["lat"], location["lng"]
        else:
            print(f"Error geocoding {address}: {data['status']}")
    else:
        print(f"HTTP error: {response.status_code}")

    return None, None


def geocode_addresses(input_csv, output_csv, api_key, country_code):
    df = pd.read_csv(input_csv)
    latitudes = []
    longitudes = []

    for address in df["Address"]:
        lat, lng = geocode_address(api_key, address, country_code)
        latitudes.append(lat)
        longitudes.append(lng)
        time.sleep(1)  # To respect API rate limits

    df["Latitude"] = latitudes
    df["Longitude"] = longitudes
    df.to_csv(output_csv, index=False)
    print(f"Geocoded addresses saved to {output_csv}")


if __name__ == "__main__":
    # Configuration
    input_csv = (
        "data/summary/BACKUP_merged_summary_report.csv"  # Path to your input CSV file
    )
    output_csv = (
        "data/summary/geocoded_summary_report.csv"  # Path to your output CSV file
    )
    api_key = os.getenv(
        "GOOGLE_GEOCODING_API_KEY"
    )  # Read API key from environment variable

    country_code = "IE"  # Specify the country code

    if not api_key:
        raise ValueError(
            "Google Geocoding API key not found. Please set the environment variable 'GOOGLE_GEOCODING_API_KEY'."
        )

    geocode_addresses(input_csv, output_csv, api_key, country_code)
