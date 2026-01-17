import os
import argparse
import json
import re
from pathlib import Path
from google import genai
from PIL import Image

# Configure API Key
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY environment variable not set.")
    exit(1)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def extract_json_from_text(text):
    """Extracts JSON block from text."""
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL) # Fallback
    if match:
        try:
            json.loads(match.group(1))
            return match.group(1)
        except:
            pass
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

def list_available_models():
    """Lists available models to help the user debug."""
    print("\n--- Available Models ---")
    try:
        # Pager object is iterable
        for model in client.models.list():
            print(f"- {model.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
    print("------------------------\n")

def analyze_image(image_path, method):
    """Extracts information from image using Gemini."""
    img = Image.open(image_path)
    
    if method == "json":
        prompt = "Please extract this image as JSON structured data. Extract all visible information in the image as structured text."
    elif method == "json_svg":
        prompt = "Please extract this image as JSON structured data. Extract all visible information in the image as structured text. Then, also carefully convert the image details into SVG format."
    else:
        raise ValueError("Unknown method")

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash', # Using 2.0 Flash as it's the current recommended
            contents=[prompt, img]
        )
        return response.text
    except Exception as e:
        print(f"Error analyzing image: {e}")
        list_available_models()
        exit(1)

def generate_image_from_text(text_prompt, output_path):
    """Generates an image using Gemini's image generation capabilities."""
    try:
        # Using gemini-2.0-flash or appropriate experimental image model
        # Note: Depending on the specific API version, 'gemini-2.0-flash' 
        # or a specific 'gemini-2.0-flash-image' (experimental) might be used.
        # We will use 'gemini-2.0-flash' as it's widely available.
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=[text_prompt]
        )
        
        saved = False
        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                image.save(output_path)
                print(f"Image saved to {output_path}")
                saved = True
                break
        
        if not saved:
            print("No image data found in the response parts.")
            # Print text parts if any, for debugging
            if response.parts:
                for part in response.parts:
                    if part.text:
                        print(f"Model response text: {part.text}")
            else:
                 print("Response contained no parts.")

    except Exception as e:
        print(f"Error generating image: {e}")
        print("Note: Ensure your API key has access to the requested model and image generation features.")
        list_available_models()

def create_html(original_img, json_img, svg_img, json_text, svg_text, output_file="report.html"):
    """Generates an HTML report comparing results."""
    
    def read_file_safe(path):
        if path and os.path.exists(path):
            return Path(path).read_text(encoding='utf-8')
        return ""

    raw_json_text = read_file_safe(json_text)
    raw_svg_text = read_file_safe(svg_text)

    json_display = extract_json_from_text(raw_json_text)
    svg_json_part = extract_json_from_text(raw_svg_text)
    svg_svg_part = extract_svg_from_text(raw_svg_text)
    
    if svg_json_part and svg_svg_part:
        svg_display = f"JSON:\n{svg_json_part}\n\nSVG:\n{svg_svg_part}"
    else:
        svg_display = raw_svg_text

    orig_rel = os.path.basename(original_img) if original_img else ""
    json_img_rel = os.path.basename(json_img) if json_img and os.path.exists(json_img) else ""
    svg_img_rel = os.path.basename(svg_img) if svg_img and os.path.exists(svg_img) else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Image Reconstruction Report</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
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

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("image_path")
    analyze_parser.add_argument("--method", choices=["json", "json_svg"], required=True)
    analyze_parser.add_argument("--output-text", required=True)

    gen_parser = subparsers.add_parser("generate")
    gen_parser.add_argument("input_text")
    gen_parser.add_argument("output_image")
    
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
        with open(args.output_text, "w") as f:
            f.write(raw_text)
        print(f"Analysis complete. Saved to {args.output_text}")

    elif args.command == "generate":
        with open(args.input_text, "r") as f:
            content = f.read()
        prompt = f"Generate an image based on the following structured data/description:\n\n{content}"
        generate_image_from_text(prompt, args.output_image)

    elif args.command == "report":
        create_html(args.original, args.json_img, args.svg_img, args.json_text, args.svg_text, args.output)

if __name__ == "__main__":
    main()
