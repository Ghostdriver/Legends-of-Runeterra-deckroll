import lor_deckcodes
import os
import json
from typing import List, NamedTuple
import random
from datetime import date
import xlsxwriter
import time
import copy

all_regions = ["BandleCity", "Bilgewater", "Demacia", "Freljord", "Ionia", "Noxus", "PiltoverZaun", "ShadowIsles", "Shurima", "Targon", "Runeterra"]
region_weights: List[int] = [1] * len(all_regions)

class lor_card(NamedTuple):
    '''all card details, but only the standarized value (refs) and is_champ'''
    associated_card_refs: List[str]
    assets_game_absolute_path: str
    assets_full_absolute_path: str
    region_refs: List[str]
    attack: int
    cost: int
    health: int
    description: str
    description_raw: str
    level_up_description: str
    level_up_description_raw: str
    flavor_text: str
    artist_name: str
    name: str
    card_code: str
    keyword_refs: List[str]
    spell_speed_ref: str
    rarity_ref: str
    subtypes: List[str]
    supertype: str
    card_type: str # to not use the built-in type
    is_collectible: bool # is_collectible to show that it's a bool
    card_set: str # to not use the built-in set
    is_champ: bool

def get_all_cards_from_json_files(card_sets_folder: str) -> List[lor_card]:
    all_cards: List[card] = []
    for card_set_folder in os.listdir(card_sets_folder):
        # Hopefully the structure doesn't change
        card_set_file_json_folder_path = os.path.join(card_sets_folder, card_set_folder, "en_us", "data")
        # Should only be one file
        card_set_file_name: str = os.listdir(card_set_file_json_folder_path)[0]
        card_set_file_json = os.path.join(card_set_file_json_folder_path, card_set_file_name)
        with open(card_set_file_json, 'r', encoding='UTF-8') as file:
            set_cards = json.load(file)
        for set_card in set_cards:
            set_card_is_champ: bool = False
            if set_card["rarityRef"] == "Champion":
                set_card_is_champ = True
            all_cards.append(lor_card(associated_card_refs=set_card["associatedCardRefs"], assets_game_absolute_path=set_card["assets"][0]["gameAbsolutePath"], assets_full_absolute_path=set_card["assets"][0]["fullAbsolutePath"], region_refs=set_card["regionRefs"], attack=set_card["attack"], cost=set_card["cost"], health=set_card["health"], description=set_card["description"], description_raw=set_card["descriptionRaw"], level_up_description=set_card["levelupDescription"], level_up_description_raw=set_card["levelupDescriptionRaw"], flavor_text=set_card["flavorText"], artist_name=set_card["artistName"], name=set_card["name"], card_code=set_card["cardCode"], keyword_refs=set_card["keywordRefs"], spell_speed_ref=set_card["spellSpeedRef"], rarity_ref=set_card["rarityRef"], subtypes=set_card["subtypes"], supertype=set_card["supertype"], card_type=set_card["type"], is_collectible=set_card["collectible"], card_set=set_card["set"], is_champ=set_card_is_champ))
    return all_cards

# name of the folder, where all card sets from https://developer.riotgames.com/docs/lor are downloaded and unzipped to
card_sets_folder: str = "unzipped card sets"
all_cards: List[lor_card] = get_all_cards_from_json_files(card_sets_folder=card_sets_folder)
collectible_cards: List[lor_card] = []
uncollectible_cards: List[lor_card] = []
all_champs: List[lor_card] = []
for card in all_cards:
    if card.is_collectible:
        collectible_cards.append(card)
        if card.is_champ:
            all_champs.append(card)
    else:
        uncollectible_cards.append(card)
card_weights: List[int] = [1] * len(collectible_cards)

jhin_followers: List[lor_card] = []
for collectible_card in collectible_cards:
    if not collectible_card.is_champ:
        if collectible_card.name == "Lord Broadmane" and collectible_card not in jhin_followers:
            jhin_followers.append(collectible_card)
        for associated_card in collectible_card.associated_card_refs:
            for uncollectible_card in uncollectible_cards:
                if uncollectible_card.card_code == associated_card:
                    if "Skill" in uncollectible_card.keyword_refs and collectible_card not in jhin_followers:
                        jhin_followers.append(collectible_card)
                    break

