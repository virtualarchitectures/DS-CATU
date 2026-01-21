import os
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

input_folder = "data/downloaded_docs/"
output_folder = "data/converted_text/"

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def get_file_paths(input_folder):
    file_paths = []

    # Loop through the files in the input folder
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # Check if file has a supported extension
            _, extension = os.path.splitext(file)
            if extension.lower() in SUPPORTED_EXTENSIONS:
                # Construct the full file path
                file_path = os.path.join(root, file)
                file_paths.append(file_path)

    return file_paths


def create_converter(force_ocr=False):
    """Create a DocumentConverter with appropriate OCR settings.

    EasyOCR is used by default. OCR is applied automatically when needed.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True

    if force_ocr:
        pipeline_options.ocr_options.force_full_page_ocr = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    return converter


def docling_convert(file_path, output_folder, subfolder, converter):
    """Convert a document using docling and save the text output."""
    # Extract the file name
    path, file_name = os.path.split(file_path)
    base_name, extension = os.path.splitext(file_name)

    # Convert the document
    input_path = Path(file_path)
    result = converter.convert(input_path)

    # Export to plain text
    text_content = result.document.export_to_markdown(strict_text=True)

    # Create the subfolder in the output folder if it doesn't exist
    subfolder_path = os.path.join(output_folder, subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    # Write text to a file in the corresponding subfolder
    output_file_path = os.path.join(subfolder_path, f"{base_name}.txt")
    print(f"Output: {output_file_path}")
    with open(output_file_path, mode="w", encoding="utf8") as f:
        f.write(text_content)


def process_documents(input_folder, output_folder, force_ocr=False):
    """Process all supported documents in the input folder."""
    file_paths = get_file_paths(input_folder)

    if not file_paths:
        print("No supported documents found.")
        return

    # Create converter once for all documents
    print(f"Initializing converter (force_ocr={force_ocr})...")
    converter = create_converter(force_ocr=force_ocr)

    for file_path in file_paths:
        print(f"Processing: {file_path}")
        # Identify the subfolder name
        subfolder = os.path.basename(os.path.dirname(file_path))
        print(f"Subfolder: {subfolder}")
        # Process the document and store it in the corresponding output subfolder
        try:
            docling_convert(file_path, output_folder, subfolder, converter)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert PDF and DOCX documents to text using docling with EasyOCR."
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Force full page OCR on all documents (slower but more thorough)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=input_folder,
        help=f"Input folder path (default: {input_folder})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=output_folder,
        help=f"Output folder path (default: {output_folder})",
    )

    args = parser.parse_args()

    process_documents(args.input, args.output, force_ocr=args.force_ocr)
