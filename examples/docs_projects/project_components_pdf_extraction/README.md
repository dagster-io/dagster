# PDF Extraction Component

A Dagster component for extracting and validating text from PDF documents using OCR and AI-powered validation. This component provides a complete pipeline for processing PDFs, converting them to high-quality images, performing OCR text extraction, and validating the extraction quality using OpenAI.

![Asset Lineage](examples/docs_projects/project_components_pdf_extraction/_static/Global-Asset-Lineage.svg)

## Features

- 📄 PDF to Image Conversion: High-quality conversion with configurable DPI
- 🔍 OCR Text Extraction: Using Tesseract with preprocessing for improved accuracy
- 🤖 AI-Powered Validation: OpenAI-based validation of extraction quality
- 📊 Detailed Metrics: Comprehensive extraction and validation metrics
- 🔄 Batch Processing: Support for processing multiple PDFs
- 📁 Organized Output: Structured output directory for each PDF

## Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed on your system
- OpenAI API key for validation features
- Poppler (for PDF to image conversion)

### Installing Tesseract

#### macOS

```bash
brew install tesseract
```

#### Windows

Download and install from [GitHub Tesseract Releases](https://github.com/UB-Mannheim/tesseract/wiki)

### Installing Poppler

#### macOS

```bash
brew install poppler
```

#### Windows

Download and install from [Poppler Releases](http://blog.alivate.com.au/poppler-windows/)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/dagster-io/dagster.git
cd dagster/examples/docs_projects/project_components_pdf_extraction
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:

```bash
uv pip install -e ".[dev]"
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Component

This project uses Dagster Components Yaml Front end to simplify deploying a new pipeline.

```yaml
components:
  pdf_extraction:
    type: pdf_extraction.lib.pdf_extraction.PdfExtraction
    config:
      pdf_dir: path/to/your/pdfs # Directory containing PDF files to process
      output_dir: path/to/output # Base output directory for all PDFs
      language: eng # OCR language
      dpi: 300 # Image DPI for PDF conversion
      openai_model: gpt-4-turbo # OpenAI model to use
      validation_score: 7 # Minimum validation score threshold
```

## Usage

1. Place your PDF files in the configured `pdf_dir`

2. Run the Dagster pipeline:

```bash
dg dev
```

3. Open the Dagster UI (typically at http://localhost:3000)

4. Launch the PDF extraction job for your files

## Output Structure

For each PDF, the component creates the following structure in your output directory:

```
output/
└── pdf_name/
    ├── page_1.png
    ├── page_2.png
    ├── ...
    ├── page_1_preprocessed.png
    ├── page_2_preprocessed.png
    ├── ...
    ├── extracted_text.txt
    ├── extracted_text.md
    ├── conversion_metadata.json
    └── extraction_metadata.json
```

## Asset Pipeline

The component creates the following assets for each PDF:

- `{pdf_name}_convert_to_image`: Converts PDF pages to high-quality images
- `{pdf_name}_extract_text`: Extracts text from the images using OCR
- Asset check on extract_text: Validates extraction quality using OpenAI

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for validation features
