import os
import argparse
import json
import re
import textwrap
from pathlib import Path
import google.generativeai as genai
from PIL import Image

# Configure API Key
# Expects GEMINI_API_KEY in environment variables
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def extract_json_from_text(text):
    """Extracts JSON block from text."""
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL) # Fallback
    if match:
         # Try to parse to see if it's valid JSON
        try:
            json.loads(match.group(1))
            return match.group(1)
        except:
            pass
    # If no blocks, try to find start and end of json
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != -1:
            return text[start:end]
    except:
        pass
    return text

def extract_svg_from_text(text):
    """Extracts SVG block from text."""
    match = re.search(r'```svg\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'```xml\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        if "<svg" in match.group(1):
             return match.group(1)
    return None

def analyze_image(image_path, method):
    """Extracts information from image using Gemini."""
    model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for speed/cost, or Pro for quality
    
    img = Image.open(image_path)
    
    if method == "json":
        prompt = "Please extract this image as JSON structured data. Extract all visible information in the image as structured text."
    elif method == "json_svg":
        prompt = "Please extract this image as JSON structured data. Extract all visible information in the image as structured text. Then, also carefully convert the image details into SVG format."
    else:
        raise ValueError("Unknown method")

    response = model.generate_content([prompt, img])
    return response.text

def generate_image_from_text(text_prompt, output_path):
    """Generates an image using Imagen (via Gemini API) based on text."""
    # Note: As of late 2024/2025, image generation might be via a specific model like 'imagen-3.0-generate-001'
    # or similar available via the API.
    try:
        # Attempt to use the image generation model
        # Using a generic name, might need adjustment based on specific API availability at runtime
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        response = model.generate_images(
            prompt=text_prompt,
            number_of_images=1,
        )
        
        if response.images:
            response.images[0].save(output_path)
            print(f"Image saved to {output_path}")
        else:
            print("No image generated.")

    except Exception as e:
        print(f"Error generating image: {e}")
        # Fallback explanation if user doesn't have access to Imagen
        print("Note: Ensure your API key has access to Imagen models.")

def create_html(original_img, json_img, svg_img, json_text, svg_text, output_file="report.html"):
    """Generates an HTML report comparing results."""
    
    def read_file_safe(path):
        if path and os.path.exists(path):
            return Path(path).read_text(encoding='utf-8')
        return ""

    raw_json_text = read_file_safe(json_text)
    raw_svg_text = read_file_safe(svg_text)

    # Extract clean data for display
    json_display = extract_json_from_text(raw_json_text)
    
    # For the SVG method, we want to show both JSON and SVG if present
    svg_json_part = extract_json_from_text(raw_svg_text)
    svg_svg_part = extract_svg_from_text(raw_svg_text)
    
    if svg_json_part and svg_svg_part:
        svg_display = f"JSON:\n{svg_json_part}\n\nSVG:\n{svg_svg_part}"
    else:
        svg_display = raw_svg_text # Fallback to raw if extraction fails

    # Relative paths for HTML
    orig_rel = os.path.basename(original_img) if original_img else ""
    json_img_rel = os.path.basename(json_img) if json_img and os.path.exists(json_img) else ""
    svg_img_rel = os.path.basename(svg_img) if svg_img and os.path.exists(svg_img) else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Reconstruction Report</title>
        <style>
            body {{ font_family: sans-serif; margin: 20px; }}
            .container {{ display: flex; flex-direction: row; gap: 20px; flex-wrap: wrap; }}
            .card {{ border: 1px solid #ccc; padding: 10px; border-radius: 8px; max-width: 400px; width: 100%; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #eee; }}
            pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; max-height: 200px; white-space: pre-wrap; word-wrap: break-word; }}
        </style>
    </head>
    <body>
        <h1>Reconstruction Report</h1>
        <div class="container">
            <div class="card">
                <h2>Original</h2>
                <img src="{orig_rel}" alt="Original">
            </div>
    """
    
    if json_img_rel:
        html += f"""
            <div class="card">
                <h2>JSON Method</h2>
                <img src="{json_img_rel}" alt="JSON Reconstructed">
                <h3>Extracted Data</h3>
                <pre>{json_display}</pre>
            </div>
        """
        
    if svg_img_rel:
        html += f"""
            <div class="card">
                <h2>JSON + SVG Method</h2>
                <img src="{svg_img_rel}" alt="SVG Reconstructed">
                <h3>Extracted Data</h3>
                <pre>{svg_display}</pre>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w") as f:
        f.write(html)
    print(f"HTML report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Image to Text to Image Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    # Analyze
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("image_path")
    analyze_parser.add_argument("--method", choices=["json", "json_svg"], required=True)
    analyze_parser.add_argument("--output-text", required=True)

    # Generate Image
    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("input_text")
    gen_parser.add_argument("output_image")
    
    # Report
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--original", required=True)
    report_parser.add_argument("--json-img")
    report_parser.add_argument("--svg-img")
    report_parser.add_argument("--json-text")
    report_parser.add_argument("--svg-text")
    report_parser.add_argument("--output", default="report.html")

    args = parser.parse_args()

    if args.command == "analyze":
        raw_text = analyze_image(args.image_path, args.method)
        
        # Save raw output first
        with open(args.output_text, "w") as f:
            f.write(raw_text)
            
        print(f"Analysis complete. Saved to {args.output_text}")

    elif args.command == "generate":
        # Read the analysis text
        with open(args.input_text, "r") as f:
            content = f.read()
            
        # Refine prompt for generation
        prompt = f"Generate an image based on the following structured data/description:\n\n{content}"
        generate_image_from_text(prompt, args.output_image)

    elif args.command == "report":
        create_html(args.original, args.json_img, args.svg_img, args.json_text, args.svg_text, args.output)

if __name__ == "__main__":
    main()
