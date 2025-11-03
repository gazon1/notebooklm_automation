import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_FOLDER = Path("/mnt/Backup/notebooklm_source_automation")
load_dotenv(str(PROJECT_FOLDER / ".env"))

ZOTERO_API_KEY = os.environ["ZOTERO_API_KEY"]
ZOTERO_USER_ID = os.environ["ZOTERO_USER_ID"]


PROMPT = """
Create a comprehensive briefing document that synthesizes the main themes and ideas from the sources.
Start with a concise Executive Summary that presents the most critical takeaways upfront.
The body of the document must provide a detailed and thorough examination of the main themes, evidence, and conclusions found in the sources.
This analysis should be structured logically with headings and bullet points to ensure clarity.
The tone must be objective and incisive.

Answer 3 key questions about practical impications of the source article:
1. What’s the problem they’re trying to solve?
2. How do they solve it? Write code to demonstate articulated ideas
3. Does it work?


Write all sources in summary and source link to original article
"""
