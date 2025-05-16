import os
import io
import base64
import argparse
import fitz  # PyMuPDF
from PIL import Image
import anthropic
from tqdm import tqdm
import time
import sys
import mimetypes

# Configure API key from system environment variables
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

# Initialize Anthropic client
if ANTHROPIC_API_KEY:
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def check_environment():
    """Check if all required environment variables are set."""
    missing_vars = []
    
    if not ANTHROPIC_API_KEY:
        missing_vars.append("ANTHROPIC_API_KEY")
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your system environment.")
        return False
    
    return True

def extract_pages_as_images(pdf_path, dpi=300):
    """Extract pages from PDF as images."""
    images = []
    try:
        doc = fitz.open(pdf_path)
        print(f"Extracting {len(doc)} pages as images...")
        for page_num in tqdm(range(len(doc))):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except Exception as e:
        print(f"Error extracting images from PDF: {e}")
        return []

def get_image_base64_and_mime(image):
    """Convert PIL Image to base64 and determine MIME type."""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    mime_type = "image/png"
    return img_str, mime_type

def translate_and_convert_to_latex_with_claude_vision(image, page_num):
    """Use Claude's vision capabilities to translate French content to English and convert to LaTeX."""
    try:
        # Convert image to base64
        img_str, mime_type = get_image_base64_and_mime(image)
        
        # Create prompt for Claude
        prompt = f"""
        You are looking at page {page_num+1} of a French academic paper. 
        
        Your task:
        1. Analyze the image and extract all text content, including any tables and mathematical formulas.
        2. Translate the French text to English.
        3. Convert the entire content to proper LaTeX format.
        4. Preserve the document structure (headings, paragraphs, etc.).
        5. Convert tables to LaTeX table environments.
        6. Ensure mathematical formulas are properly formatted in LaTeX math environments.
        7. Return ONLY the LaTeX code without explanations.
        8. Don't put \\begin{{document}} and \\end{{document}} in your response.
        9. filled or unfilled square box in the end of the paragraph means \\end{{proof}}.
        """
        
        # Call Claude API with image
        response = claude_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4000,
            temperature=0.2,
            system="You are an expert translator and LaTeX formatter specialized in academic papers.",
            messages=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": img_str,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Error in Claude processing: {e}")
        return f"% Error processing page {page_num+1}\n% {str(e)}\n\n"

def combine_latex_pages(latex_pages):
    """Combine individual LaTeX pages into a complete document."""
    # Basic LaTeX document structure
    preamble = """
\\documentclass{amsart}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{graphicx}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage{hyperref}
\\usepackage{natbib}
\\usepackage{booktabs}
\\usepackage{float}
\\usepackage{array}
\\usepackage{multirow}
\\usepackage{longtable}
\\usepackage{mathrsfs}


\\begin{document}

\\maketitle
"""
    
    # Combine all pages
    content = "\n\n% ===== NEW PAGE =====\n\n".join(latex_pages)
    
    # End document
    postamble = "\n\n\\end{document}"

    
    return preamble + content + postamble

def main():
    # Check environment variables
    if not check_environment():
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description='Convert French PDF to English LaTeX using Claude with Vision')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('--output', help='Output LaTeX file path', default=None)
    parser.add_argument('--dpi', help='DPI for image extraction', type=int, default=300)
    parser.add_argument('--start-page', help='Start page (0-indexed)', type=int, default=0)
    parser.add_argument('--end-page', help='End page (0-indexed, inclusive)', type=int, default=None)
    parser.add_argument('--batch-size', help='Number of pages to process in one batch', type=int, default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: File {args.pdf_path} not found.")
        sys.exit(1)
    
    # Set default output path if not provided
    if args.output is None:
        base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
        args.output = f"{base_name}_translated_en.tex"
    
    # Extract pages as images
    images = extract_pages_as_images(args.pdf_path, dpi=args.dpi)
    if not images:
        sys.exit(1)
    
    # Apply page range if specified
    start_page = args.start_page
    end_page = args.end_page if args.end_page is not None else len(images) - 1
    
    if start_page < 0 or start_page >= len(images):
        print(f"Error: Start page {start_page} is out of range (0-{len(images)-1}).")
        sys.exit(1)
    
    if end_page < start_page or end_page >= len(images):
        print(f"Error: End page {end_page} is out of range ({start_page}-{len(images)-1}).")
        sys.exit(1)
    
    selected_images = images[start_page:end_page+1]
    
    # Process pages in batches if specified
    batch_size = args.batch_size or len(selected_images)
    num_batches = (len(selected_images) + batch_size - 1) // batch_size
    
    all_latex_pages = []
    
    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min((batch_idx + 1) * batch_size, len(selected_images))
        batch_images = selected_images[batch_start:batch_end]
        
        print(f"Processing batch {batch_idx+1}/{num_batches} (pages {start_page+batch_start+1}-{start_page+batch_end})...")
        
        # Process each page in the batch
        latex_pages = []
        for i, image in enumerate(tqdm(batch_images)):
            actual_page = start_page + batch_start + i
            
            # Process directly with Claude's vision capabilities
            latex_content = translate_and_convert_to_latex_with_claude_vision(image, actual_page)
            latex_pages.append(latex_content)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        all_latex_pages.extend(latex_pages)
        
        # Save intermediate results
        if num_batches > 1:
            batch_output = f"{os.path.splitext(args.output)[0]}_batch{batch_idx+1}.tex"
            batch_latex = combine_latex_pages(latex_pages)
            with open(batch_output, 'w', encoding='utf-8') as f:
                f.write(batch_latex)
            print(f"Batch {batch_idx+1} saved to: {batch_output}")
    
    # Combine all pages into a complete LaTeX document
    full_latex = combine_latex_pages(all_latex_pages)
    
    # Save to file
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(full_latex)
    
    print(f"Translation and conversion complete. LaTeX file saved to: {args.output}")

if __name__ == "__main__":
    main()