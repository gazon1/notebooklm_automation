import random
import sys
import time
from pathlib import Path as p

import click
from loguru import logger
from patchright.sync_api import Locator, Page, expect, sync_playwright

from adspower_api_utils import click_random, close_browser, start_browser
from database import DatabaseManager
from models import ProcessingStatus

PROMPT = """
Create a comprehensive briefing document that synthesizes the main themes and ideas from the sources.
Start with a concise Executive Summary that presents the most critical takeaways upfront.
The body of the document must provide a detailed and thorough examination of the main themes, evidence, and conclusions found in the sources.
This analysis should be structured logically with headings and bullet points to ensure clarity.
The tone must be objective and incisive.

Write all sources in summary and source link to original article/video
"""
T = 5

# Configure loguru logger for better output formatting
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

CHECK_VIEPORT_ELEMENT_JS = """
    el => {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= window.innerHeight &&
            rect.right <= window.innerWidth
        );
    }
"""


def scroll_until_loc(
    page: Page,
    loc: Locator,
    step: int = 10000,
    delay: float = 0.3,
    max_steps: int = 50,
):
    """
    Скроллит колесом мыши вниз, пока footer не окажется в viewport.
    :param page: Playwright Page
    :param step: шаг прокрутки (пикселей)
    :param delay: задержка между шагами (сек)
    :param max_steps: ограничение по количеству шагов
    """
    for _ in range(max_steps):
        in_viewport = loc.evaluate(
            """el => {
                const rect = el.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            }"""
        )
        if in_viewport:
            return True

        # Скроллим колесом
        page.mouse.wheel(0, step)
        time.sleep(delay)

    return False


def read_clipboard_content(page: Page) -> str:
    page.bring_to_front()
    page.click("body")
    page.wait_for_timeout(1000)
    try:
        return page.evaluate("() => navigator.clipboard.readText()")
    except Exception as e:
        logger.error(f"Ошибка чтения буфера: {e}")
        return ""


def create_source_list(source_type: str) -> list:
    """
    Create a list of URLs from a CSV file containing source links.

    Reads a CSV file named '{source_type}_links.csv' from the sources directory,
    skips empty lines, and returns a list of valid URLs.

    Args:
        source_type (str): Type of source ('website' or 'youtube')

    Returns:
        list: List of URLs extracted from the CSV file

    Raises:
        ValueError: If the file doesn't exist or contains no valid URLs
    """
    file_path = p("sources") / f"{source_type}_links.csv"

    if not file_path.exists():
        raise ValueError(f"{file_path} doesn't exist or is in the wrong location.")

    urls = []
    blank_line_count = 0

    with open(str(file_path), mode="r", encoding="utf-8", newline="") as file_content:
        # Skip header row
        next(file_content)

        for line in file_content:
            cleaned_link = line.strip()
            if cleaned_link:
                urls.append(cleaned_link)
            else:
                blank_line_count += 1

        if len(urls) == 0:
            raise ValueError(
                f"Error: {source_type}_links.csv does not contain any valid records."
            )

        if blank_line_count > 0:
            logger.info(
                f"Note: {blank_line_count} empty records from your {source_type}_csv file skipped."
            )

    return urls


