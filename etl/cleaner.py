# etl/cleaner.py
from bs4 import BeautifulSoup
import re

def clean_legislation_html(html_content):
    """
    Cleans HTML content of legislation, removing images, watermarks,
    and non-essential annotations. Extracts the main text.

    Args:
        html_content (bytes or str): The raw HTML content.

    Returns:
        str: Cleaned plain text of the legislation.
        dict: Extracted metadata.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted tags/elements:
    # Common elements to remove: scripts, styles, navs, headers, footers, images, watermarks.
    # You'll need to inspect the HTML to find the exact tags/classes.
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'img', 'noscript']):
        tag.decompose()

    # Remove elements that look like watermarks or background annotations.
    # This is highly dependent on the website's specific HTML structure.
    # Example: if watermarks are in a div with a specific class.
    # for watermark_div in soup.find_all('div', class_='watermark'):
    #     watermark_div.decompose()

    # Often, the main content is within a specific div or section.
    # Find the main content area. This is critical for good cleaning.
    # Inspect legislation.gov.uk: they often use <main id="content"> or similar.
    main_content_div = soup.find('main', id='content') or soup.find('div', class_='content')
    if not main_content_div:
        main_content_div = soup # Fallback to entire soup if main content not found

    # Remove non-essential annotations (e.g., footnotes, sidebars, internal links).
    # Look for classes like 'footnote', 'annotation', 'marginal-note', 'editor-note'.
    # Example:
    for annotation_tag in main_content_div.find_all(class_=re.compile(r'(footnote|annotation|editor-note|nav-link|sig-block)')):
         annotation_tag.decompose()

    # Extract text and clean up whitespace
    text = main_content_div.get_text(separator=' ', strip=True)

    # Further clean up multiple spaces, newlines, and specific patterns
    text = re.sub(r'\s+', ' ', text).strip() # Replace multiple whitespaces with single space
    text = re.sub(r'(\n\s*){2,}', '\n\n', text) # Reduce multiple newlines
    
    return text

def extract_metadata(html_content):
    """
    Extracts relevant metadata from the HTML content.
    Examples: Title, Legislation Type (e.g., SI, Act), Identifier, Date Made, Effective Date.

    Args:
        html_content (bytes or str): The raw HTML content.

    Returns:
        dict: A dictionary of extracted metadata.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    metadata = {}

    # Title: Often found in <title> tag or an <h1> within the main content.
    title_tag = soup.find('meta', property='og:title')
    if title_tag and 'content' in title_tag.attrs:
        metadata['title'] = title_tag['content'].strip()
    elif soup.find('h1', class_='title'):
        metadata['title'] = soup.find('h1', class_='title').get_text(strip=True)
    elif soup.title:
        metadata['title'] = soup.title.get_text(strip=True).replace(' - Legislation.gov.uk', '')

    # Legislation Identifier (e.g., "2024 No. 76")
    # This might be in a specific h2 or p tag. Inspect the source.
    id_tag = soup.find(class_='LegislationIdentifier') # Or similar class name
    if id_tag:
        metadata['identifier'] = id_tag.get_text(strip=True)
    else:
        # Try to extract from URL if not explicitly found in HTML
        # Example: https://www.legislation.gov.uk/uksi/2024/76/made/data.htm -> 2024/76
        url_match = re.search(r'/(uksi|ukpga|asp|nisi)/(\d{4})/(\d+)', soup.find('link', rel='canonical')['href'] if soup.find('link', rel='canonical') else '')
        if url_match:
            metadata['type'] = url_match.group(1) # uksi, ukpga etc.
            metadata['year'] = int(url_match.group(2))
            metadata['number'] = int(url_match.group(3))
            metadata['identifier'] = f"{url_match.group(2)} No. {url_match.group(3)}"


    # Dates (e.g., Date Made, Laid Before Parliament, Coming into force)
    # These are often in definition lists (dl) or tables.
    # Look for terms like 'Date Made:', 'Laid Before Parliament:'.
    for dt_tag in soup.find_all('dt'):
        dt_text = dt_tag.get_text(strip=True)
        if 'Date Made:' in dt_text and dt_tag.find_next_sibling('dd'):
            metadata['date_made'] = dt_tag.find_next_sibling('dd').get_text(strip=True)
        if 'Coming into force:' in dt_text and dt_tag.find_next_sibling('dd'):
            metadata['effective_date'] = dt_tag.find_next_sibling('dd').get_text(strip=True)
        # Add more date types as needed

    # Type of legislation (e.g., "Statutory Instrument", "Act")
    # This could be derived from the URL or specific text.
    if 'type' not in metadata:
        type_tag = soup.find('span', class_='LegislationType')
        if type_tag:
            metadata['type'] = type_tag.get_text(strip=True)
        elif 'identifier' in metadata:
            if 'uksi' in metadata['identifier'].lower() or 'statutory instrument' in metadata['identifier'].lower():
                metadata['type'] = 'Statutory Instrument'
            elif 'ukpga' in metadata['identifier'].lower() or 'act' in metadata['identifier'].lower():
                metadata['type'] = 'Public General Act'

    # Source URL
    metadata['source_url'] = soup.find('link', rel='canonical')['href'] if soup.find('link', rel='canonical') else ''
    
    # Check if a category/subject can be extracted from the page itself
    # This is often not explicitly present in a structured way without more advanced NLP
    # But sometimes keywords are provided.
    
    return metadata

if __name__ == '__main__':
    # Example usage:
    # Assume you have some raw HTML content from scraper.py
    # For testing, you can download a sample HTML and save it.
    
    sample_html_path = "sample_legislation.html" # Replace with a path to a downloaded HTML file

    try:
        with open(sample_html_path, 'r', encoding='utf-8') as f:
            sample_html_content = f.read()

        cleaned_text = clean_legislation_html(sample_html_content)
        metadata = extract_metadata(sample_html_content)

        print("\n--- Cleaned Text (first 500 chars) ---")
        print(cleaned_text[:500])

        print("\n--- Extracted Metadata ---")
        for key, value in metadata.items():
            print(f"{key}: {value}")

    except FileNotFoundError:
        print(f"Error: {sample_html_path} not found. Please download a sample HTML file first.")
        print("You can get one by running scraper.py and saving the output.")
    except Exception as e:
        print(f"An error occurred during cleaning/metadata extraction: {e}")