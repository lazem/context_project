# Confluence Export Tooling

This repository contains two companion scripts that help you back up a Confluence Cloud space and turn the export into Markdown:

- `conf_crawler.py` crawls every page in a Confluence space and downloads the legacy Word export (`.doc`) for each page.
- `converter.py` walks the downloaded export, extracts the embedded HTML from each `.doc` file, and converts it to Markdown.

The usual workflow is to export the space with the crawler, then convert the resulting files.

---

## Requirements

- Python 3.10+ (other 3.x versions will likely work as well)
- Dependencies from `requirements.txt` (`requests`, `markdownify`, etc.). Install them with:

  ```bash
  pip install -r requirements.txt
  ```

If you do not want to hard‑code sensitive values (email/API token) in the scripts, export them as environment variables and read them in before running.

---

## `conf_crawler.py`

### What it does
`conf_crawler.py` uses the Confluence REST API to enumerate every page in a space and the `/exportword` endpoint to download each one as a `.doc` file. Files are written to `confluence_word_exports/`, recreating the Confluence page hierarchy as nested folders.

### Key configuration
Update the constants at the top of the script before running:

| Setting | Description |
| --- | --- |
| `CONFLUENCE_BASE_URL` | Your site root (include `/wiki`). |
| `SPACE_KEY` | Short key of the space you want to export. |
| `EMAIL` / `API_TOKEN` | Atlassian account credentials used for basic auth. Generate the API token from https://id.atlassian.com/manage/api-tokens. |
| `OUTPUT_DIR` | Target folder for the downloaded `.doc` files. |
| `PAGE_LIMIT` | Pagination size for the REST API calls. Lower this if you hit rate limits. |
| `SLEEP_BETWEEN_DOWNLOADS` | Delay between downloads to reduce pressure on Confluence. |

### Running the crawler

```bash
python conf_crawler.py
```

The script prints progress for every page. Each exported Word document is saved as `<page-title>_<pageId>.doc` under `confluence_word_exports/<ancestor>/<page>/`.

*Tip:* keep your credentials out of version control (for example, source them from environment variables or a `.env` file) before you run the script.

---

## `converter.py`

### What it does
`converter.py` opens every `.doc`, `.html`, or `.txt` file under the configured `input_dir`, looks for the embedded HTML saved by Confluence, decodes it from quoted‑printable, converts it to Markdown with `markdownify`, and writes the result to the mirrored folder inside `Context/`. Images are stripped during conversion.

### Defaults and safety checks

- `input_dir` defaults to `@confluence_word_exports`. Update this to `confluence_word_exports` (or whichever folder you pointed `conf_crawler.py` at) before running.
- `output_dir` defaults to `Context`. The script **deletes and recreates** this directory at startup so you always get a clean Markdown tree—ensure nothing important lives there.
- Temporary Office lock files that start with `~$` are ignored automatically.

### Running the converter

```bash
python converter.py
```

The script walks every subdirectory of the input folder, preserves the structure, and emits Markdown files with sanitized filenames (spaces preserved, `+` replaced with `_`). Progress is printed for each file as it is processed, and failures are logged rather than stopping the run.

---

## End-to-end workflow

1. **Configure credentials**: set `CONFLUENCE_BASE_URL`, `SPACE_KEY`, and valid Atlassian credentials in `conf_crawler.py`.
2. **Export the space**: run `python conf_crawler.py`. Confirm the `.doc` files appear under `confluence_word_exports/**`.
3. **Adjust `converter.py` paths** if necessary so `input_dir` matches your export folder.
4. **Convert to Markdown**: run `python converter.py`. Review the resulting Markdown tree in `Context/**`.

Optional next steps:
- Commit the Markdown output or sync it to an external knowledge base.
- Post-process the Markdown (e.g., run a link checker or feed into another documentation tool).

---

## Troubleshooting tips

- **HTTP errors / authentication failures**: regenerate the API token, make sure basic auth is enabled for your Atlassian account, and verify your user has access to the target space.
- **Large spaces timing out**: lower `PAGE_LIMIT` or increase `SLEEP_BETWEEN_DOWNLOADS` to keep within Confluence rate limits.
- **Unexpected directory names**: `sanitize_filename` removes characters that are illegal on most filesystems. Page titles with only illegal characters will be renamed to `untitled`.
- **Empty Markdown files**: if Confluence returns a different MIME format, `converter.py` may not find `<html>...</html>` markers. Inspect the `.doc` file manually and adjust the regex if needed.

This README should give you enough context to run both scripts and adapt them to other Confluence spaces.