@click.command()
@click.option(
    "--profile_number",
    default="1",
    help="Profile number for the browser instance",
)
def main(profile_number: str) -> None:
    """
    Automate adding multiple sources to Google NotebookLM.

    This script reads URLs from a CSV file and automatically adds them
    as sources to a new NotebookLM notebook using browser automation.

    Args:
        source_type (str): Type of sources to add ('website' or 'youtube')
        notebook_name (str): Name for the new notebook
    """
    logger.info("Starting NotebookLM automation script...")

    start_time = time.time()

    try:
        db_manager = DatabaseManager()
        puppeteer_ws = start_browser(profile_number)
        if not puppeteer_ws:
            print(f"Failed to launch browser for profile {profile_number}.")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(
                puppeteer_ws, slow_mo=random.randint(2000, 3000)
            )
            context = browser.contexts[0] if browser.contexts else browser.new_context()

            context.add_init_script("""
                Object.defineProperty(window, 'navigator', {
                    value: new Proxy(navigator, {
                        has: (target, key) => key === 'webdriver' ? false : key in target,
                        get: (target, key) =>
                            key === 'webdriver' ? undefined : typeof target[key] === 'function' ? target[key].bind(target) : target[key]
                    })
                });
            """)

            page = context.new_page()
            page.context.grant_permissions(["clipboard-read"])
            base_url = "https://notebooklm.google.com"
            notebook_id = "/notebook/d71669e3-88d4-41fd-8a4b-98806b35d29f"
            page.goto(base_url + notebook_id)

            checkbox_id = "mat-mdc-checkbox-0-input"
            select_all_selector = f'input[type="checkbox"][id="{checkbox_id}"]'
            click_random(page.locator(select_all_selector))
            video_source_list = page.locator("div.single-source-container").all()

            for url_index, current_url in enumerate(video_source_list):
                title = current_url.locator(
                    'div[aria-label="Название источника"]'
                ).inner_text()

                if db_manager.video_exists_by_title(title):
                    logger.warning(
                        f"Source [{url_index + 1}/{len(video_source_list)}] ({title}) already exists in the database. Skipping."
                    )
                    continue

                source_type_button = current_url.locator("input")
                if source_type_button.is_visible():
                    click_random(page.locator(select_all_selector))
                    click_random(page.locator(select_all_selector))
                    click_random(source_type_button)
                else:
                    logger.error("Не активна кнопка включить источник, пропускаю")
                    continue

                logger.info(
                    f"Source [{url_index + 1}/{len(video_source_list)}] ({title}) summarising..."
                )

                page.locator("textarea.cdk-textarea-autosize").fill(PROMPT)

                send_prompt_button = page.locator(
                    "query-box > div > div > form > div > button"
                )
                expect(send_prompt_button).to_be_enabled()
                click_random(send_prompt_button)

                # Жду пока кнопка отправки не станет активной чтобы быть уверенным что ответ готов

                time.sleep(60)
                loading_dots = page.locator("div.loading-dots")
                expect(loading_dots).not_to_be_attached(timeout=60_000 * 2)

                element = page.locator("div.chat-panel-content")
                element.evaluate("element => element.scrollTop = element.scrollHeight")

                copy_button_list = page.locator("button.xap-copy-to-clipboard").all()

                for element in copy_button_list:
                    is_in_view = element.evaluate(CHECK_VIEPORT_ELEMENT_JS)
                    if is_in_view:
                        copy_button = element
                        break
                else:
                    logger.error(
                        f"Не нашёл кнопку копирования в видимой области. Пропускаю ({title})"
                    )
                    continue

                click_random(copy_button)

                text_from_buffer = read_clipboard_content(page)
                if source_type_button.is_visible():
                    click_random(
                        source_type_button
                    )  # Выключаю источник после копирования
                logger.info(f"Text from clipboard: {text_from_buffer[:100]}...")

                db_manager.insert_video(
                    title=title,
                    url=None,
                    youtube_id=None,
                    status=ProcessingStatus.SENT_TO_NOTEBOOKLM,
                    summary=text_from_buffer,
                )
                logger.success(
                    f"Source [{url_index + 1}/{len(video_source_list)}] ({title}) sent to database."
                )
            # Calculate and display execution time
            end_time = time.time()
            total_seconds = round(end_time - start_time)

            if total_seconds > 59:
                minutes_elapsed = total_seconds // 60
                seconds_remaining = total_seconds % 60
                logger.info(
                    f"Time elapsed: {minutes_elapsed} minutes and {seconds_remaining} seconds."
                )
            else:
                logger.info(f"Time elapsed: {total_seconds} seconds.")

            logger.success("Notebook title updated successfully!")

            browser.close()
            time.sleep(random.uniform(T * 0.85, T * 1.15))

    except Exception as e:
        print(f"error for profile {profile_number}: {e}")

    finally:
        close_browser(profile_number)


if __name__ == "__main__":
    main()
