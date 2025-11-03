import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_FOLDER = Path("/mnt/Backup/notebooklm_source_automation")
load_dotenv(str(PROJECT_FOLDER / ".env"))

ZOTERO_API_KEY = os.environ["ZOTERO_API_KEY"]
ZOTERO_USER_ID = os.environ["ZOTERO_USER_ID"]