def deckroll(allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> str:
    # A few exceptions -- not all problematic cases are solved/detected
    if len(allowed_cards) < 1 or (weight_cards and sum(card_weights) == 0):
        return "Error - there has to be atleast one allowed card and the sum of chances can't be 0, if weights are enabled"
    if total_amount_cards < 1 or total_amount_cards > 100:
        return "Error - the total amount of cards has to be between 1 and 100"
    if amount_champs < 0 or amount_champs > 100:
        return "Error - the total amount of champs has to be between 0 and 100"
    if len(regions) < 1 or (weight_regions and sum(region_weights) == 0):
        return "Error - atleast one region has to be given and the sum of chances can't be 0, if weights are enabled"
    for region in regions:
        if region not in all_regions:
            return f"Error - regions have to be named correctly - region {region} is named incorrectly - every region has to be one of {all_regions}"
    if mono_region_chance < 0 or mono_region_chance > 100:
        return "Error - the mono region chance has to be between 0 and 100"
    for chance in [one_of_chance, two_of_chance, three_of_chance]:
        if chance < 0 or chance > 100:
            return f"Error - chance {chance} has to be between 0 and 100"
    if amount_champs > total_amount_cards:
        return "Error - the total amount of cards has to be higher than the amount of champs"
    if "Runeterra" in regions and amount_champs == 0:
        "Error - Runeterra can't be in the allowed regions without any champs allowed"
    if weight_cards and len(allowed_cards) != len(card_weights):
        "Error - The length of given cards and card weights has to be equal, when cards should be weighted"
    if weight_regions and len(regions) != len(region_weights):
        "Error - The length of given regions and region weights has to be equal, when cards should be weighted"
    rolled_regions: List[str] = []
    # rolled deck is a dictionary, that consists of card-codes and amount of the card
    rolled_deck: dict[str, int] = {}
    # rollable champs and non champs is just a created list from 
    rollable_champ_card_codes: List[str] = []
    rollable_champ_weights: List[int] = []
    rollable_non_champ_card_codes: List[str] = []
    rollable_non_champ_weights: List[int] = []
    runeterra_champs: List[lor_card] = []
    runeterra_champ_weights: List[int] = []
    remaining_deck_slots = total_amount_cards
    remaining_champ_slots = amount_champs
    if weight_cards:
        card_weights: List[int] = copy.deepcopy(card_weights)
    else:
        card_weights: List[int] = [1] * len(allowed_cards)
    if weight_regions:
        region_weights: List[int] = copy.deepcopy(region_weights)
    else:
        region_weights: List[int] = [1] * len(regions)
    # Monoregion deck
    if mono_region_chance > random.randrange(100):
        # Don't allow Runeterra as Mono-Region, because the card pool is too small
        if "Runeterra" in regions:
            region_weights[regions.index("Runeterra")] = 0
        rolled_region = random.choices(regions, weights=region_weights)[0]
        rolled_regions.append(rolled_region)
    else:
        for i in range(2):
            rolled_region = random.choices(regions, weights=region_weights)[0]
            rolled_regions.append(rolled_region)
            # Prevents duplicated rolled region
            if not (allow_two_runeterra_champs and amount_champs > 1 and rolled_region == "Runeterra"):
                region_weights[regions.index(rolled_region)] = 0
    # Two Runeterra champs
    if rolled_regions.count("Runeterra") == 2:
        for index, allowed_card in enumerate(allowed_cards):
            if "Runeterra" in allowed_card.region_refs and allowed_card.is_champ and allowed_card not in runeterra_champs:
                runeterra_champs.append(allowed_card)
                runeterra_champ_weights.append(card_weights[index])
        if len(runeterra_champs) < 2:
            return "Error - not enough Runeterra Champs for rolling included for a two runeterra champ deck"
        rolled_runeterra_champs: List[lor_card] = []
        for i in range(2):
            rolled_runeterra_champ = random.choices(runeterra_champs, weights=runeterra_champ_weights)[0]
            rolled_runeterra_champs.append(rolled_runeterra_champ)
            runeterra_champ_weights[runeterra_champs.index(rolled_runeterra_champ)] = 0
        if amount_champs >= 6:
            rolled_deck[rolled_runeterra_champs[0].card_code] = 3
            rolled_deck[rolled_runeterra_champs[1].card_code] = 3
        elif amount_champs % 2 == 0:
            rolled_deck[rolled_runeterra_champs[0].card_code] = amount_champs // 2
            rolled_deck[rolled_runeterra_champs[1].card_code] = amount_champs // 2
        else:
            rolled_deck[rolled_runeterra_champs[0].card_code] = amount_champs // 2 + 1
            rolled_deck[rolled_runeterra_champs[1].card_code] = amount_champs // 2
        remaining_champ_slots = 0
        if amount_champs >= 6:
            remaining_deck_slots -= 6
        else:
            remaining_deck_slots -= amount_champs
        # Add rollable non_champs for rolled Runeterra-Champs 
        if rolled_runeterra_champs[0].name == "Bard" or rolled_runeterra_champs[1].name == "Bard":
            for index, allowed_card in enumerate(allowed_cards):
                # "06RU001T3" is the Chime Card
                if "06RU001T3" in allowed_card.associated_card_refs and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champs[0].name == "Evelynn" or rolled_runeterra_champs[1].name == "Evelynn":
            for index, allowed_card in enumerate(allowed_cards):
                if "Husk" in allowed_card.description_raw and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champs[0].name == "Jax" or rolled_runeterra_champs[1].name == "Jax":
            for index, allowed_card in enumerate(allowed_cards):
                if "WEAPONMASTER" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champs[0].name == "Jhin" or rolled_runeterra_champs[1].name == "Jhin":
            for index, allowed_card in enumerate(allowed_cards):
                if allowed_card in jhin_followers and allowed_card not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champs[0].name == "Kayn" or rolled_runeterra_champs[1].name == "Kayn":
            for index, allowed_card in enumerate(allowed_cards):
                if "CULTIST" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
    
    # Roll runeterra champ, if runeterra was rolled as region 
    elif "Runeterra" in rolled_regions:
        for index, allowed_card in enumerate(allowed_cards):
            if "Runeterra" in allowed_card.region_refs and allowed_card.is_champ and allowed_card not in runeterra_champs:
                runeterra_champs.append(allowed_card)
                runeterra_champ_weights.append(card_weights[index])
        if len(runeterra_champs) == 0:
            return "Error - no Runeterra Champ for rolling included"
        rolled_runeterra_champ = random.choices(runeterra_champs, weights=runeterra_champ_weights)[0]
        if remaining_champ_slots == 1:
            rolled_deck[rolled_runeterra_champ.card_code] = 1
            remaining_champ_slots -= 1
            remaining_deck_slots -= 1
        elif remaining_champ_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=[one_of_chance, two_of_chance])[0]
            rolled_deck[rolled_runeterra_champ.card_code] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount
        else:
            rolled_amount = random.choices(range(1, 4), weights=[one_of_chance, two_of_chance, three_of_chance])[0]
            rolled_deck[rolled_runeterra_champ.card_code] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount
        # Add rollable non_champs for rolled Runeterra-Champ
        if rolled_runeterra_champ.name == "Bard":
            for index, allowed_card in enumerate(allowed_cards):
                # "06RU001T3" is the Chime Card
                if "06RU001T3" in allowed_card.associated_card_refs and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champ.name == "Evelynn":
            for index, allowed_card in enumerate(allowed_cards):
                if "Husk" in allowed_card.description_raw and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champ.name == "Jax":
            for index, allowed_card in enumerate(allowed_cards):
                if "WEAPONMASTER" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champ.name == "Jhin":
            for index, allowed_card in enumerate(allowed_cards):
                if allowed_card in jhin_followers and allowed_card not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
        if rolled_runeterra_champ.name == "Kayn":
            for index, allowed_card in enumerate(allowed_cards):
                if "CULTIST" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
    
    # Search given allowed cards for champs and non_champs from the rolled regions
    for rolled_region in rolled_regions:
        if rolled_region != "Runeterra":
            for index, allowed_card in enumerate(allowed_cards):
                # check for card already in rollable cards is to prevent duplicate region cards to be twice as likely (and maybe lead to bugs)
                if rolled_region in allowed_card.region_refs and allowed_card.is_champ and allowed_card.card_code not in rollable_champ_card_codes:
                    rollable_champ_card_codes.append(allowed_card.card_code)
                    rollable_champ_weights.append(card_weights[index])
                elif rolled_region in allowed_card.region_refs and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])
    
    # Roll the deck
    # Champs first (to the given amount)
    while remaining_champ_slots > 0:
        if sum(rollable_champ_weights) == 0:
            break
        rolled_champ = random.choices(rollable_champ_card_codes, weights=rollable_champ_weights)[0]
        rollable_champ_weights[rollable_champ_card_codes.index(rolled_champ)] = 0
        if remaining_champ_slots == 1:
            rolled_deck[rolled_champ] = 1
            remaining_champ_slots -= 1
            remaining_deck_slots -= 1
        elif remaining_champ_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=[one_of_chance, two_of_chance])[0]
            rolled_deck[rolled_champ] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount
        else:
            rolled_amount = random.choices(range(1, 4), weights=[one_of_chance, two_of_chance, three_of_chance])[0]
            rolled_deck[rolled_champ] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount

    # Special Case not enough champs to fill the amount
    if remaining_champ_slots > 0:
        if fill_up_one_and_two_ofs_if_out_of_rollable_cards:
            for key, value in rolled_deck.items():
                if remaining_champ_slots == 0:
                    break
                if value == 1 and remaining_champ_slots == 1:
                    rolled_deck[key] = 2
                    remaining_champ_slots = 0
                    remaining_deck_slots -= 1
                elif value == 1 and remaining_champ_slots > 1:
                    rolled_deck[key] = 3
                    remaining_champ_slots -= 2
                    remaining_deck_slots -= 2
                elif value == 2 and remaining_champ_slots >= 1:
                    rolled_deck[key] = 3
                    remaining_champ_slots -= 1
                    remaining_deck_slots -= 1
            if remaining_champ_slots > 0:
                return f"Error - no champ for rolling included / left for the regions {rolled_regions} even after filling up one and two ofs"
        else:
            return f"Error - no champ for rolling included / left for the regions {rolled_regions}"

    # Roll the non champs
    while remaining_deck_slots > 0:
        if sum(rollable_non_champ_weights) == 0:
            break
        rolled_non_champ = random.choices(rollable_non_champ_card_codes, weights=rollable_non_champ_weights)[0]
        rollable_non_champ_weights[rollable_non_champ_card_codes.index(rolled_non_champ)] = 0
        if remaining_deck_slots == 1:
            rolled_deck[rolled_non_champ] = 1
            remaining_champ_slots -= 1
            remaining_deck_slots -= 1
        elif remaining_deck_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=[one_of_chance, two_of_chance])[0]
            rolled_deck[rolled_non_champ] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount
        else:
            rolled_amount = random.choices(range(1, 4), weights=[one_of_chance, two_of_chance, three_of_chance])[0]
            rolled_deck[rolled_non_champ] = rolled_amount
            remaining_champ_slots -= rolled_amount
            remaining_deck_slots -= rolled_amount

    # Special Case not enough cards to fill the deck
    if remaining_deck_slots > 0:
        if fill_up_one_and_two_ofs_if_out_of_rollable_cards:
            for key, value in rolled_deck.items():
                # To skip champs (otherwise this may lead to more champs in the deck than specified)
                is_champ = False
                for champ in all_champs:
                    if champ.card_code == key:
                        is_champ = True
                        break
                if is_champ:
                    continue
                if remaining_deck_slots == 0:
                    break
                if value == 1 and remaining_deck_slots == 1:
                    rolled_deck[key] = 2
                    remaining_champ_slots = 0
                    remaining_deck_slots -= 1
                elif value == 1 and remaining_deck_slots > 1:
                    rolled_deck[key] = 3
                    remaining_champ_slots -= 2
                    remaining_deck_slots -= 2
                elif value == 2 and remaining_deck_slots >= 1:
                    rolled_deck[key] = 3
                    remaining_champ_slots -= 1
                    remaining_deck_slots -= 1
            if remaining_deck_slots > 0:
                return f"Error - not enough cards for rolling included / left for the regions {rolled_regions} even after filling up one and two ofs"
        else:
            return f"Error - not enough cards for rolling included / left for the regions {rolled_regions}"

    # Get the deckcode
    rolled_deck_array = []
    for key, value in rolled_deck.items():
        rolled_deck_array.append(f"{value}:{key}")
    lor_deck = lor_deckcodes.LoRDeck(rolled_deck_array)
    deck_code = lor_deck.encode()
    return deck_code

