import lor_deckcodes
import os
import json
from typing import List, NamedTuple
import random
from datetime import date
import xlsxwriter
import time
import copy
import string

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
        print(card_set_file_json)
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
        for associated_card in collectible_card.associated_card_refs:
            for uncollectible_card in uncollectible_cards:
                if uncollectible_card.card_code == associated_card:
                    if "Skill" in uncollectible_card.keyword_refs and collectible_card not in jhin_followers:
                        jhin_followers.append(collectible_card)
                    break

ryze_follower_names: List[str] = ["Feral Prescience", "Warning Shot", "Advanced Intel", "Bandle Tellstones", "Bilgewater Tellstones", "Bloodbait", "Construct of Desolation", "Demacian Tellstones", "Fae Sprout", "Heavens Aligned", "Imagined Possibilities", "Ionian Tellstones", "Jettison", "Jury-Rig", "Messenger's Sigil", "Mushroom Cloud", "Noxian Tellstones", "Piltovan Tellstones", "Ranger's Resolve", "Ransom Riches", "Sapling Toss", "Shadow Isles Tellstones", "Shroud of Darkness", "Shuriman Tellstones", "Spell Thief", "Stoneweaving", "Stress Testing", "Targonian Tellstones", "Tempting Prospect", "Three Sisters", "Trinket Trade", "Allure", "Ancestral Boon", "Behold the Infinite", "Calculated Creations", "Discreet Invitation", "Encore", "Entrapment", "Entreat", "Field Promotion", "Gifts From Beyond", "Icathian Myths", "Insight of Ages", "Line 'Em Up", "Magical Journey", "Payday", "Poro Stories", "Rite of Passage", "Shared Spoils", "Sown Seeds", "Starbone", "Supercool Starchart", "Swindle", "Time Trick", "Trail of Evidence", "Arise!", "Call the Wild", "Dragon's Clutch", "En Garde", "Fae Aid", "Flash of Brilliance", "Formal Invitation", "Lure of the Depths", "Mobilize", "Pilfered Goods", "Poro Snax", "Sap Magic", "Stalking Shadows", "Starlit Epiphany", "Unraveled Earth", "Vision", "Encroaching Shadows", "Lost Riches", "Risen Mists", "Salvage", "Sneezy Biggledust!", "Stand Alone", "The Unending Wave", "The Unforgiving Cold", "Whispered Words", "Catalyst of Aeons", "Deep Meditation", "Drum Solo", "Eye of Nagakabouros", "Gift of the Hearthblood", "Nine Lives", "Portalpalooza", "The Time Has Come", "Aurora Porealis", "Celestial Trifecta", "Glory's Call", "Hextech Anomaly", "Hidden Pathways", "Sands of Time", "Shaman's Call", "Eclectic Collection", "Servitude of Desolation", "Spirit Fire", "Sputtering Songspinner", "Progress Day!", "Voices of the Old Ones"]
ryze_followers: List[lor_card] = []
for collectible_card in collectible_cards:
    if collectible_card.name in ryze_follower_names:
        ryze_followers.append(collectible_card)

def check_input_parameters(allowed_cards: List[lor_card], weight_cards: bool, card_weights: List[int], total_amount_cards: int, amount_champs: int, regions: List[str], weight_regions: bool, region_weights: List[int], mono_region_chance: int, allow_two_runeterra_champs: bool, one_of_chance: int, two_of_chance: int, three_of_chance: int, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool) -> None | str:
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
        return "Error - Runeterra can't be in the allowed regions without any champs allowed"
    if weight_cards and len(allowed_cards) != len(card_weights):
        return "Error - The length of given cards and card weights has to be equal, when cards should be weighted"
    if weight_regions and len(regions) != len(region_weights):
        return "Error - The length of given regions and region weights has to be equal, when cards should be weighted"
    return None

