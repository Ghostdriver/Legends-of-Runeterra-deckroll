from PIL import Image
from CardData import CardData
import urllib.request
from typing import List
from CardPool import CardPool
from playwright.async_api import async_playwright

def assemble_card_image(card_pool: CardPool, card: CardData, language: str = "en_us"):
    # Get image of the card and associated cards
    image_list: List = []
    urllib.request.urlretrieve(url=card.game_absolute_path, filename="images/image.png")
    card_image = Image.open("images/image.png")
    image_list.append(card_image)
    for index, associated_card_code in enumerate(card.associated_card_refs):
        associated_card = card_pool.get_card_by_card_code(card_code=associated_card_code, language=language)
        urllib.request.urlretrieve(url=associated_card.game_absolute_path, filename=f"images/image{index}.png")
        card_image = Image.open(f"images/image{index}.png")
        image_list.append(card_image)
    
    image_size = card_image.size
    total_width = len(image_list) * image_size[0]

    all_in_one_img = Image.new('RGB', (total_width, image_size[1]))

    current_width = 0
    for image in image_list:
        all_in_one_img.paste(image, (current_width, 0))
        current_width += image.size[0]

    all_in_one_img.save('images/card.jpg')

async def screenshot_deck_from_runeterrra_ar(screenshot_url: str):
    async with async_playwright() as playwright:
        firefox = playwright.firefox
        browser = await firefox.launch()
        page = await browser.new_page()
        await page.goto(screenshot_url, wait_until="networkidle")
        await page.locator("#screen.screencolor.imgbackdeck").screenshot(path="images/screenshot.png")
        await browser.close()
