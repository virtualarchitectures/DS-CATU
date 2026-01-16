import os
import csv
import argparse

input_csv_path = "data/summary/determination_details.csv"
input_text_folder = "data/converted_text/determinations"
output_csv_path = "data/summary/address_validation_results.csv"


def validate_addresses(input_csv, text_folder, output_csv):
    """
    Validates that addresses in the CSV exist in their source text files.
    """
    results = []
    total = 0
    valid = 0
    invalid = 0
    skipped = 0

    with open(input_csv, mode="r", newline="", encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file)
        header = next(csv_reader)  # Skip header row

        for row in csv_reader:
            total += 1
            text_filename = row[0]
            address = row[3]

            # Skip if address is empty or None
            if not address or address.lower() == "none":
                print(f"Skipping {text_filename}: No address to validate")
                results.append(
                    [text_filename, address, "SKIPPED", "No address extracted"]
                )
                skipped += 1
                continue

            # Construct path to source text file
            text_file_path = os.path.join(text_folder, text_filename)

            if not os.path.exists(text_file_path):
                print(f"Error: Source file not found: {text_file_path}")
                results.append(
                    [text_filename, address, "ERROR", "Source file not found"]
                )
                invalid += 1
                continue

            # Read source text file
            with open(
                text_file_path, "r", encoding="utf-8", errors="ignore"
            ) as text_file:
                text_content = text_file.read()

            # Check if address exists in text (case-insensitive)
            if address.lower() in text_content.lower():
                print(f"Valid: {text_filename} - Address found")
                results.append(
                    [text_filename, address, "VALID", "Address found in source"]
                )
                valid += 1
            else:
                print(f"Invalid: {text_filename} - Address NOT found")
                results.append(
                    [text_filename, address, "INVALID", "Address not found in source"]
                )
                invalid += 1

    # Write results to output CSV
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Text Filename", "Address", "Status", "Details"])
        csv_writer.writerows(results)

    # Print summary
    matched = total - skipped
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    print(f"Total records: {total}")
    print(f"Matched addresses: {matched}")
    print(f"Skipped (no address): {skipped}")
    print(f"Matched rate: {matched / total * 100:.1f}%" if total > 0 else "N/A")
    print(f"Valid addresses: {valid}")
    print(f"Invalid addresses: {invalid}")
    print(f"Validation rate: {valid / matched * 100:.1f}%" if matched > 0 else "N/A")
    print(f"\nResults written to: {output_csv}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate addresses extracted from determination orders"
    )
    parser.add_argument(
        "--input-csv",
        default=input_csv_path,
        help="Path to the determination details CSV file",
    )
    parser.add_argument(
        "--text-folder",
        default=input_text_folder,
        help="Path to the folder containing source text files",
    )
    parser.add_argument(
        "--output-csv",
        default=output_csv_path,
        help="Path to write validation results CSV",
    )

    args = parser.parse_args()

    validate_addresses(args.input_csv, args.text_folder, args.output_csv)