def roll_regions(amount_champs: int, regions: List[str], region_weights: List[int], mono_region_chance: int, allow_two_runeterra_champs: bool) -> List[str]:
    rolled_regions: List[str] = []
    # Monoregion deck
    if mono_region_chance > random.randrange(100):
        # Don't allow Runeterra as Mono-Region, because the card pool is too small
        if "Runeterra" in regions:
            region_weights[regions.index("Runeterra")] = 0
        rolled_region = random.choices(regions, weights=region_weights)[0]
        rolled_regions.append(rolled_region)
    # Two region deck
    else:
        for i in range(2):
            rolled_region = random.choices(regions, weights=region_weights)[0]
            rolled_regions.append(rolled_region)
            # Prevents duplicated rolled region
            if not (allow_two_runeterra_champs and amount_champs > 1 and rolled_region == "Runeterra"):
                region_weights[regions.index(rolled_region)] = 0
    return rolled_regions

def init_runeterra_champs(allowed_cards: List[lor_card], card_weights: List[int], runeterra_champs: List[lor_card], runeterra_champ_weights: List[int]) -> None:
    for index, allowed_card in enumerate(allowed_cards):
        if "Runeterra" in allowed_card.region_refs and allowed_card.is_champ and allowed_card not in runeterra_champs:
            runeterra_champs.append(allowed_card)
            runeterra_champ_weights.append(card_weights[index])

def roll_runeterra_champs(runeterra_champs: List[lor_card], runeterra_champ_weights: List[int], runeterra_champ_amount: int) -> List[lor_card]:
    rolled_runeterra_champs: List[lor_card] = []
    for i in range(runeterra_champ_amount):
        rolled_runeterra_champ = random.choices(runeterra_champs, weights=runeterra_champ_weights)[0]
        rolled_runeterra_champs.append(rolled_runeterra_champ)
        runeterra_champ_weights[runeterra_champs.index(rolled_runeterra_champ)] = 0
    return rolled_runeterra_champs

def add_runeterra_champs_to_deck(rolled_deck: dict[str, int], remaining_champ_slots: int, rolled_runeterra_champs: List[lor_card], card_amount_chances: List[int]) -> int:
    if len(rolled_runeterra_champs) == 1:
        if remaining_champ_slots == 1:
            rolled_amount = 1
            rolled_deck[rolled_runeterra_champs[0].card_code] = rolled_amount
        elif remaining_champ_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=card_amount_chances[0:2])[0]
            rolled_deck[rolled_runeterra_champs[0].card_code] = rolled_amount
        else:
            rolled_amount = random.choices(range(1, 4), weights=card_amount_chances)[0]
            rolled_deck[rolled_runeterra_champs[0].card_code] = rolled_amount
        return rolled_amount
    elif len(rolled_runeterra_champs) == 2:
        if remaining_champ_slots >= 6:
            rolled_deck[rolled_runeterra_champs[0].card_code] = 3
            rolled_deck[rolled_runeterra_champs[1].card_code] = 3
        elif remaining_champ_slots % 2 == 0:
            rolled_deck[rolled_runeterra_champs[0].card_code] = remaining_champ_slots // 2
            rolled_deck[rolled_runeterra_champs[1].card_code] = remaining_champ_slots // 2
        else:
            rolled_deck[rolled_runeterra_champs[0].card_code] = remaining_champ_slots // 2 + 1
            rolled_deck[rolled_runeterra_champs[1].card_code] = remaining_champ_slots // 2
        if remaining_champ_slots > 6:
            return 6
        else:
            return remaining_champ_slots

