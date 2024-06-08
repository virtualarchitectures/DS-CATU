import csv
import os


def combine_csv(input_dir, output_file):
    # Get list of all CSV files in the input directory
    csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
    csv_files.sort()  # Ensure files are processed in the correct order

    with open(output_file, mode="w", newline="") as outfile:
        writer = csv.writer(outfile)
        header_written = False

        for csv_file in csv_files:
            input_file = os.path.join(input_dir, csv_file)
            with open(input_file, mode="r", newline="") as infile:
                reader = csv.reader(infile)
                header = next(reader)

                # Write the header only once
                if not header_written:
                    writer.writerow(header)
                    header_written = True

                # Write the rest of the rows
                writer.writerows(reader)


if __name__ == "__main__":
    input_dir = "data/geocoding_batches"  # Replace with your input directory containing the split CSV files
    output_file = "data/recombined_summary_report.csv"  # Replace with your desired output CSV file path

    combine_csv(input_dir, output_file)
