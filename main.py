from typing import  Dict, Literal
from CardData import ALL_REGIONS
from CardPool import CardPool
from Deckroll import Deckroll
from DiscordBot import DiscordBot
from copy import deepcopy

# CARD_SETS in CardData needs to be updated
SCREENSHOT_PREFIX = "https://runeterra.ar/decks/bot/"
DECKLINK_PREFIX: str = "https://runeterra.ar/decks/code/"
DECKROLL_DECK_PREFIX: str = "https://app.mobalytics.gg/lor/decks/code/"
CREATE_EXCEL_SPREADSHEAT: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True

# INIT CARD_POOLS
card_pool_standard = CardPool(format="client_Formats_Standard_name")
card_pool_eternal = CardPool(format="client_Formats_Eternal_name")
#card_pool_eternal.create_txt_file_with_card_names()

# INIT DEFAULT VALUES FOR DECKROLL
format_default = "standard"
language_default = "en_us"
amount_regions_default = 2
amount_cards_default = 40
amount_champions_default = 6
all_regions = ALL_REGIONS
regions_and_weights_default: Dict[str, int] = {}
for region in all_regions:
    regions_and_weights_default[region] = 1
cards_and_weights_standard_default: Dict[str, int] = {}
for collectible_card in card_pool_standard.collectible_cards:
    cards_and_weights_standard_default[collectible_card.card_code] = 1
cards_and_weights_eternal_default: Dict[str, int] = {}
for collectible_card in card_pool_eternal.collectible_cards:
    cards_and_weights_eternal_default[collectible_card.card_code] = 1
count_chances_default: Dict[int, int] = {
    1: 20,
    2: 30,
    3: 50
}
count_chances_two_remaining_deck_slots_default: Dict[int, int] = {
    1: 33,
    2: 67
}
# ADDITIONAL DEFAULT VALUES FOR DRAFTING
region_offers_per_pick_default: int = 3
regions_to_choose_per_pick_default: int = 1
card_offers_per_pick_default: int = 3
cards_to_choose_per_pick_default: int = 1
card_bucket_size_default: int = 1
draft_champions_first_default: bool = False

# INDIVIDUAL DECKROLL FOR EXCEL SPREADSHEAT - change the values to fit your needs!
format: Literal["standard", "eternal"] = "standard"
if format == "standard":
    card_pool = card_pool_standard
    cards_and_weights = deepcopy(cards_and_weights_standard_default)
else:
    card_pool = card_pool_eternal
    cards_and_weights = deepcopy(cards_and_weights_eternal_default)
amount_regions = amount_regions_default
amount_cards = amount_cards_default
amount_champions = amount_champions_default
regions_and_weights = deepcopy(regions_and_weights_default)
count_chances = deepcopy(count_chances_default)
count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
# deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
# print(deck_roll.roll_deck())

if __name__ == "__main__":
    if CREATE_EXCEL_SPREADSHEAT:
        deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
        deck_roll.roll_deck_spreadsheat(amount_decks=AMOUNT_DECKS, decklink_prefix=DECKROLL_DECK_PREFIX)
    if START_DISCORD_BOT:
        discord_bot = DiscordBot(screenshot_prefix=SCREENSHOT_PREFIX, decklink_prefix=DECKLINK_PREFIX, deckroll_deck_prefix=DECKLINK_PREFIX, card_pool_standard=card_pool_standard, card_pool_eternal=card_pool_eternal, format_default=format_default, language_default=language_default, amount_regions_default=amount_regions_default, amount_cards_default=amount_cards_default, amount_champions_default=amount_champions_default, regions_and_weights_default=regions_and_weights_default, cards_and_weights_standard_default=cards_and_weights_standard_default, cards_and_weights_eternal_default=cards_and_weights_eternal_default, count_chances_default=count_chances_default, count_chances_two_remaining_deck_slots_default=count_chances_two_remaining_deck_slots_default, region_offers_per_pick_default=region_offers_per_pick_default, regions_to_choose_per_pick_default=regions_to_choose_per_pick_default, card_offers_per_pick_default=card_offers_per_pick_default, cards_to_choose_per_pick_default=cards_to_choose_per_pick_default, card_bucket_size_default=card_bucket_size_default, draft_champions_first_default=draft_champions_first_default)
