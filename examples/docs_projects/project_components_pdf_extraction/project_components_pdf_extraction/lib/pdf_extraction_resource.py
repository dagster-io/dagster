# type: ignore
import json
import os
from typing import Any, ClassVar, Optional

import dagster as dg
import pytesseract
import requests
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter


class PDFTextExtractor(dg.ConfigurableResource):
    """Initialize the PDF processor resource.

    Args:
        language: OCR language (default: 'eng')
        dpi: DPI for PDF conversion (default: 300)
        openai_api_key: OpenAI API key for validation (optional)
        preprocess: Whether to preprocess images (default: True)
    """

    language: str
    dpi: int
    openai_api_key: str
    preprocess: bool = True
    log: ClassVar = dg.get_dagster_logger()  # Add type annotation with ClassVar
    output_dir: str

    @property
    def openai_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }

    def preprocess_image(self, image_path: str, save_preprocessed: bool = True) -> tuple:
        """Preprocess image to improve OCR quality.

        Args:
            image_path: Path to the image file
            save_preprocessed: Whether to save the preprocessed image

        Returns:
            Tuple of (preprocessed image, path to saved preprocessed image)
        """
        self.log.info(f"Preprocessing image: {image_path}")

        # Load the image
        image = Image.open(image_path)

        # Convert to grayscale
        image = image.convert("L")

        # 1. Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast by factor of 2

        # 2. Apply threshold using point() method with proper type handling
        threshold = 200  # Threshold value (0-255)

        def threshold_func(p: int) -> int:
            return 255 if p > threshold else 0

        image = image.point(threshold_func)

        # 3. Remove small noise
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # 4. Sharpen the image
        image = image.filter(ImageFilter.SHARPEN)
        image = image.filter(ImageFilter.SHARPEN)  # Apply twice for stronger effect

        # 5. Enhance edges
        image = image.filter(ImageFilter.EDGE_ENHANCE)

        # Save preprocessed image if requested
        if save_preprocessed:
            # Generate preprocessed image path
            image_dir = os.path.dirname(image_path)
            image_filename = os.path.basename(image_path)
            preprocessed_path = os.path.join(image_dir, f"preprocessed_{image_filename}")

            # Save the preprocessed image
            image.save(preprocessed_path)
            self.log.info(f"Saved preprocessed image to {preprocessed_path}")

            return image, preprocessed_path

        return image, None

    def convert_pdf_to_images(
        self,
        pdf_path: str,
        output_folder: Optional[str] = None,
        specific_pages: Optional[list[int]] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> dict[str, Any]:
        """Convert PDF to images and save them to a folder.

        Args:
            pdf_path: Path to the PDF file
            output_folder: Custom output folder path. If None, creates folder with PDF name
            specific_pages: List of specific page numbers to extract (1-based). If None, extract all pages
            start_page: First page number to extract (1-based). Only used if specific_pages is None
            end_page: Last page number to extract (1-based). Only used if specific_pages is None

        Returns:
            Dictionary with conversion results
        """
        self.log.info(f"Converting PDF to images: {pdf_path}")

        # Check if file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output folder as output/pdf_name
        if output_folder is None:
            output_folder = os.path.join(
                self.output_dir, os.path.splitext(os.path.basename(pdf_path))[0]
            )
        os.makedirs(output_folder, exist_ok=True)
        self.log.info(f"Output folder: {output_folder}")

        # Convert PDF to images
        try:
            if specific_pages is not None:
                self.log.info(f"Specific pages: {specific_pages}")

                # Convert 1-based page numbers to 0-based for convert_from_path
                first_page = min(specific_pages)
                last_page = max(specific_pages)
                images = convert_from_path(
                    pdf_path,
                    dpi=self.dpi,
                    first_page=first_page,
                    last_page=last_page,
                )
                # Filter to only the specific pages requested
                images = [
                    img for i, img in enumerate(images, start=first_page) if i in specific_pages
                ]
            else:
                # Use start/end page range if provided, otherwise convert all pages
                first_page = start_page if start_page is not None else 1
                last_page = end_page if end_page is not None else None

                # If no end_page specified, convert all pages
                if last_page is None:
                    images = convert_from_path(
                        pdf_path,
                        dpi=self.dpi,
                        first_page=first_page,
                    )
                else:
                    images = convert_from_path(
                        pdf_path,
                        dpi=self.dpi,
                        first_page=first_page,
                        last_page=last_page,
                    )

            self.log.info(f"Converted {len(images)} pages to images")
        except Exception as e:
            self.log.error(f"Error converting PDF to images: {e!s}")
            raise

        # Save images to folder
        image_paths = []
        image_metadata = []

        for i, image in enumerate(images):
            # Calculate 1-based page number based on whether we're using specific pages or range
            if specific_pages is not None:
                page_number = specific_pages[i]
            else:
                page_number = first_page + i

            # Save original image
            image_path = os.path.join(output_folder, f"{page_number}.png")
            image.save(image_path, "PNG")

            image_paths.append(image_path)
            image_metadata.append(
                {
                    "page": page_number,
                    "path": image_path,
                    "width": image.width,
                    "height": image.height,
                    "dpi": self.dpi,
                }
            )

        # Create output
        result = {
            "file": os.path.basename(pdf_path),
            "images_folder": output_folder,
            "total_pages": len(images),
            "image_paths": image_paths,
            "images": image_metadata,
        }

        # Save metadata to folder
        metadata_path = os.path.join(output_folder, "conversion_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.log.info(f"Images saved to {output_folder}")
        return result

    def extract_text_from_images(self, pdf_name: str) -> dict[str, Any]:
        """Extract text from images using Tesseract OCR.

        Args:
            pdf_name: Name of the PDF file (without extension) to find metadata

        Returns:
            Dictionary with extraction results
        """
        self.log.info(f"Looking for conversion metadata for PDF: {pdf_name}")

        # Construct path to metadata file in the PDF-specific output directory
        pdf_output_dir = os.path.join(self.output_dir, pdf_name)
        metadata_path = os.path.join(pdf_output_dir, "conversion_metadata.json")

        # Load the conversion metadata
        try:
            with open(metadata_path, encoding="utf-8") as f:
                conversion_result = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find conversion metadata at {metadata_path}. "
                "Make sure the convert_to_image asset has run successfully."
            )

        self.log.info("Found conversion metadata, starting text extraction")

        # Use the PDF-specific output directory for all files
        images_folder = pdf_output_dir  # Override the folder from conversion_result
        image_paths = conversion_result["image_paths"]

        results = []
        preprocessed_paths = []

        # Process each image
        for i, image_path in enumerate(image_paths):
            page_number = i + 1  # 1-based page numbering
            self.log.info(f"Processing page {page_number}/{len(image_paths)}")

            try:
                # Preprocess the image if requested
                if self.preprocess:
                    image, preprocessed_path = self.preprocess_image(image_path)
                    if preprocessed_path:
                        preprocessed_paths.append(preprocessed_path)
                else:
                    image = Image.open(image_path)
                    preprocessed_path = None

                # Extract text with Tesseract
                page_text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                    config="--psm 1 --oem 3",  # Page segmentation mode 1: Auto with OSD
                )

                results.append(
                    {
                        "page": page_number,
                        "text": page_text,
                        "image_path": image_path,
                        "preprocessed_path": preprocessed_path,
                    }
                )

            except Exception as e:
                self.log.error(f"OCR error on page {page_number}: {e!s}")
                results.append(
                    {"page": page_number, "text": "", "error": str(e), "image_path": image_path}
                )

        # Use absolute paths in the result
        pdf_output_dir = os.path.abspath(os.path.join(self.output_dir, pdf_name))
        extraction_result = {
            "file": conversion_result["file"],
            "images_folder": pdf_output_dir,
            "total_pages": conversion_result["total_pages"],
            "pages": results,
            "preprocessed_paths": [os.path.abspath(p) for p in preprocessed_paths],
            "output_directory": pdf_output_dir,
            "text_file": os.path.abspath(os.path.join(pdf_output_dir, "extracted_text.txt")),
            "markdown_file": os.path.abspath(os.path.join(pdf_output_dir, "extracted_text.md")),
        }

        # Save extracted text to the PDF-specific directory
        all_text = ""
        for page in results:
            all_text += f"--- Page {page['page']} ---\n"
            all_text += page["text"]
            all_text += "\n\n"

        text_file = os.path.join(images_folder, "extracted_text.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(all_text)

        # Save extraction metadata to the PDF-specific directory
        extraction_metadata_path = os.path.join(images_folder, "extraction_metadata.json")
        with open(extraction_metadata_path, "w", encoding="utf-8") as f:
            metadata = extraction_result.copy()
            for page in metadata["pages"]:
                page["text_length"] = len(page.get("text", ""))
                if "text" in page and len(page["text"]) > 100:
                    page["text"] = page["text"][:100] + "..."
            json.dump(metadata, f, indent=2)

        # Update the paths in the result to use the output directory
        extraction_result["text_file"] = text_file
        extraction_result["metadata_file"] = extraction_metadata_path

        self.log.info(f"Text extracted and saved to {text_file}")
        return extraction_result

    def validate_purchase_order(
        self,
        pdf_name: str,
        expected_fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Validate generic purchase order extraction using OpenAI."""
        self.log.info(f"Validating purchase order extraction for PDF: {pdf_name}")

        # Get the PDF-specific output directory
        pdf_output_dir = os.path.join(self.output_dir, pdf_name)

        if not self.openai_api_key:
            self.log.warning("OpenAI API key not provided. Skipping validation.")
            error_result = {
                "error": "No OpenAI API key provided",
                "file": pdf_name,
                "validation_performed": False,
            }
            # Save error to PDF-specific directory
            error_file = os.path.join(pdf_output_dir, "po_validation_error.json")
            with open(error_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2)
            return error_result

        # Construct path to the extracted text file in the PDF-specific directory
        text_file_path = os.path.join(pdf_output_dir, "extracted_text.txt")

        try:
            # Read the full text
            with open(text_file_path, encoding="utf-8") as f:
                all_text = f.read()
        except FileNotFoundError:
            error_msg = f"Could not find extracted text file at {text_file_path}"
            self.log.error(error_msg)
            error_result = {
                "error": error_msg,
                "file": pdf_name,
                "validation_performed": False,
            }
            # Save error to PDF-specific directory
            error_file = os.path.join(pdf_output_dir, "po_validation_error.json")
            with open(error_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2)
            return error_result

        # Define common purchase order sections and headers to check for
        common_po_headers = [
            "Purchase Order",
            "PO Number",
            "Order Number",
            "Vendor",
            "Supplier",
            "Ship To",
            "Bill To",
            "Order Date",
            "Delivery Date",
            "Payment Terms",
            "Subtotal",
            "Tax",
            "Total",
            "Line Items",
            "Product",
            "Description",
            "Quantity",
            "Unit Price",
            "Amount",
            "Authorized By",
            "Shipping Method",
            "Special Instructions",
        ]

        # Add any additional expected fields if provided
        if expected_fields:
            common_po_headers.extend(expected_fields)

        # Format headers to search for
        headers_list = "\n".join([f"- {header}" for header in common_po_headers])

        # Build the prompt for OpenAI
        prompt = f"""Analyze the following text extracted from a purchase order PDF using OCR:

                    {all_text}

                    CONTEXT: This is a purchase order document that has been processed with OCR. We need to strictly verify if key purchase order sections and headers were successfully extracted.

                    1. Check if the following required purchase order headers and sections are present in the extracted text:
                    {headers_list}

                    2. For each identified header, extract the corresponding information.
                    - Headers must be explicitly present (e.g., "PO Number:" or "Purchase Order #")
                    - Values must be clearly associated with their headers
                    - Substitutions or inferred fields should be counted as missing

                    3. Identify any missing or incomplete sections.

                    Please provide:
                    1. OCR quality assessment (scale 1-10) using these criteria:
                       - 10: Perfect extraction, all text clear and accurate
                       - 8-9: Minor issues, all critical information present and accurate
                       - 6-7: Some issues but most text readable, some formatting problems
                       - 4-5: Significant issues, multiple unclear sections
                       - 1-3: Major problems, text largely unreadable or inaccurate

                    2. List specific OCR errors or issues found
                    3. List of purchase order headers/sections found with exact values
                    4. List of missing or incomplete sections
                    5. Assessment of whether this is a complete and valid purchase order

                    Scoring criteria:
                    - Required fields (must all be present): PO Number, Order Date, Ship To, Total Amount
                    - Critical sections (at least 3 must be present): Line Items, Payment Terms, Vendor Info, Authorized By
                    - Supporting fields (should have majority): Shipping Method, Special Instructions, Tax, Subtotal
                    - Format and structure should be clear and professional
                    - Line items must be properly structured with quantities and prices

                    Return your analysis in JSON format with the following structure:
                    {{
                        "ocr_quality": 1-10,
                        "ocr_issues": ["issue1", "issue2", ...],
                        "headers_found": {{
                            "purchase_order_number": "value",
                            "vendor_information": "value",
                            "order_date": "value",
                            "total_amount": "value",
                            "payment_terms": "value",
                            ... (other headers found)
                        }},
                        "line_items_found": true/false,
                        "missing_sections": ["section1", "section2", ...],
                        "is_complete_po": true/false,
                        "corrected_text": "full corrected text if needed"
                    }}

                    Note: Be strict in your assessment. Only mark fields as found if they are explicitly present and clearly readable.
                    """

        # Make the API call
        try:
            payload = {
                "model": "gpt-4-turbo",  # or another suitable model
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.openai_headers,
                json=payload,
            )
            response.raise_for_status()

            # Parse the response
            result = response.json()
            validation = json.loads(result["choices"][0]["message"]["content"])

            # Add metadata to validation result
            validation["file"] = pdf_name
            validation["validation_performed"] = True
            validation["expected_headers"] = common_po_headers

            # Calculate header detection metrics
            if "headers_found" in validation:
                found_headers = len(validation["headers_found"])
                expected_headers = len(common_po_headers)
                validation["header_detection_rate"] = (
                    found_headers / expected_headers if expected_headers > 0 else 0
                )

            # Save validation results in the PDF-specific directory
            validation_file = os.path.join(pdf_output_dir, "po_validation_results.json")
            with open(validation_file, "w", encoding="utf-8") as f:
                json.dump(validation, f, indent=2)

            # Save corrected text if available to PDF-specific directory
            if validation.get("corrected_text"):
                corrected_file = os.path.join(pdf_output_dir, "po_corrected_text.txt")
                with open(corrected_file, "w", encoding="utf-8") as f:
                    f.write(validation["corrected_text"])
                validation["corrected_text_file"] = corrected_file
                self.log.info(f"Saved corrected text to {corrected_file}")

            self.log.info(f"Purchase order validation results saved to {validation_file}")
            return validation

        except Exception as e:
            self.log.error(f"Error validating purchase order with OpenAI: {e!s}")
            error_result = {"error": str(e), "file": pdf_name, "validation_performed": False}

            # Save error information in the PDF-specific directory
            error_file = os.path.join(pdf_output_dir, "po_validation_error.json")
            with open(error_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2)

            return error_result
