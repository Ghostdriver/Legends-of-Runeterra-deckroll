from PIL import Image
from CardData import CardData
import urllib.request
from typing import List
from CardPool import CardPool
from playwright.async_api import async_playwright
import discord
from Deck import Deck

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

def assemble_deck_embed(card_pool: CardPool, deckcode: str, language: str = "en_us") -> discord.Embed:
    DECKLINK_PREFIX: str = "https://runeterra.ar/decks/code/"
    deck_url = f"{DECKLINK_PREFIX}{deckcode}?lang={language}"
    deck = Deck(card_pool=card_pool)
    deck.load_deck_from_deckcode(deckcode=deckcode)
    champions = deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Champion")
    champions_formatted = card_list_to_string(card_pool=card_pool, card_list=champions, deck=deck, language=language)
    units = deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Unit")
    units_formatted = card_list_to_string(card_pool=card_pool, card_list=units, deck=deck, language=language)
    spells = deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Spell")
    spells_formatted = card_list_to_string(card_pool=card_pool, card_list=spells, deck=deck, language=language)
    equipments_and_landmarks = deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Equipment") + deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Landmark")
    equipments_and_landmarks_formatted = card_list_to_string(card_pool=card_pool, card_list=equipments_and_landmarks, deck=deck, language=language)

    embed=discord.Embed(title="Decklink runeterra.ar", url=deck_url)
    embed.add_field(name="Champions", value=champions_formatted, inline=True)
    embed.add_field(name="Follower", value=units_formatted, inline=True)
    embed.add_field(name="Spells", value=spells_formatted, inline=True)
    embed.add_field(name="Equipments and Landmarks", value=equipments_and_landmarks_formatted, inline=True)
    return embed



def card_list_to_string(card_pool: CardPool, card_list: List[CardData], deck: Deck, language: str = "en_us") -> str:
    concatenated_list = ""
    for card in card_list:
        for card_localized in card_pool.collectible_cards_with_localization[language]:
            if card.card_code == card_localized.card_code:
                concatenated_list += f"{deck.cards_and_counts[card.card_code]}x {card_localized.name}\n"
    return concatenated_list