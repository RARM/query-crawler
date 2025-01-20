import requests
from bs4 import BeautifulSoup
import csv
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

def crawl_page(url, query, visited_urls, max_threads=8):  # Add max_threads parameter
    """
    Crawls a single page and searches for the given query.

    Args:
        url (str): The URL of the page to crawl.
        query (str): The search query.
        visited_urls (set): A set of visited URLs to avoid cycles.
        max_threads (int): The maximum number of threads to use.

    Returns:
        list: A list of tuples, where each tuple contains the matching text and the URL where it was found.
    """
    try:
        if url in visited_urls:
            return []
        visited_urls.add(url)

        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        all_text = soup.get_text(separator=" ", strip=True)
        matches = [(query.lower(), url)] if query.lower() in all_text.lower() else []

        links = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('/') or link['href'].startswith(url)]
        links = [urljoin(url, link) for link in links]

        # Use ThreadPoolExecutor with max_threads
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(crawl_page, link, query, visited_urls, max_threads) for link in links]
            for future in as_completed(futures):
                matches.extend(future.result())

        return matches

    except requests.exceptions.RequestException as e:
        print(f"Error crawling {url}: {e}")
        return []

def save_results_to_csv(results, csv_file):
    """
    Saves the search results to a CSV file.

    Args:
        results (list): A list of tuples, where each tuple contains the matching text and the URL.
        csv_file (str): The name of the CSV file to save the results to.
    """
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Text', 'URL'])
        for text, url in results:
            writer.writerow([text, url])

def main():
    parser = argparse.ArgumentParser(description="Crawl a website and search for a specific query.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('homepage', help='URL of the website homepage to crawl.')
    parser.add_argument('query', help='Search query to look for on the website.')
    parser.add_argument('-t', '--threads', type=int, default=8, help='Number of threads to use for crawling (default: 8)')
    args = parser.parse_args()

    results = crawl_page(args.homepage, args.query, set(), args.threads)  # Pass args.threads to crawl_page
    save_results_to_csv(results, 'search_results.csv')

if __name__ == "__main__":
    main()