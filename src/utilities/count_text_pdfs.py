import os
import re
from pathlib import Path


def has_extractable_text(pdf_path, min_text_ratio=0.001):
    """
    Check if a PDF likely has extractable text content by examining raw bytes.

    PDFs with embedded text contain text streams with readable content,
    while scanned PDFs are mostly compressed image data.

    Args:
        pdf_path: Path to the PDF file
        min_text_ratio: Minimum ratio of text-like content to file size

    Returns:
        bool: True if the PDF likely has extractable text
    """
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()

        # Look for text stream markers and font definitions
        has_fonts = b"/Font" in content or b"/Type /Font" in content
        has_text_objects = b"BT" in content and b"ET" in content  # Begin/End Text markers

        # Count text-like sequences in streams (after decompression markers)
        # Look for patterns like "(text)" or "<hex>" which are PDF text operators
        text_patterns = re.findall(rb'\([\x20-\x7e]{10,}\)', content)
        text_content_size = sum(len(p) for p in text_patterns)

        # Also check for ToUnicode maps which indicate text encoding
        has_tounicode = b"/ToUnicode" in content

        # Heuristic: has fonts AND (text objects with content OR unicode maps)
        if has_fonts and has_text_objects:
            # Check if there's meaningful text content
            if text_content_size > 100 or has_tounicode:
                return True
            # Additional check: look for Tj/TJ operators (show text)
            if b"Tj" in content or b"TJ" in content:
                return True

        return False

    except Exception as e:
        print(f"  Warning: Could not read {pdf_path.name}: {e}")
        return False


def count_pdfs_in_folder(folder_path):
    """
    Count text-encoded vs scanned PDFs in a folder.

    Returns:
        tuple: (total_count, text_encoded_count, scanned_count, error_count)
    """
    folder = Path(folder_path)
    if not folder.exists():
        return 0, 0, 0, 0

    pdf_files = list(folder.glob("*.pdf"))
    total = len(pdf_files)
    text_encoded = 0
    scanned = 0
    errors = 0

    for pdf_file in pdf_files:
        try:
            if has_extractable_text(pdf_file):
                text_encoded += 1
            else:
                scanned += 1
        except Exception:
            errors += 1

    return total, text_encoded, scanned, errors


def main():
    base_path = Path(__file__).parent.parent.parent / "data" / "downloaded_pdfs"

    subfolders = ["determinations", "tribunals"]

    print("=" * 60)
    print("PDF Text Content Analysis")
    print("=" * 60)

    grand_total = 0
    grand_text = 0
    grand_scanned = 0

    for subfolder in subfolders:
        folder_path = base_path / subfolder
        print(f"\n{subfolder.upper()}")
        print("-" * 40)

        if not folder_path.exists():
            print(f"  Folder not found: {folder_path}")
            continue

        total, text_encoded, scanned, errors = count_pdfs_in_folder(folder_path)

        if total == 0:
            print("  No PDF files found")
            continue

        text_pct = (text_encoded / total) * 100 if total > 0 else 0
        scanned_pct = (scanned / total) * 100 if total > 0 else 0

        print(f"  Total PDFs:      {total}")
        print(f"  Text-encoded:    {text_encoded} ({text_pct:.1f}%)")
        print(f"  Scanned/Image:   {scanned} ({scanned_pct:.1f}%)")
        if errors > 0:
            print(f"  Read errors:     {errors}")

        grand_total += total
        grand_text += text_encoded
        grand_scanned += scanned

    print("\n" + "=" * 60)
    print("COMBINED TOTALS")
    print("-" * 40)
    if grand_total > 0:
        print(f"  Total PDFs:      {grand_total}")
        print(f"  Text-encoded:    {grand_text} ({(grand_text/grand_total)*100:.1f}%)")
        print(f"  Scanned/Image:   {grand_scanned} ({(grand_scanned/grand_total)*100:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    main()
