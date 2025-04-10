import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any
import logging

import dagster as dg
import pytesseract
import requests
from dagster_components import (
    Component,
    ComponentLoadContext,
    Scaffolder,
    Resolvable,
    ResolvedAssetSpec,
    ScaffoldRequest,
)
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

class PDFTextExtractor(dg.ConfigurableResource):
    def __init__(self, language="eng", dpi=300, openai_api_key=None, preprocess=True):
        """Initialize the PDF processor resource.

        Args:
            language: OCR language (default: 'eng')
            dpi: DPI for PDF conversion (default: 300)
            openai_api_key: OpenAI API key for validation (optional)
            preprocess: Whether to preprocess images (default: True)
        """
        self.language = language
        self.dpi = dpi
        self.openai_api_key = openai_api_key
        self.preprocess = preprocess

        # Set up OpenAI headers if API key is available
        if self.openai_api_key:
            self.openai_headers = {
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
        self.logger.info(f"Preprocessing image: {image_path}")

        # Load the image
        image = Image.open(image_path)

        # Convert to grayscale
        image = image.convert("L")

        # 1. Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast by factor of 2

        # 2. Apply threshold
        threshold = 200  # Threshold value (0-255)
        image = image.point(lambda p: 255 if p > threshold else 0)

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
            self.logger.info(f"Saved preprocessed image to {preprocessed_path}")

            return image, preprocessed_path

        return image, None

    def convert_pdf_to_images(
        self, pdf_path: str, output_folder: str = None, pages: list[int] = None
    ) -> dict[str, Any]:
        """Convert PDF to images and save them to a folder.

        Args:
            pdf_path: Path to the PDF file
            output_folder: Custom output folder path. If None, creates folder with PDF name
            pages: List of page numbers to extract (0-based). If None, extract all pages

        Returns:
            Dictionary with conversion results
        """
        self.logger.info(f"Converting PDF to images: {pdf_path}")

        # Check if file exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output folder
        pdf_basename = os.path.basename(pdf_path)
        pdf_name = os.path.splitext(pdf_basename)[0]

        if not output_folder:
            output_folder = os.path.join(os.path.dirname(pdf_path), pdf_name)

        # Create folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Convert PDF to images
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=pages[0] + 1 if pages else None,
                last_page=pages[-1] + 1 if pages else None,
            )
            self.logger.info(f"Converted {len(images)} pages to images")
        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {e!s}")
            raise

        # Save images to folder
        image_paths = []
        image_metadata = []

        for i, image in enumerate(images):
            page_num = pages[i] if pages else i
            page_number = page_num + 1  # 1-based page numbering

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
            "file": pdf_basename,
            "images_folder": output_folder,
            "total_pages": len(images),
            "image_paths": image_paths,
            "images": image_metadata,
        }

        # Save metadata to folder
        metadata_path = os.path.join(output_folder, "conversion_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.logger.info(f"Images saved to {output_folder}")
        return result

    def extract_text_from_images(self, conversion_result: dict[str, Any]) -> dict[str, Any]:
        """Extract text from images using Tesseract OCR.

        Args:
            conversion_result: Result dictionary from convert_pdf_to_images

        Returns:
            Dictionary with extraction results
        """
        self.logger.info("Extracting text using OCR")

        images_folder = conversion_result["images_folder"]
        image_paths = conversion_result["image_paths"]

        results = []
        preprocessed_paths = []

        # Process each image
        for i, image_path in enumerate(image_paths):
            page_number = i + 1  # 1-based page numbering
            self.logger.info(f"Processing page {page_number}/{len(image_paths)}")

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
                self.logger.error(f"OCR error on page {page_number}: {e!s}")
                results.append(
                    {"page": page_number, "text": "", "error": str(e), "image_path": image_path}
                )

        # Create output
        extraction_result = {
            "file": conversion_result["file"],
            "images_folder": images_folder,
            "total_pages": conversion_result["total_pages"],
            "pages": results,
            "preprocessed_paths": preprocessed_paths,
        }

        # Save extracted text to folder
        all_text = ""
        for page in results:
            all_text += f"--- Page {page['page']} ---\n"
            all_text += page["text"]
            all_text += "\n\n"

        text_file = os.path.join(images_folder, "extracted_text.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(all_text)

        # Save extraction metadata
        extraction_metadata_path = os.path.join(images_folder, "extraction_metadata.json")
        with open(extraction_metadata_path, "w", encoding="utf-8") as f:
            # Create a copy without the full text to keep metadata file smaller
            metadata = extraction_result.copy()
            for page in metadata["pages"]:
                page["text_length"] = len(page.get("text", ""))
                if "text" in page and len(page["text"]) > 100:
                    page["text"] = page["text"][:100] + "..."
            json.dump(metadata, f, indent=2)

        extraction_result["text_file"] = text_file
        self.logger.info(f"Text extracted and saved to {text_file}")
        return extraction_result

    def validate_with_openai(
        self, extraction_result: dict[str, Any], context: str = "", expected_info: list[str] = None
    ) -> dict[str, Any]:
        """Validate extraction using OpenAI.

        Args:
            extraction_result: Result dictionary from extract_text_from_images
            context: Context description of the document
            expected_info: List of expected information items

        Returns:
            Dictionary with validation results
        """
        logger.info("Validating extraction with OpenAI")

        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided. Skipping validation.")
            return {
                "error": "No OpenAI API key provided",
                "file": extraction_result["file"],
                "validation_performed": False,
            }

        # Read the full text
        with open(extraction_result["text_file"], encoding="utf-8") as f:
            all_text = f.read()

        # Prepare the prompt with context and expected information
        expected_info_str = ""
        if expected_info:
            expected_info_str = "The document should contain information about: "
            expected_info_str += ", ".join(expected_info)

        context_str = f"Document context: {context}\n" if context else ""

        prompt = f"""I need you to validate and improve text extracted from a PDF using OCR.

                {context_str}
                {expected_info_str}

                Please analyze the following extracted text:

                {all_text}

                Please provide:
                1. An assessment of OCR quality (scale 1-10)
                2. Identified OCR errors
                3. Corrected text where possible
                4. List of key information found
                5. Assessment of whether expected information was found

                Return your analysis in JSON format.
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
            validation["file"] = extraction_result["file"]
            validation["validation_performed"] = True

            # Save validation results
            images_folder = extraction_result["images_folder"]
            validation_file = os.path.join(images_folder, "validation_results.json")
            with open(validation_file, "w", encoding="utf-8") as f:
                json.dump(validation, f, indent=2)

            # Save corrected text if available
            corrected_file = None
            if validation.get("corrected_text"):
                corrected_file = os.path.join(images_folder, "corrected_text.txt")
                with open(corrected_file, "w", encoding="utf-8") as f:
                    f.write(validation["corrected_text"])

                validation["corrected_text_file"] = corrected_file
                logger.info(f"Saved corrected text to {corrected_file}")

            logger.info(f"Validation results saved to {validation_file}")
            return validation

        except Exception as e:
            logger.error(f"Error validating with OpenAI: {e!s}")
            error_result = {
                "error": str(e),
                "file": extraction_result["file"],
                "validation_performed": False,
            }

            # Save error information
            images_folder = extraction_result["images_folder"]
            error_file = os.path.join(images_folder, "validation_error.json")
            with open(error_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2)

            return error_result


class PdfExtraction(Component, Resolvable):
    """A component for extracting and validating text from PDF documents.

    This component provides a complete PDF text extraction pipeline that:
    1. Converts PDF pages to high-quality images
    2. Performs OCR text extraction using Tesseract
    3. Validates extraction quality using OpenAI
    4. Generates detailed extraction reports and metrics

    The component creates three main assets:
    - {pdf_name}_convert_to_image: Converts PDF pages to images
    - {pdf_name}_extract_text: Extracts text from the images using OCR
    - Asset check on extract_text: Validates extraction quality using OpenAI

    Configuration:
        pdf_path (str): Path to the PDF document to process
        output_dir (str): Directory for storing extracted images and text
        asset_specs (Sequence[ResolvedAssetSpec]): Asset specifications for the pipeline
        language (str): OCR language code (e.g., 'eng' for English)
        dpi (int): DPI resolution for PDF to image conversion
        openai_api_key (str): OpenAI API key for validation
        openai_model (str): OpenAI model to use for validation
        validation_score (int): Minimum acceptable validation score (1-10)
    """

    def __init__(
        self,
        pdf_path: str,
        output_dir: str,
        asset_specs: Sequence[ResolvedAssetSpec],
        language: str,
        dpi: int,
        openai_api_key: str,
        openai_model: str,
        validation_score: int,
    ):
        self.pdf_path = pdf_path
        self.asset_specs = asset_specs

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # Create the PDF extractor resource
        pdf_extractor_resource = PDFTextExtractor(
            language="eng", dpi=300, openai_api_key=dg.EnvVar("OPENAI_API_KEY")
        )

        @dg.asset(name=f"{Path(self.pdf_path).stem}_convert_to_image", specs=self.asset_specs)
        def convert_to_image(context: dg.AssetExecutionContext, pdf_extractor: PDFTextExtractor):
            """Convert PDF to images, one per page."""
            conversion_result = pdf_extractor.convert_pdf_to_images(self.pdf_path)
            return conversion_result

        @dg.asset(
            name=f"{Path(self.pdf_path).stem}_extract_text",
            specs=self.asset_specs,
            deps=[f"{Path(self.pdf_path).stem}_convert_to_image"],
        )
        def extract_text(
            context: dg.AssetExecutionContext, pdf_extractor: PDFTextExtractor, convert_to_image
        ):
            """Extract text from the converted images using OCR."""
            extraction_result = pdf_extractor.extract_text_from_images(convert_to_image)
            return extraction_result

        @dg.asset_check(
            asset_name=f"{Path(self.pdf_path).stem}_extract_text",
            name=f"{Path(self.pdf_path).stem}_validate_extraction_quality",
        )
        def check_extraction_quality(
            context: dg.AssetCheckContext, pdf_extractor: PDFTextExtractor
        ):
            """Validate the extracted text quality using OpenAI."""
            # Get the asset value (extraction result)
            extraction_result = context.asset_value

            # Validate with OpenAI
            validation_result = pdf_extractor.validate_with_openai(
                extraction_result,
                context="PDF document text extraction validation",
                expected_info=["document content", "text quality", "completeness"],
            )

            # Check if validation was performed successfully
            if not validation_result.get("validation_performed", False):
                return dg.AssetCheckResult(
                    success=False,
                    metadata={"error": validation_result.get("error", "Unknown validation error")},
                )

            # Get the OCR quality score from validation
            ocr_quality_score = validation_result.get("ocr_quality_score", 0)

            # Consider the check successful if quality score is 7 or higher
            success = ocr_quality_score >= 7

            return dg.AssetCheckResult(
                success=success,
                metadata={
                    "ocr_quality_score": ocr_quality_score,
                    "identified_errors": validation_result.get("identified_errors", []),
                    "key_information_found": validation_result.get("key_information_found", []),
                },
            )

        return dg.Definitions(
            assets=[convert_to_image, extract_text],
            asset_checks=[check_extraction_quality],
            resources={"pdf_extractor": pdf_extractor_resource},
        )


class PdfExtractionScaffolder(Scaffolder):
    """Scaffolder for PdfExtraction component."""

    @property
    def default_format(self) -> str:
        """Override to always use YAML format."""
        return "yaml"
    
    def scaffold(self, request: ScaffoldRequest) -> str:
        """Generate scaffold code for PdfExtraction component."""
        return f"""# PDF Extraction Component Configuration
        components:
        pdf_extraction:
            type: pdf_extraction.lib.pdf_extraction.PdfExtraction
            config:
            pdf_path: path/to/your/document.pdf  # Replace with actual PDF path
            output_dir: path/to/output  # Replace with desired output directory
            language: eng  # OCR language
            dpi: 300  # Image DPI for PDF conversion
            openai_api_key: {{ env: OPENAI_API_KEY }}  # Use environment variable
            openai_model: gpt-4-turbo  # OpenAI model to use
            validation_score: 7  # Minimum validation score threshold
            asset_specs:
                - key: {request.asset_key}
                group_name: {request.group_name}
        """

    @property
    def description(self) -> str:
        return """
        Scaffolds a PdfExtraction component that:
        1. Converts PDF documents to images
        2. Extracts text using OCR
        3. Validates extraction quality using OpenAI
        
        Required configuration:
        - pdf_path: Path to the PDF document to process
        - output_dir: Directory for output files
        - openai_api_key: API key for OpenAI validation (uses environment variable)
        - asset_specs: Asset specifications for the pipeline
        """

    def example_code(self) -> str:
        return """
                components:
                pdf_extraction:
                    type: pdf_extraction.lib.pdf_extraction.PdfExtraction
                    config:
                    pdf_path: /path/to/document.pdf
                    output_dir: /path/to/output
                    language: eng
                    dpi: 300
                    openai_api_key: { env: OPENAI_API_KEY }
                    openai_model: gpt-4-turbo
                    validation_score: 7
                    asset_specs:
                        - key: pdf_text_extraction
                        group_name: document_processing
                """