def add_rollable_non_champs_and_weights_for_rolled_runeterra_champs(allowed_cards: List[lor_card], card_weights: List[int], rolled_runeterra_champs: List[lor_card], rollable_non_champ_card_codes: List[str], rollable_non_champ_weights=List[int]) -> None:
    rolled_runeterra_champ_names = []
    for rolled_runeterra_champ in rolled_runeterra_champs:
        rolled_runeterra_champ_names.append(rolled_runeterra_champ.name)
    if "Aatrox" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if "DARKIN" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Bard" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            # "06RU001T3" is the Chime Card
            if "06RU001T3" in allowed_card.associated_card_refs and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Evelynn" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if "Husk" in allowed_card.description_raw and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Jax" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if "WEAPONMASTER" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Jhin" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if allowed_card in jhin_followers and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Kayn" in rolled_runeterra_champ_names or "Varus" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if "CULTIST" in allowed_card.subtypes and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    if "Ryze" in rolled_runeterra_champ_names:
        for index, allowed_card in enumerate(allowed_cards):
            if allowed_card in ryze_followers and allowed_card.card_code not in rollable_non_champ_card_codes:
                rollable_non_champ_card_codes.append(allowed_card.card_code)
                rollable_non_champ_weights.append(card_weights[index])
    

def add_rollable_cards_and_weights_for_rolled_regions_other_than_runeterra(allowed_cards: List[lor_card], rolled_regions: List[str], rollable_champ_card_codes: List[str], rollable_champ_weights: List[int], rollable_non_champ_card_codes: List[str], rollable_non_champ_weights: List[int]) -> None:
    for rolled_region in rolled_regions:
        if rolled_region != "Runeterra":
            for index, allowed_card in enumerate(allowed_cards):
                if rolled_region in allowed_card.region_refs and allowed_card.is_champ and allowed_card.card_code not in rollable_champ_card_codes:
                    rollable_champ_card_codes.append(allowed_card.card_code)
                    rollable_champ_weights.append(card_weights[index])
                elif rolled_region in allowed_card.region_refs and not allowed_card.is_champ and allowed_card.card_code not in rollable_non_champ_card_codes:
                    rollable_non_champ_card_codes.append(allowed_card.card_code)
                    rollable_non_champ_weights.append(card_weights[index])

def roll_non_runeterra_champs(rolled_deck: dict[str, int], remaining_champ_slots: int, card_amount_chances: List[int], rollable_champ_card_codes: List[str], rollable_champ_weights: List[int]) -> int:
    amount_cards_added_to_the_deck: int = 0
    total_rollable_champ_weights: int = sum(rollable_champ_weights)
    while remaining_champ_slots > 0:
        if total_rollable_champ_weights == 0:
            break
        rolled_champ = random.choices(rollable_champ_card_codes, weights=rollable_champ_weights)[0]
        # Remove card from pool by settings the chance of rolling it to 0
        total_rollable_champ_weights -= rollable_champ_weights[rollable_champ_card_codes.index(rolled_champ)]
        rollable_champ_weights[rollable_champ_card_codes.index(rolled_champ)] = 0
        if remaining_champ_slots == 1:
            rolled_amount = 1
        elif remaining_champ_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=card_amount_chances[0:2])[0]
        else:
            rolled_amount = random.choices(range(1, 4), weights=card_amount_chances)[0]
        rolled_deck[rolled_champ] = rolled_amount
        remaining_champ_slots -= rolled_amount
        amount_cards_added_to_the_deck += rolled_amount
    return amount_cards_added_to_the_deck

def fill_up_champ_one_and_two_ofs(rolled_deck: dict[str, int], remaining_champ_slots=int) -> int:
    amount_cards_added_to_the_deck: int = 0
    for key, value in rolled_deck.items():
        if remaining_champ_slots == 0:
            break
        if value == 1 and remaining_champ_slots == 1:
            rolled_deck[key] = 2
            remaining_champ_slots -= 1
            amount_cards_added_to_the_deck += 1
        elif value == 1 and remaining_champ_slots > 1:
            rolled_deck[key] = 3
            remaining_champ_slots -= 2
            amount_cards_added_to_the_deck += 2
        elif value == 2 and remaining_champ_slots >= 1:
            rolled_deck[key] = 3
            remaining_champ_slots -= 1
            amount_cards_added_to_the_deck += 1
    return amount_cards_added_to_the_deck
            
