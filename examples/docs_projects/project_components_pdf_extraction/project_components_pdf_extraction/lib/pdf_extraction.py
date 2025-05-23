import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import dagster as dg

from .pdf_extraction_resource import PDFTextExtractor


class PdfExtractionScaffolder(dg.Scaffolder):
    """Scaffolds a PDF extraction component with configuration and example PDFs."""

    def scaffold(self, request: dg.ScaffoldRequest) -> None:
        """Generate scaffold code for PdfExtraction component.

        Args:
            request: The scaffold request containing type name, target path, format, project root and optional params
        """
        # Default configuration values
        config = {
            "pdf_dir": "source_pdfs",
            "output_dir": "output",
            "language": "eng",
            "dpi": 300,
            "openai_model": "gpt-4-turbo",
            "validation_score": 7,
            "asset_specs": [],
        }

        # Create the component YAML using scaffold_component
        dg.scaffold_component(request, config)

    @property
    def description(self) -> str:
        return """Scaffolds a PdfExtraction component that:
        1. Processes multiple PDF documents from a directory
        2. Converts PDFs to images
        3. Extracts text using OCR
        4. Validates extraction quality using OpenAI

        Required configuration:
        - pdf_dir: Directory containing PDF files to process
        - output_dir: Base directory for output files
        - openai_api_key: API key for OpenAI validation (uses environment variable)

        Optional configuration:
        - language: OCR language code (default: 'eng')
        - dpi: Image DPI for PDF conversion (default: 300)
        - openai_model: OpenAI model to use (default: 'gpt-4-turbo')
        - validation_score: Minimum validation score threshold (default: 7)
        """