def create_tournament_spreadsheat(amount_players: int, amount_decks_per_player: int = 1, link_to_website_for_showing_the_deck: bool = False, link_prefix_before_deck_code: str = "", allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> None:
    '''Creates a Excel-File for the given amount players and decks_per_player and the specified deckroll modifications'''
    start_time = time.time()
    date_today = str(date.today())
    with xlsxwriter.Workbook(f"Random Deck Tournament {date_today}.xlsx") as workbook:
        worksheet = workbook.add_worksheet()
        if link_to_website_for_showing_the_deck:
            first_line = ["Player"] + ["Deck", "Link"] * amount_decks_per_player
        else:
            first_line = ["Player"] + ["Deck"] * amount_decks_per_player
        for column, element in enumerate(first_line):
            worksheet.write(0, column, element)
        for row in range(1, amount_players + 1):
            for deck in range(amount_decks_per_player):
                deck_code = deckroll(allowed_cards=allowed_cards, weight_cards=weight_cards, card_weights=card_weights, total_amount_cards=total_amount_cards, amount_champs=amount_champs, regions=regions, weight_regions=weight_regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs = allow_two_runeterra_champs, one_of_chance=one_of_chance, two_of_chance=two_of_chance, three_of_chance=three_of_chance, fill_up_one_and_two_ofs_if_out_of_rollable_cards=fill_up_one_and_two_ofs_if_out_of_rollable_cards)
                if link_to_website_for_showing_the_deck:
                    worksheet.write(row, 1 + deck * 2, deck_code)
                    worksheet.write(row, 1 + deck * 2 + 1, f"{link_prefix_before_deck_code}{deck_code}")
                else:
                    worksheet.write(row, 1 + deck, deck_code)
    end_time = time.time()
    print(f"finished after {str(round(end_time-start_time, 3))} seconds - Random Deck Tournament {date_today}.xlsx was created in the current folder")

def create_mm_tournament_spreadsheat(amount_players: int, link_prefix_before_deck_code: str = "", allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> None:
    '''Creates a Excel-File for the given amount players and the specified deckroll modifications'''
    start_time = time.time()
    date_today = str(date.today())
    filename = f"Random Deck Tournament {date_today}.xlsx"
    with xlsxwriter.Workbook(filename) as workbook:
        worksheet = workbook.add_worksheet()
        first_line = ["Player"] + ["Deck Link", "Deck Code"] * 2
        for column, element in enumerate(first_line):
            worksheet.write(0, column, element)
        for row in range(1, amount_players + 1):
            deck_code = deckroll(allowed_cards=allowed_cards, weight_cards=weight_cards, card_weights=card_weights, total_amount_cards=total_amount_cards, amount_champs=amount_champs, regions=regions, weight_regions=weight_regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs = allow_two_runeterra_champs, one_of_chance=one_of_chance, two_of_chance=two_of_chance, three_of_chance=three_of_chance, fill_up_one_and_two_ofs_if_out_of_rollable_cards=fill_up_one_and_two_ofs_if_out_of_rollable_cards)
            worksheet.write_formula(row, 1, f"=HYPERLINK(\"{link_prefix_before_deck_code}\"&C{row+1})")
            worksheet.write(row, 2, deck_code)
            worksheet.write_formula(row, 3, f"=HYPERLINK(\"{link_prefix_before_deck_code}\"&E{row+1})")
    end_time = time.time()
    print(f"finished after {str(round(end_time-start_time, 3))} seconds - {filename} was created in the current folder")

def create_mm_reroll_spreadsheat(amount_decks: int, allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> None:
    '''Creates a Excel-File with numbers and decks with the specified deckroll modifications'''
    start_time = time.time()
    date_today = str(date.today())
    filename = f"Random Deck Tournament Reroll Decks {date_today}.xlsx"
    with xlsxwriter.Workbook(filename) as workbook:
        worksheet = workbook.add_worksheet()
        first_line = ["Number", "Deckcode"]
        for column, element in enumerate(first_line):
            worksheet.write(0, column, element)
        for row in range(1, amount_decks + 1):
            deck_code = deckroll(allowed_cards=allowed_cards, weight_cards=weight_cards, card_weights=card_weights, total_amount_cards=total_amount_cards, amount_champs=amount_champs, regions=regions, weight_regions=weight_regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs = allow_two_runeterra_champs, one_of_chance=one_of_chance, two_of_chance=two_of_chance, three_of_chance=three_of_chance, fill_up_one_and_two_ofs_if_out_of_rollable_cards=fill_up_one_and_two_ofs_if_out_of_rollable_cards)
            worksheet.write(row, 0, row)
            worksheet.write(row, 1, deck_code)
    end_time = time.time()
    print(f"finished after {str(round(end_time-start_time, 3))} seconds - {filename} was created in the current folder")

# Make Region Runeterra very likely:
# region_weights[all_regions.index("Runeterra")] = 20
# Exclude a region:
# region_weights[all_regions.index("Demacia")] = 0
# Make newest cards more likely:
# for index, card in enumerate(collectible_cards):
#     if card.card_set == "Set6":
#         card_weights[index] = 10
#create_tournament_spreadsheat(amount_players=100, amount_decks_per_player=1, link_to_website_for_showing_the_deck=True, link_prefix_before_deck_code="https://masteringruneterra.com/deck/", allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)

#create_mm_tournament_spreadsheat(amount_players=100, link_prefix_before_deck_code="https://masteringruneterra.com/deck/", allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)
create_mm_reroll_spreadsheat(amount_decks=30, allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)
