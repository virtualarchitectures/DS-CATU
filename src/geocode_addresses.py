import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def geocode_with_google(api_key, address):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key,
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


def geocode_with_here(api_key, address):
    base_url = "https://geocode.search.hereapi.com/v1/geocode"
    params = {
        "q": address,
        "apiKey": api_key,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["items"]:
            location = data["items"][0]["position"]
            print(f"{address}: {location['lat']},{location['lng']}")
            return location["lat"], location["lng"]
        else:
            print(f"Error geocoding {address}: No results found")
    else:
        print(f"HTTP error: {response.status_code}")

    return None, None


def geocode_address(api_key, address, api_provider):
    if api_provider == "google":
        return geocode_with_google(api_key, address)
    elif api_provider == "here":
        return geocode_with_here(api_key, address)
    else:
        raise ValueError("Unsupported API provider. Choose either 'google' or 'here'.")


def geocode_addresses(input_csv, output_csv, api_key, api_provider):
    print(f"You are using the {api_provider} Geocoding API")
    df = pd.read_csv(input_csv)
    latitudes = []
    longitudes = []

    for address in df["Address"]:
        lat, lng = geocode_address(api_key, address, api_provider)
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
    api_key_google = os.getenv("GOOGLE_GEOCODING_API_KEY")  # Google API key
    api_key_here = os.getenv("HERE_GEOCODING_API_KEY")  # Here API key
    api_provider = os.getenv("API_PROVIDER")  # API provider (google/here)S

    if api_provider == "google":
        api_key = api_key_google
        if not api_key:
            raise ValueError(
                "Google Geocoding API key not found. Please set the environment variable 'GOOGLE_GEOCODING_API_KEY'."
            )
    elif api_provider == "here":
        api_key = api_key_here
        if not api_key:
            raise ValueError(
                "Here Geocoding API key not found. Please set the environment variable 'HERE_GEOCODING_API_KEY'."
            )
    else:
        raise ValueError("Unsupported API provider. Choose either 'google' or 'here'.")

    geocode_addresses(input_csv, output_csv, api_key, api_provider)
