import os
import argparse
import json
import re
import shutil
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
        prompt = "First, please extract this image as JSON structured data in ```json block. Then, also carefully convert the image details into SVG format in ```svg block."
    else:
        raise ValueError("Unknown method")

    try:
        response = client.models.generate_content(
            model='gemini-3-pro-preview',
            contents=[prompt, img]
        )
        return response.text
    except Exception as e:
        print(f"Error analyzing image: {e}")
        list_available_models()
        raise e

def generate_image_from_text(text_prompt, output_path):
    """Generates an image using Gemini's image generation capabilities."""
    try:
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
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
        # We don't raise here to allow the pipeline to continue even if generation fails

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

    # Prepare paths and copy original image to output directory
    out_dir = os.path.dirname(output_file)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    orig_rel = ""
    if original_img and os.path.exists(original_img):
        orig_filename = os.path.basename(original_img)
        dest_path = os.path.join(out_dir, orig_filename)
        try:
            # Copy file if it's not the same file
            if os.path.abspath(original_img) != os.path.abspath(dest_path):
                shutil.copy2(original_img, dest_path)
            orig_rel = orig_filename
        except Exception as e:
            print(f"Warning: Could not copy original image: {e}")
            orig_rel = os.path.basename(original_img) # Fallback

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

    if svg_svg_part:
        html += f"""
            <div class="card">
                <h2>Extracted SVG Rendering</h2>
                <div style="border: 1px solid #eee; padding: 10px; background: white; display: flex; justify-content: center; align-items: center; min-height: 200px;">
                    {svg_svg_part}
                </div>
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

def batch_process(input_dir, output_dir):
    """Processes all images in a directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.bmp'}
    images = [f for f in input_path.iterdir() if f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"No images found in '{input_dir}'.")
        return

    print(f"Found {len(images)} images. Starting batch processing...")
    
    report_links = []

    for index, img_file in enumerate(images, 1):
        print(f"\n[{index}/{len(images)}] Processing {img_file.name}...")
        
        # Create a subfolder for this image's results
        # Use simple name to avoid filesystem issues
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', img_file.stem)
        img_out_dir = output_path / safe_name
        img_out_dir.mkdir(exist_ok=True)
        
        # Define paths
        json_text_path = img_out_dir / "analysis_json.txt"
        svg_text_path = img_out_dir / "analysis_svg.txt"
        json_img_path = img_out_dir / "reconstructed_json.png"
        svg_img_path = img_out_dir / "reconstructed_svg.png"
        report_path = img_out_dir / "report.html"
        
        try:
            # 1. Analyze JSON
            print("  - Analyzing (JSON)...")
            json_text = analyze_image(img_file, "json")
            json_text_path.write_text(json_text, encoding='utf-8')
            
            # 2. Analyze JSON+SVG
            print("  - Analyzing (JSON+SVG)...")
            svg_text = analyze_image(img_file, "json_svg")
            svg_text_path.write_text(svg_text, encoding='utf-8')
            
            # 3. Generate JSON Image
            print("  - Generating Image (JSON)...")
            prompt_json = f"Generate an image based on the following structured data/description:\n\n{json_text}"
            generate_image_from_text(prompt_json, json_img_path)
            
            # 4. Generate SVG Image
            print("  - Generating Image (JSON + SVG)...")
            
            # Try to extract clean JSON and SVG to verify we have both and structure the prompt
            svg_part_json = extract_json_from_text(svg_text)
            svg_part_svg = extract_svg_from_text(svg_text)
            
            # Check if extraction was successful 
            # (extract_json returns original text on failure, extract_svg returns None)
            has_json = svg_part_json and svg_part_json != svg_text
            has_svg = svg_part_svg is not None
            
            if has_json and has_svg:
                prompt_svg = (
                    "Generate an image based on the following combined information:\n\n"
                    f"1. JSON Description:\n{svg_part_json}\n\n"
                    f"2. SVG Structure:\n{svg_part_svg}"
                )
            else:
                # Fallback: use the raw text if we couldn't parse distinct blocks
                prompt_svg = f"Generate an image based on the following structured data (containing JSON and/or SVG):\n\n{svg_text}"
            
            generate_image_from_text(prompt_svg, svg_img_path)
            
            # 5. Report
            print("  - Creating Report...")
            create_html(str(img_file), str(json_img_path), str(svg_img_path), str(json_text_path), str(svg_text_path), str(report_path))
            
            # Store link for index
            # Use relative path from output_dir to report_path
            rel_link = f"{safe_name}/report.html"
            report_links.append((img_file.name, rel_link))
            
        except Exception as e:
            print(f"  - Error processing {img_file.name}: {e}")

    # Create Index HTML
    index_html = output_path / "index.html"
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Batch Processing Report</title>
        <style>
            body { font-family: sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; line-height: 1.6; }
            h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
            ul { list-style-type: none; padding: 0; }
            li { margin: 15px 0; background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #eee; }
            a { text-decoration: none; color: #007bff; font-weight: bold; font-size: 1.1em; }
            a:hover { text-decoration: underline; color: #0056b3; }
            .status { font-size: 0.9em; color: #666; margin-left: 10px; }
        </style>
    </head>
    <body>
        <h1>Batch Processing Index</h1>
        <p>Processed images from directory.</p>
        <ul>
    """
    for name, link in report_links:
        html_content += f'<li><a href="{link}">{name}</a> <span class="status">→ View Report</span></li>'
    
    if not report_links:
        html_content += "<li>No reports generated.</li>"

    html_content += "</ul></body></html>"
    
    index_html.write_text(html_content, encoding='utf-8')
    print(f"\nBatch processing complete. Index at: {index_html}")

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

    # Batch
    batch_parser = subparsers.add_parser("batch")
    batch_parser.add_argument("--input-dir", required=True, help="Directory containing images to process")
    batch_parser.add_argument("--output-dir", required=True, help="Directory to save reports and results")

    args = parser.parse_args()

    if args.command == "analyze":
        try:
            raw_text = analyze_image(args.image_path, args.method)
            with open(args.output_text, "w") as f:
                f.write(raw_text)
            print(f"Analysis complete. Saved to {args.output_text}")
        except Exception:
            exit(1)

    elif args.command == "generate":
        with open(args.input_text, "r") as f:
            content = f.read()
        prompt = f"Generate an image based on the following structured data/description:\n\n{content}"
        generate_image_from_text(prompt, args.output_image)

    elif args.command == "report":
        create_html(args.original, args.json_img, args.svg_img, args.json_text, args.svg_text, args.output)

    elif args.command == "batch":
        batch_process(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()
