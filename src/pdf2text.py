import os
from pdf2image import convert_from_path
import pytesseract

input_folder = "data/downloaded_pdfs/"
output_folder = "data/converted_text/"


def get_file_paths(input_folder):
    file_paths = []

    # Loop through the files in the input folder
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # Construct the full file path
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths


def join_rows(text):
    # Store the result
    result = []

    # Split multiline strings into a list of lines
    lines = text.split("\n")

    # Accumulate lines into paragraphs
    current_paragraph = ""
    for line in lines:
        # If the line is not empty
        if line.strip():
            # Add the line to the current paragraph
            current_paragraph += line + " "
            # If the line ends with a colon or full stop, start a new paragraph
            if line.strip().endswith(":") or line.strip().endswith("."):
                result.append(current_paragraph.strip())
                current_paragraph = ""
        else:
            # Add the current paragraph to the result if not empty
            if current_paragraph:
                result.append(current_paragraph.strip())
                current_paragraph = ""

    # Add the remaining paragraph to the result if not empty
    if current_paragraph:
        result.append(current_paragraph.strip())

    # Join the paragraphs with newlines and return the result
    return "\n".join(result)


def pdf2text(file_path, output_folder, subfolder, page_numbers=False):
    images = convert_from_path(file_path)

    # Extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

    # Get the number of pages
    page_count = len(images)
    print(f"Pages: {page_count}")

    # Combine text from multiple pages
    combined_text = ""

    # Iterate through pages
    for page_number, image_data in enumerate(images, start=1):
        txt = pytesseract.image_to_string(image_data)

        # Remove form feed character
        txt = txt.replace("\x0c", "")

        # Combine pages and add page numbers if requested
        if page_numbers:
            combined_text += f"Page # {str(page_number)}\n\n"
            combined_text += f"{txt}\n\n"
        else:
            combined_text += f"{txt}"

    # Join lines that don't end with a full stop
    combined_text = join_rows(combined_text)

    # Create the subfolder in the output folder if it doesn't exist
    subfolder_path = os.path.join(output_folder, subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    # Write combined text to a file in the corresponding subfolder
    output_file_path = os.path.join(subfolder_path, f"{base_name}.txt")
    print(f"Output: {output_file_path}")
    with open(output_file_path, mode="w") as f:
        f.write(combined_text)


def process_pdfs(input_folder, output_folder, page_numbers=False):
    file_paths = get_file_paths(input_folder)

    for file_path in file_paths:
        print(f"Processing: {file_path}")
        # Identify the subfolder name
        subfolder = os.path.basename(os.path.dirname(file_path))
        print(f"Subfolder: {subfolder}")
        # Process the PDF and store it in the corresponding output subfolder
        pdf2text(file_path, output_folder, subfolder, page_numbers)


process_pdfs(input_folder, output_folder, page_numbers=False)
