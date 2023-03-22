from PIL import Image
from CardData import CardData
import urllib.request
from typing import List
from CardPool import CardPool
from playwright.async_api import async_playwright

def assemble_card_image(card_pool: CardPool, card: CardData):
    # Get image of the card and associated cards
    image_list: List = []
    urllib.request.urlretrieve(url=card.game_absolute_path, filename="images/image.png")
    card_image = Image.open("images/image.png")
    image_list.append(card_image)
    for index, associated_card_code in enumerate(card.associated_card_refs):
        associated_card = card_pool.get_card_by_card_code(associated_card_code)
        urllib.request.urlretrieve(url=associated_card.game_absolute_path, filename=f"images/image{index}.png")
        card_image = Image.open(f"images/image{index}.png")
        image_list.append(card_image)
    
    # merge images
    # Open images and store them in a list
    total_width = 0
    max_height = 0
    # find the width and height of the final image
    for img in image_list:
        total_width += img.size[0]
        max_height = max(max_height, img.size[1])
    # create a new image with the appropriate height and width
    new_img = Image.new('RGB', (total_width, max_height))
    # Write the contents of the new image
    current_width = 0
    for img in image_list:
        new_img.paste(img, (current_width, 0))
        current_width += img.size[0]
    # Save the image
    new_img.save('images/card.jpg')

async def screenshot_deck_from_runeterrra_ar(deckcode: str):
    # load deck from deckcode to see, that it's a regular deck
    #deck = Deck(card_pool=card_pool)
    #deck.load_deck_from_deckcode(deckcode=deckcode)
    deck_url = "https://runeterra.ar/decks/bot/" + deckcode
    async with async_playwright() as playwright:
        firefox = playwright.firefox
        browser = await firefox.launch()
        page = await browser.new_page()
        await page.goto(deck_url, wait_until="load")
        await page.locator("#screen.screencolor.imgbackdeck").screenshot(path="images/screenshot.png")
        await browser.close()