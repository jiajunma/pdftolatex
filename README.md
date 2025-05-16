# PDF-to-LaTeX Translator

Convert French academic papers from PDF to LaTeX format in English using Claude's vision capabilities.

## Overview

This tool extracts pages from a French PDF paper as images, processes them directly with Anthropic's Claude (which has vision capabilities), and converts the content to LaTeX format in English. It's particularly useful for researchers who need to translate and work with academic papers in LaTeX format.


## Features

- **PDF Page Extraction**: Converts PDF pages to high-quality images
- **French to English Translation**: Translates academic content with proper terminology
- **LaTeX Conversion**: Generates well-formatted LaTeX code

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key with access to Claude models with vision capabilities

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/jiajunma/pdftolatex.git
   cd pdftolatex
   ```


2. Install required packages:
   ```
   pip install PyMuPDF Pillow anthropic tqdm
   ```


3. Set up your Anthropic API key:

   For Linux/macOS:
   ```bash
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export ANTHROPIC_MODEL="claude-3-sonnet-latest"
   ```

   For Windows (Command Prompt):
   ```
   set ANTHROPIC_API_KEY=your_anthropic_api_key
   set ANTHROPIC_MODEL=claude-3-sonnet-latest
   ```

   For Windows (PowerShell):
   ```
   $env:ANTHROPIC_API_KEY="your_anthropic_api_key"
   $env:ANTHROPIC_MODEL="claude-3-sonnet-latest"
   ```

## Usage

### Basic Usage

```bash
python pdf2latex.py path/to/your/french_paper.pdf
```

This will process the entire PDF and save the output as `french_paper_translated_en.tex`.

### Advanced Options

```bash
python pdf2latex.py path/to/your/french_paper.pdf --output translated_paper.tex --dpi 400 --start-page 0 --end-page 5 --batch-size 3
```

### Parameters

- `pdf_path`: Path to the input PDF file (required)
- `--output`: Output LaTeX file path (default: input_filename_translated_en.tex)
- `--dpi`: DPI for image extraction (default: 300)
- `--start-page`: First page to process, 0-indexed (default: 0)
- `--end-page`: Last page to process, 0-indexed (default: last page)
- `--batch-size`: Number of pages to process in one batch (default: all pages)

### Testing Your Setup

To verify your API key and environment are set up correctly:

```bash
python test_claude_vision.py
```

## How It Works

1. **PDF Processing**: The tool extracts each page of the PDF as a high-resolution image
2. **Vision Analysis**: Claude analyzes the image to understand text, layout, tables, and formulas
3. **Translation**: The content is translated from French to English
4. **LaTeX Generation**: The translated content is formatted as LaTeX code
5. **Document Assembly**: All pages are combined into a complete LaTeX document

## Recommended Models

- **claude-3-sonnet-latest**: Recommended default model - good balance of quality and speed

## Troubleshooting

### Authentication Errors

If you encounter authentication errors:

1. **Check API Key Format**: Make sure your API key is correctly formatted
2. **Environment Variables**: Verify the environment variable is properly set
3. **Run the test script**: Use `test_claude_vision.py` to verify your setup



## License

This project is licensed under the MIT License 


