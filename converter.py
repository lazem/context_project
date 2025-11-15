

import os
import re
import quopri
import shutil
from markdownify import markdownify as md

def convert_html_doc_to_md(doc_path, md_path):
    """
    Extracts HTML from a MIME-saved .doc file, decodes it,
    and converts its content to a clean Markdown file, ignoring images.
    """
    try:
        with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        html_start_match = re.search(r'<html', content, re.IGNORECASE)
        html_end_match = re.search(r'</html>', content, re.IGNORECASE)

        if not html_start_match or not html_end_match:
            print(f"--> Skipping '{doc_path}': Could not find HTML content.")
            return

        html_content_bytes = content[html_start_match.start():html_end_match.end()].encode('utf-8')
        decoded_html = quopri.decodestring(html_content_bytes).decode('utf-8')
        
        markdown_content = md(decoded_html, heading_style="ATX", strip=['img'])

        # Ensure the output directory for the file exists
        os.makedirs(os.path.dirname(md_path), exist_ok=True)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Successfully converted '{doc_path}'")

    except Exception as e:
        print(f"An error occurred while processing '{doc_path}': {e}")

if __name__ == "__main__":
    input_dir = "@confluence_word_exports"
    output_dir = "Context"

    # --- Validate Input Directory ---
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
    else:
        # --- Clean Output Directory ---
        print(f"Clearing contents of '{output_dir}' directory...")
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Starting conversion from '{input_dir}' to '{output_dir}'...")

        # --- Walk the Directory Tree ---
        for root, dirs, files in os.walk(input_dir):
            # Determine the corresponding output directory
            relative_path = os.path.relpath(root, input_dir)
            current_output_dir = os.path.join(output_dir, relative_path)

            for filename in files:
                if filename.lower().endswith(('.doc', '.html', '.txt')) and not filename.startswith('~$'):
                    input_path = os.path.join(root, filename)
                    
                    # Create a clean filename for the output
                    output_filename = os.path.splitext(filename)[0].replace('+', '_') + '.md'
                    output_path = os.path.join(current_output_dir, output_filename)
                    
                    # The conversion function will create the directory if needed
                    convert_html_doc_to_md(input_path, output_path)
        
        print("\nConversion process finished.")

