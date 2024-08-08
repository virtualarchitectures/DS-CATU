import csv
import os


def split_csv(input_file, batch_size, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, mode="r", newline="") as infile:
        reader = csv.reader(infile)
        header = next(reader)

        batch_count = 0
        current_batch = []

        for row_num, row in enumerate(reader):
            current_batch.append(row)
            if (row_num + 1) % batch_size == 0:
                output_file = os.path.join(output_dir, f"batch_{batch_count}.csv")
                with open(output_file, mode="w", newline="") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                    writer.writerows(current_batch)
                batch_count += 1
                current_batch = []

        # Write any remaining rows that did not make a full batch
        if current_batch:
            output_file = os.path.join(output_dir, f"batch_{batch_count}.csv")
            with open(output_file, mode="w", newline="") as outfile:
                writer = csv.writer(outfile)
                writer.writerow(header)
                writer.writerows(current_batch)


if __name__ == "__main__":
    input_file = "data/summary/merged_summary_report.csv"  # Replace with your input CSV file path
    batch_size = 999  # Replace with the desired batch size
    output_dir = "data/geocoding_batches"  # Replace with your desired output directory

    split_csv(input_file, batch_size, output_dir)