@dg.scaffold_with(PdfExtractionScaffolder)
@dataclass
class PdfExtraction(dg.Component, dg.Resolvable):
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

    pdf_dir: str
    output_dir: str
    asset_specs: Sequence[dg.ResolvedAssetSpec]
    validation_score: int = 7
    language: str = "eng"
    dpi: int = 300
    openai_model: str = "gpt-4o-mini"

    def _normalize_key(self, key: str) -> str:
        return key.replace("-", "_")

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Initialize pdf_paths as an empty list
        pdf_paths = []

        # Get all PDF files from the directory
        if os.path.isdir(self.pdf_dir):
            pdf_files = [f for f in os.listdir(self.pdf_dir) if f.lower().endswith(".pdf")]
            pdf_paths = [os.path.join(self.pdf_dir, pdf) for pdf in pdf_files]

        # Create single shared PDF extractor resource
        pdf_extractor_resource = PDFTextExtractor(
            language=self.language,
            dpi=self.dpi,
            openai_api_key=dg.EnvVar("OPENAI_API_KEY"),
            preprocess=True,
            output_dir=self.output_dir,  # Base output directory
        )

        assets = []
        asset_checks = []
        all_jobs = []

        # Create assets for each PDF file
        for pdf_path in pdf_paths:
            key_prefix = self._normalize_key(f"{Path(pdf_path).stem}")

            # Create convert_to_image asset with captured pdf_path
            def _make_convert_to_image(pdf_path=pdf_path, key_prefix=key_prefix):
                @dg.asset(
                    name=f"{key_prefix}_convert_to_image",
                    group_name="pdf_extraction",
                )
                def convert_to_image(
                    context: dg.AssetExecutionContext, pdf_extractor: PDFTextExtractor
                ):
                    """Convert PDF to images, one per page."""
                    return pdf_extractor.convert_pdf_to_images(
                        pdf_path, output_folder=os.path.join(self.output_dir, key_prefix)
                    )

                return convert_to_image

            # Create extract_text asset with captured key_prefix
            def _make_extract_text(key_prefix=key_prefix, pdf_path=pdf_path):
                @dg.asset(
                    name=f"{key_prefix}_extract_text",
                    deps=[f"{key_prefix}_convert_to_image"],
                    group_name="pdf_extraction",
                )
                def extract_text(
                    context: dg.AssetExecutionContext, pdf_extractor: PDFTextExtractor
                ):
                    """Extract text from the converted images using OCR."""
                    context.log.info(f"Extracting text for PDF: {key_prefix}")

                    # Define the output directory and ensure it exists
                    pdf_output_dir = os.path.join(self.output_dir, key_prefix)

                    # Extract text and save directly to output directory
                    extraction_result = pdf_extractor.extract_text_from_images(key_prefix)

                    # Format the extracted text as markdown
                    markdown_text = f"# Extracted Text from {Path(pdf_path).name}\n\n"
                    for page in extraction_result["pages"]:
                        markdown_text += f"## Page {page['page']}\n\n"
                        markdown_text += f"{page['text']}\n\n"

                    # Save markdown version to output directory
                    markdown_file = os.path.join(pdf_output_dir, "extracted_text.md")
                    with open(markdown_file, "w", encoding="utf-8") as f:
                        f.write(markdown_text)

                    return dg.Output(
                        value=extraction_result,
                        metadata={
                            "text": dg.MetadataValue.md(markdown_text),
                            "total_pages": dg.MetadataValue.int(extraction_result["total_pages"]),
                            "file_name": dg.MetadataValue.text(extraction_result["file"]),
                            "output_directory": dg.MetadataValue.path(pdf_output_dir),
                            "markdown_file": dg.MetadataValue.path(markdown_file),
                            "text_file": dg.MetadataValue.path(
                                os.path.join(pdf_output_dir, "extracted_text.txt")
                            ),
                        },
                    )

                return extract_text

            # Create asset check with captured key_prefix
            def _make_check_extraction_quality(key_prefix=key_prefix):
                @dg.asset_check(asset=f"{key_prefix}_extract_text")
                def check_extraction_quality(pdf_extractor: PDFTextExtractor):
                    """Validate the extracted text quality using OpenAI."""
                    validation_result = pdf_extractor.validate_purchase_order(
                        key_prefix,
                        expected_fields=["document content", "text quality", "completeness"],
                    )

                    if not validation_result.get("validation_performed", False):
                        return dg.AssetCheckResult(
                            passed=False,
                            metadata={
                                "error": validation_result.get("error", "Unknown validation error")
                            },
                        )

                    ocr_quality_score = validation_result.get("ocr_quality", 0)
                    passed = ocr_quality_score >= self.validation_score

                    return dg.AssetCheckResult(
                        passed=passed,
                        metadata={
                            "ocr_quality_score": dg.MetadataValue.int(ocr_quality_score),
                            "identified_errors": dg.MetadataValue.json(
                                validation_result.get("identified_errors", [])
                            ),
                            "key_information_found": dg.MetadataValue.json(
                                validation_result.get("key_information_found", [])
                            ),
                            "headers_found": dg.MetadataValue.json(
                                validation_result.get("headers_found", {})
                            ),
                            "missing_sections": dg.MetadataValue.json(
                                validation_result.get("missing_sections", [])
                            ),
                            "is_complete_po": dg.MetadataValue.bool(
                                validation_result.get("is_complete_po", False)
                            ),
                        },
                    )

                return check_extraction_quality

            # Create job for this PDF
            pdf_job = dg.define_asset_job(
                name=f"{key_prefix}_extraction_job",
                selection=[f"{key_prefix}_convert_to_image", f"{key_prefix}_extract_text"],
            )

            # Add assets, checks, and job to their respective lists
            assets.extend([_make_convert_to_image(), _make_extract_text()])
            asset_checks.append(_make_check_extraction_quality())
            all_jobs.append(pdf_job)

        # Create a job that processes all PDFs
        asset_names = []
        for key_prefix in [self._normalize_key(Path(pdf).stem) for pdf in pdf_paths]:
            asset_names.extend([f"{key_prefix}_convert_to_image", f"{key_prefix}_extract_text"])

        all_pdfs_job = dg.define_asset_job(name="process_all_pdfs", selection=asset_names)
        all_jobs.append(all_pdfs_job)

        return dg.Definitions(
            assets=assets,
            asset_checks=asset_checks,
            jobs=all_jobs,
            resources={
                "pdf_extractor": pdf_extractor_resource,
            },
        )
