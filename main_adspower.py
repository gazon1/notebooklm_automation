import math
import os
import random
import time

from adspower_api_utils import close_browser, start_browser
from loguru import logger
from patchright.sync_api import Locator, sync_playwright


###########################################################################################
DISPOSABLE = False  # use disposable profiles
disp_N = 10  # number of disposable profiles
T = 15  # seconds delay
###########################################################################################


def load_profiles(file_name: str = "profiles.txt") -> list[str]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def click_random(locator: Locator, manual_radius: float | None = None) -> None:
    time.sleep(random.uniform(1, 2))
    locator.wait_for(state="visible", timeout=50000)
    box = locator.bounding_box()
    if box is None:
        raise Exception("Bounding box not found")
    width, height = box["width"], box["height"]
    cx, cy = width / 2, height / 2
    radius = manual_radius if manual_radius is not None else min(width, height) / 2
    angle = random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(random.uniform(0, 1))
    rand_x = cx + r * math.cos(angle)
    rand_y = cy + r * math.sin(angle)

    locator.click(position={"x": rand_x, "y": rand_y})


def activity(profile_number: str) -> None:
    try:
        puppeteer_ws = start_browser(profile_number)
        if not puppeteer_ws:
            print(f"Failed to launch browser for profile {profile_number}.")
            return

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(puppeteer_ws, slow_mo=random.randint(2000, 3000))
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
            ###########################################################################################
            page.goto("https://chat.deepseek.com/a/chat/s/ec2724d8-0cc5-40c0-ad5a-0325f3675ecc")
            page.wait_for_load_state("load")
            # textarea
            page.fill(
                "input[name=textarea]",
                "В комплекте мешок магниевой соли 10кг. Магниевая соль для ванны GLEB SALT (она же эпсом соль) - это удивительный продукт, который одновременно поможет Вам укрепить иммунитет, избавиться от проблем с лишним весом, снимет стресс и укрепит нервную систему, а также улучшит состояние кожи. Продукт состоит на 99% из сульфата магния, а магний жизненно необходим человеку. Магний участвует в регуляции нервной системы, артериального давления, поддерживает сердечно-сосудистую систему, стимулирует отделение желчи и работу кишечника и принимает участие в еще более 350 процессов в организме. Жителям мегаполисов магний необходим в повышенном количестве, так как в их жизни присутствует хронический стресс. Магниевые соли для ванной обладают выраженным расслабляющим и терапевтическим действием, но для этого необходим накопительный эффект. Длительность лечебного курса составляет 10-15 ванн. Ванны следует принимать через день. Рекомендуемое количество соли на ванну 400-500г. Английскую соль эпсома лучше всего принимать лечебным курсом, чтобы был эффект! Магниевая соль подходит для приготовления ванночек для рук, ног и всего тела, а так же можно использовать для приготовления детских ванн. Детская ванна с epsom salt с магнием будет иметь успокаивающий эффект перед сном для ваших детей.",
            )
            send_btn_locator = page.locator('.ds-icon-button._7436101[role="button"]')
            if send_btn_locator.is_visible():
                click_random(send_btn_locator)
                logger.info("Click done")
            else:
                logger.warning("Send button not found")
            # кнопка перед отправкой и с текстом: role=button, class=ds-icon-button _7436101
            # стала кнопка: ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled

            locator = page.locator(".ds-icon-button._7436101.bcc55ca1.ds-icon-button--disabled")
            locator.wait_for(state="attached", timeout=60_000)
            logger.info(f"Message sent for profile {profile_number}")
            ###########################################################################################

            input("Press Enter to continue...")
            ###########################################################################################
            browser.close()
            time.sleep(random.uniform(T * 0.85, T * 1.15))

    except Exception as e:
        print(f"error for profile {profile_number}: {e}")

    finally:
        close_browser(profile_number)


if __name__ == "__main__":
    profiles = ["5"] * disp_N if DISPOSABLE else load_profiles("profiles.txt")
    for profile in profiles:
        activity(profile)
