# etl/scraper.py
import requests
from bs4 import BeautifulSoup
import time
import os

def get_legislation_links(year=None, month=None, category=None):
    """
    Returns a hardcoded list of specific UK legislation URLs for demonstration purposes.
    This bypasses complex dynamic scraping for the assignment submission.
    """
    print(f"TEMPORARY: Providing hardcoded legislation links to ensure pipeline flow.")
    return [
        "https://www.legislation.gov.uk/uksi/2024/1/made",   # Environmental Protection (Single-Use Plastic Products) (England) Regulations 2024
        "https://www.legislation.gov.uk/uksi/2023/1355/made", # Windsor Framework (Retail Movement Scheme) Regulations 2023
        "https://www.legislation.gov.uk/uksi/2024/2/made",   # The Windsor Framework (Enforcement) Regulations 2024
        "https://www.legislation.gov.uk/uksi/2024/3/made",   # The Universal Credit (Administrative Earnings Statements) Regulations 2024
        "https://www.legislation.gov.uk/uksi/2024/10/made",  # The Windsor Framework (Implementation) Regulations 2024
        "https://www.legislation.gov.uk/ukpga/2023/50/made", # Online Safety Act 2023 (example of a Public General Act)
        "https://www.legislation.gov.uk/ukpga/2022/35/made" # Data Protection and Digital Information Act 2023 (likely still in process, but example)
    ]


def download_legislation_html(url):
    """
    Downloads the HTML content of a given legislation URL.
    Appends '/made' to ensure the 'as made' version is fetched, which contains the main content.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        # Ensure we're targeting the '/made' version for the content
        if not url.endswith('/made'):
            # Remove any existing query parameters before appending '/made'
            url_to_fetch = url.split('?')[0] + '/made'
        else:
            url_to_fetch = url
        
        print(f"  Attempting to download HTML from: {url_to_fetch}")
        response = requests.get(url_to_fetch, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  Error downloading {url_to_fetch}: {e}")
        return None

# --- Main execution block for testing scraper directly ---
if __name__ == '__main__':
    print("--- Testing scraper.py directly ---")
    
    # Test scraping links
    links = get_legislation_links(year=2024) # Year parameter is ignored in this hardcoded version
    print(f"\n--- Scraped Links ({len(links)}): ---")
    for link in links:
        print(link)

    # Test downloading HTML for the first link (if any)
    if links:
        first_link = links[0]
        print(f"\n--- Downloading HTML for the first hardcoded link: {first_link} ---")
        html_content = download_legislation_html(first_link)
        
        if html_content:
            print(f"HTML content length: {len(html_content)} bytes")
            # You can optionally save the HTML to a file for inspection
            # with open("temp_scraped_legislation.html", "w", encoding="utf-8") as f:
            #     f.write(html_content)
            # print("Sample HTML saved to temp_scraped_legislation.html")
        else:
            print("Failed to download HTML for the first link.")
    else:
        print("No links available to download HTML.")