def roll_non_champs(rolled_deck: dict[str, int], remaining_deck_slots: int, card_amount_chances: List[int], rollable_non_champ_card_codes: List[str], rollable_non_champ_weights: List[int]) -> int:
    amount_cards_added_to_the_deck: int = 0
    total_rollable_non_champ_weights: int = sum(rollable_non_champ_weights)
    while remaining_deck_slots > 0:
        if total_rollable_non_champ_weights == 0:
            break
        rolled_non_champ = random.choices(rollable_non_champ_card_codes, weights=rollable_non_champ_weights)[0]
        # Remove card from pool by settings the chance of rolling it to 0
        total_rollable_non_champ_weights -= rollable_non_champ_weights[rollable_non_champ_card_codes.index(rolled_non_champ)]
        rollable_non_champ_weights[rollable_non_champ_card_codes.index(rolled_non_champ)] = 0
        if remaining_deck_slots == 1:
            rolled_amount = 1
        elif remaining_deck_slots == 2:
            rolled_amount = random.choices(range(1, 3), weights=card_amount_chances[0:2])[0]
        else:
            rolled_amount = random.choices(range(1, 4), weights=card_amount_chances)[0]
        rolled_deck[rolled_non_champ] = rolled_amount
        remaining_deck_slots -= rolled_amount
        amount_cards_added_to_the_deck += rolled_amount
    return amount_cards_added_to_the_deck

def fill_up_non_champ_one_and_two_ofs(rolled_deck: dict[str, int], remaining_deck_slots=int) -> int:
    amount_cards_added_to_the_deck: int = 0
    for key, value in rolled_deck.items():
        if remaining_deck_slots == 0:
            break
        if value == 1 and remaining_deck_slots == 1:
            rolled_deck[key] = 2
            remaining_deck_slots -= 1
            amount_cards_added_to_the_deck += 1
        elif value == 1 and remaining_deck_slots > 1:
            rolled_deck[key] = 3
            remaining_deck_slots -= 2
            amount_cards_added_to_the_deck += 2
        elif value == 2 and remaining_deck_slots >= 1:
            rolled_deck[key] = 3
            remaining_deck_slots -= 1
            amount_cards_added_to_the_deck += 1
    return amount_cards_added_to_the_deck

def get_deckcode_for_rolled_deck(rolled_deck: dict[str, int]) -> str:
    rolled_deck_formatted = []
    for key, value in rolled_deck.items():
        rolled_deck_formatted.append(f"{value}:{key}")
    lor_deck = lor_deckcodes.LoRDeck(rolled_deck_formatted)
    deck_code = lor_deck.encode()
    return deck_code

