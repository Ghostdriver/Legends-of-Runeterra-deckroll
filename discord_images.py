from PIL import Image
from CardData import CardData
import urllib.request
from typing import List, Tuple
from CardPool import CardPool
from playwright.async_api import async_playwright
import discord
from Deck import Deck

def assemble_card_image(card_pool: CardPool, card_name: str, language: str = "en_us") -> Tuple[discord.Embed, discord.File]:
    # Put image of the card and associated cards in one image and save it
    SINGLE_CARD_SIZE = (680, 1024)
    ASSEMBLED_CARD_IMAGE_PATH = "images/card.jpg"
    DISCORD_FILENAME = "card.jpg"
    card = card_pool.get_card_by_card_name(card_name=card_name, language=language)
    embed = discord.Embed(title=card.name)

    # Go through the card and it's associated cards, retrieve the images and put them into one image
    card_codes = [card.card_code] + card.associated_card_refs
    all_in_one_img = Image.new('RGB', (SINGLE_CARD_SIZE[0] * len(card_codes), SINGLE_CARD_SIZE[1]))
    for index, card_code in enumerate(card_codes):
        card = card_pool.get_card_by_card_code(card_code=card_code, language=language)
        card_image_path = urllib.request.urlretrieve(url=card.game_absolute_path)[0]
        card_image = Image.open(card_image_path)
        all_in_one_img.paste(card_image, (SINGLE_CARD_SIZE[0] * index, 0))
    all_in_one_img.save(ASSEMBLED_CARD_IMAGE_PATH)

    file = discord.File(ASSEMBLED_CARD_IMAGE_PATH, filename=DISCORD_FILENAME)
    embed.set_image(url=f"attachment://{DISCORD_FILENAME}")
    return (embed, file)

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