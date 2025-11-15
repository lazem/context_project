import os
import time
import requests

# =========================
# CONFIG
# =========================
# Your Confluence Cloud base URL
CONFLUENCE_BASE_URL = "https://novamedia.atlassian.net/wiki"  # note the /wiki

# Space key to export
SPACE_KEY = "IAH"  # e.g. "IT", "DOCS", "ENG"

# Atlassian email + API token (for basic auth)
EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")

# Where to store the .docx files
OUTPUT_DIR = "confluence_word_exports"

# Pagination and throttling
PAGE_LIMIT = 10                 # number of pages per REST call
SLEEP_BETWEEN_DOWNLOADS = 0.5   # seconds between downloads to be nice to Confluence


# =========================
# HELPERS
# =========================

def ensure_output_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def sanitize_filename(name: str) -> str:
    """
    Make a safe filename out of the page title.
    Removes illegal characters and trims length.
    """
    forbidden = r'\/:*?"<>|'
    sanitized = "".join(c for c in name if c not in forbidden)
    sanitized = sanitized.strip()
    if not sanitized:
        sanitized = "untitled"
    return sanitized[:150]


def build_page_directory(ancestors, page_title):
    """Return OUTPUT_DIR joined with sanitized ancestor titles and this page."""
    folders = []
    for ancestor in ancestors:
        title = ancestor.get("title")
        if not title:
            continue
        sanitized = sanitize_filename(title)
        if sanitized:
            folders.append(sanitized)

    page_segment = sanitize_filename(page_title)
    if page_segment:
        folders.append(page_segment)

    if not folders:
        return OUTPUT_DIR

    return os.path.join(OUTPUT_DIR, *folders)


def get_all_pages_in_space():
    """
    Yield {id, title} for all pages in a space using the Confluence REST API.
    """
    start = 0

    session = requests.Session()
    session.auth = (EMAIL, API_TOKEN)

    while True:
        url = (
            f"{CONFLUENCE_BASE_URL}/rest/api/content"
            f"?spaceKey={SPACE_KEY}&type=page&limit={PAGE_LIMIT}&start={start}"
            f"&expand=ancestors"
        )

        resp = session.get(url)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            break

        for page in results:
            yield {
                "id": page["id"],
                "title": page["title"],
                "ancestors": page.get("ancestors", []),
            }

        size = data.get("size", 0)
        next_start = data.get("start", 0) + size
        total_size = data.get("totalSize")

        # stop if we are at or beyond the total
        if total_size is not None and next_start >= total_size:
            break

        if size == 0:
            break

        start = next_start


def export_page_to_word(page_id: str, page_title: str, ancestors):
    """
    Export a single Confluence page to Word (.doc) via the legacy
    /wiki/exportword endpoint that is still available on Cloud.
    """
    url = f"{CONFLUENCE_BASE_URL}/exportword?pageId={page_id}"

    resp = requests.get(url, auth=(EMAIL, API_TOKEN))
    resp.raise_for_status()

    safe_title = sanitize_filename(page_title)
    filename = f"{safe_title}_{page_id}.doc"

    page_dir = build_page_directory(ancestors, page_title)
    os.makedirs(page_dir, exist_ok=True)
    filepath = os.path.join(page_dir, filename)

    with open(filepath, "wb") as f:
        f.write(resp.content)

    print(f"Exported: {page_title}  ->  {filepath}")


# =========================
# MAIN
# =========================

def main():
    ensure_output_dir(OUTPUT_DIR)

    print(f"Listing pages in space: {SPACE_KEY}")
    for page in get_all_pages_in_space():
        page_id = page["id"]
        title = page["title"]

        try:
            export_page_to_word(page_id, title, page.get("ancestors", []))
            time.sleep(SLEEP_BETWEEN_DOWNLOADS)
        except Exception as e:
            print(f"Failed to export page {title} ({page_id}): {e}")


if __name__ == "__main__":
    main()