def deckroll(allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> str:
    # CHECK INPUT PARAMETERS
    error = check_input_parameters(allowed_cards=allowed_cards, weight_cards=weight_cards, card_weights=card_weights, total_amount_cards=total_amount_cards, amount_champs=amount_champs, regions=regions, weight_regions=weight_regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs=allow_two_runeterra_champs, one_of_chance=one_of_chance, two_of_chance=two_of_chance, three_of_chance=three_of_chance, fill_up_one_and_two_ofs_if_out_of_rollable_cards=fill_up_one_and_two_ofs_if_out_of_rollable_cards)
    if error:
        return error
    
    # INIT VARIABLES
    # rolled deck is a dictionary, that consists of card-codes and amount of the card
    card_amount_chances: List[int] = [one_of_chance, two_of_chance, three_of_chance]
    rolled_deck: dict[str, int] = {}
    rollable_champ_card_codes: List[str] = []
    rollable_champ_weights: List[int] = []
    rollable_non_champ_card_codes: List[str] = []
    rollable_non_champ_weights: List[int] = []
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
    
    # ROLL REGIONS
    rolled_regions: List[str] = roll_regions(amount_champs=amount_champs, regions=regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs=allow_two_runeterra_champs)
    
    # ROLL RUNETERRA CHAMPS
    if "Runeterra" in rolled_regions:
        # INIT AVAILABLE RUNETERRA-CHAMPS AND WEIGHTS
        runeterra_champs: List[lor_card] = []
        runeterra_champ_weights: List[int] = []
        init_runeterra_champs(allowed_cards=allowed_cards, card_weights=card_weights, runeterra_champs=runeterra_champs, runeterra_champ_weights=runeterra_champ_weights)
        if len(runeterra_champs) < rolled_regions.count("Runeterra"):
            return f"Error - not enough Runeterra Champs for rolling included - {len(runeterra_champs)} for a {rolled_regions.count('Runeterra')} runeterra champ deck"
        # ROLL RUNETERRA CHAMPS
        rolled_runeterra_champs: List[lor_card] = roll_runeterra_champs(runeterra_champs=runeterra_champs, runeterra_champ_weights=runeterra_champ_weights, runeterra_champ_amount=rolled_regions.count("Runeterra"))
        # ROLL AMOUNT AND ADD ROLLED RUNETERRA CHAMPS TO THE DECK
        cards_added_to_the_deck = add_runeterra_champs_to_deck(rolled_deck=rolled_deck, remaining_champ_slots=remaining_champ_slots, rolled_runeterra_champs=rolled_runeterra_champs, card_amount_chances=card_amount_chances)
        remaining_deck_slots -= cards_added_to_the_deck
        remaining_champ_slots -= cards_added_to_the_deck
        # ADD ROLLABLE NON CHAMPS TO THE RESPECTIVE LIST
        add_rollable_non_champs_and_weights_for_rolled_runeterra_champs(allowed_cards=allowed_cards, card_weights=card_weights, rolled_runeterra_champs=rolled_runeterra_champs, rollable_non_champ_card_codes=rollable_non_champ_card_codes, rollable_non_champ_weights=rollable_non_champ_weights)
    
    # ADD ROLLABLE CARDS AND WEIGHTS FROM OTHER REGIONS THAN RUNETERRA TO THEIR RESPECTIVE LISTS
    add_rollable_cards_and_weights_for_rolled_regions_other_than_runeterra(allowed_cards=allowed_cards, rolled_regions=rolled_regions, rollable_champ_card_codes=rollable_champ_card_codes, rollable_champ_weights=rollable_champ_weights, rollable_non_champ_card_codes=rollable_non_champ_card_codes, rollable_non_champ_weights=rollable_non_champ_weights)
    
    # ROLL THE DECK
    # ROLL THE CHAMPS
    amount_cards_added_to_the_deck = roll_non_runeterra_champs(rolled_deck=rolled_deck, remaining_champ_slots=remaining_champ_slots, card_amount_chances=card_amount_chances, rollable_champ_card_codes=rollable_champ_card_codes, rollable_champ_weights=rollable_champ_weights)
    remaining_champ_slots -= amount_cards_added_to_the_deck
    remaining_deck_slots -= amount_cards_added_to_the_deck

    # FILL UP CHAMP SLOTS, IF NOT ALL CHAMP SLOTS ARE USED AND THE OPTION IS ENABLED
    if remaining_champ_slots > 0:
        if fill_up_one_and_two_ofs_if_out_of_rollable_cards:
            amount_cards_added_to_the_deck = fill_up_champ_one_and_two_ofs(rolled_deck=rolled_deck, remaining_champ_slots=remaining_champ_slots)
            remaining_champ_slots -= amount_cards_added_to_the_deck
            remaining_deck_slots -= amount_cards_added_to_the_deck
            if remaining_champ_slots > 0:
                return f"Error - no champ for rolling included / left for the regions {rolled_regions} even after filling up one and two ofs"
        else:
            return f"Error - no champ for rolling included / left for the regions {rolled_regions}"

    # ROLL THE NON CHAMPS
    amount_cards_added_to_the_deck = roll_non_champs(rolled_deck=rolled_deck, remaining_deck_slots=remaining_deck_slots, card_amount_chances=card_amount_chances, rollable_non_champ_card_codes=rollable_non_champ_card_codes, rollable_non_champ_weights=rollable_non_champ_weights)
    remaining_deck_slots -= amount_cards_added_to_the_deck

    # FILL UP DECK SLOTS, IF NOT ALL DECK SLOTS ARE USED AND THE OPTION IS ENABLED
    if remaining_deck_slots > 0:
        if fill_up_one_and_two_ofs_if_out_of_rollable_cards:
            amount_cards_added_to_the_deck = fill_up_non_champ_one_and_two_ofs(rolled_deck=rolled_deck, remaining_deck_slots=remaining_deck_slots)
            remaining_deck_slots -= amount_cards_added_to_the_deck
            if remaining_deck_slots > 0:
                return f"Error - not enough cards for rolling included / left for the regions {rolled_regions} even after filling up one and two ofs"
        else:
            return f"Error - not enough cards for rolling included / left for the regions {rolled_regions}"

    # GET AND RETURN THE DECKCODE
    deck_code = get_deckcode_for_rolled_deck(rolled_deck=rolled_deck)
    return deck_code

def multiple_deckrolls_and_removing_rolled_cards(amount_decks: int, allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> List[str]:
    '''Creates a Excel-File with numbers and decks with the specified deckroll modifications and with a card_pool, that gets smaller each deck'''
    rolled_decks: List[str] = []
    allowed_cards = copy.deepcopy(allowed_cards)
    card_weights = copy.deepcopy(card_weights)
    regions = copy.deepcopy(regions)
    region_weights = copy.deepcopy(region_weights)
    for i in range(amount_decks):
        deck_code = deckroll(allowed_cards=allowed_cards, weight_cards=weight_cards, card_weights=card_weights, total_amount_cards=total_amount_cards, amount_champs=amount_champs, regions=regions, weight_regions=weight_regions, region_weights=region_weights, mono_region_chance=mono_region_chance, allow_two_runeterra_champs = allow_two_runeterra_champs, one_of_chance=one_of_chance, two_of_chance=two_of_chance, three_of_chance=three_of_chance, fill_up_one_and_two_ofs_if_out_of_rollable_cards=fill_up_one_and_two_ofs_if_out_of_rollable_cards)
        rolled_decks.append(deck_code)
        if not deck_code.startswith("Error"):
            deck = lor_deckcodes.LoRDeck.from_deckcode(deck_code)
            for deck_card in deck.cards:
                for index, allowed_card in enumerate(allowed_cards):
                    if allowed_card.card_code == deck_card.card_code:
                        del allowed_cards[index]
                        del card_weights[index]
                        # Runeterra can be excluded from the list if all champs are rolled
                        if "Runeterra" in allowed_card.region_refs:
                            not_rolled_runeterra_champs = 0
                            for allowed_card in allowed_cards:
                                if "Runeterra" in allowed_card.region_refs:
                                    not_rolled_runeterra_champs += 1
                            if not_rolled_runeterra_champs == 0:
                                del region_weights[regions.index("Runeterra")]
                                del regions[regions.index("Runeterra")]
                        break
    return rolled_decks

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

default_allowed_letters: List[str] = list(string.ascii_letters + "!" + "?" + "." + " ")
def create_txt_file_with_card_names(allowed_cards: List[lor_card] = collectible_cards, allowed_letters: List[str] = default_allowed_letters) -> None:
    # This text file can be used for scribbl with custom words
    card_names_formatted: List[str] = []
    for allowed_card in allowed_cards:
        card_name = allowed_card.name
        card_name_formatted = ""
        for letter in card_name:
            if letter in allowed_letters:
                card_name_formatted += letter
        card_names_formatted.append(card_name_formatted)
    date_today = str(date.today())
    filename = f"Card names {date_today}.txt"
    with open(filename, "w") as file:
        file.write(str(card_names_formatted))
    print(f"{filename} was created in the current folder")

# Check if runeterra champ followers are correct (biggest part manually) -- prints amount of associated cards
#runeterra_champ_names = ["Jax", "Bard", "Evelynn", "Jhin", "Ryze", "Kayn", "Varus", "Kayn", "Aatrox"]
#runeterra_champs: List[lor_card] = []
#for collectible_card in collectible_cards:
#    if collectible_card.name in runeterra_champ_names:
#        runeterra_champs.append(collectible_card)
#for runeterra_champ in runeterra_champs:
#    associated_follower_card_codes: List[str] = []
#    add_rollable_non_champs_and_weights_for_rolled_runeterra_champs(allowed_cards=collectible_cards, card_weights=card_weights, rolled_runeterra_champs=[runeterra_champ], rollable_non_champ_card_codes=associated_follower_card_codes, rollable_non_champ_weights=card_weights)
#    print(f"{runeterra_champ.name} has {len(associated_follower_card_codes)} associated cards!")

# Make Region Runeterra very likely:
# region_weights[all_regions.index("Runeterra")] = 20

# Exclude a region:
# region_weights[all_regions.index("Demacia")] = 0

# Make newest cards more likely:
# (Card Codes from Aatrox Expansion)
new_card_codes = ['06NX041', '06NX039', '06RU006', '06RU006T2', '06RU006T12', '06RU006T3', '06RU006T7', '06RU006T6', '06RU006T9', '06RU006T5', '06RU006T1', '06RU006T11', '06RU006T4', '06RU006T8', '06RU026', '06RU026T2', '06RU026T1', '06RU026T7', '06RU026T3', '06RU026T6', '06RU026T4', '06RU026T5', '06RU043', '06RU039', '06FR018', '06FR027', '06FR036', '06FR021', '06FR035', '06FR018T1', '06FR018T3', '06BC023', '06BC043', '06BC029', '06BC029T3', '06BC029T1', '06BC042', '06IO023', '06IO039', '06IO023T3', '06IO023T1', '06IO040', '06IO039T2', '06IO039T1', '06IO037', '06PZ006', '06PZ010', '06PZ041', '06PZ009', '06BW040', '06BW044', '06MT007', '06MT018', '06MT018T1', '06MT031', '06MT010', '06MT016', '06MT015', '06MT008', '06MT008T2', '06MT008T1', '06MT035', '06MT017', '06MT035T1', '06MT052', '06SH051', '06SH046', '06SH028', '06DE041', '06DE044', '06DE043', '06DE039', '06SI042', '06SI039', '06SI038'] 
for index, card in enumerate(collectible_cards):
    if card.card_code in new_card_codes:
        card_weights[index] = 20

#create_tournament_spreadsheat(amount_players=100, amount_decks_per_player=1, link_to_website_for_showing_the_deck=True, link_prefix_before_deck_code="https://masteringruneterra.com/deck/", allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)
#create_mm_tournament_spreadsheat(amount_players=100, link_prefix_before_deck_code="https://masteringruneterra.com/deck/", allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)
#create_mm_reroll_spreadsheat(amount_decks=10000, allowed_cards=collectible_cards, weight_cards=True, card_weights=card_weights, total_amount_cards=40, amount_champs=6, regions=all_regions, weight_regions=True, region_weights=region_weights, mono_region_chance=0, allow_two_runeterra_champs=True, one_of_chance=20, two_of_chance=30, three_of_chance=50, fill_up_one_and_two_ofs_if_out_of_rollable_cards=True)
#print(multiple_deckrolls_and_removing_rolled_cards(50))
#create_txt_file_with_card_names()
