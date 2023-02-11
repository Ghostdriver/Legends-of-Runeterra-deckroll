from typing import List, Dict, Literal
from CardData import CardData, CARD_SETS
import requests
import json
from functools import cache
from zipfile import ZipFile
from io import BytesIO
import os
import string
from datetime import date

class CardPool:
    def __init__(self, api_or_local: Literal["API", "LOCAL"], ryze_follower_names: List[str] = []) -> None:
        '''All parameters get passed to get_all_cards, which is not a class function to make it cacheable'''
        self.all_cards: List[CardData] = get_all_cards(api_or_local=api_or_local)
        self.collectible_cards: List[CardData] = []
        self.uncollectible_cards: List[CardData] = []
        self.all_champs: List[CardData] = []
        self.runeterra_champs: List[CardData] = []
        self.non_runeterra_champs: List[CardData] = []
        self.all_non_champs: List[CardData] = []
        for card in self.all_cards:
            if card.is_collectible:
                self.collectible_cards.append(card)
                if card.is_champ:
                    self.all_champs.append(card)
                    if "Runeterra" in card.region_refs:
                        self.runeterra_champs.append(card)
                    else:
                        self.non_runeterra_champs.append(card)
                else:
                    self.all_non_champs.append(card)
            else:
                self.uncollectible_cards.append(card)
        print(f"CardPool initialized with {len(self.collectible_cards)} collectible cards")
        print(f"CardPool initialized with {len(self.uncollectible_cards)} uncollectible cards")
        print(f"CardPool initialized with {len(self.all_champs)} champion cards")
        print(f"CardPool initialized with {len(self.runeterra_champs)} runeterra champion cards")
        print(f"CardPool initialized with {len(self.non_runeterra_champs)} non runeterra champion cards")
        print(f"CardPool initialized with {len(self.all_non_champs)} non champion cards")
        # RUNETERRA CHAMPS
        self.aatrox_followers: List[CardData] = []
        self.bard_followers: List[CardData] = []
        self.evelynn_followers: List[CardData] = []
        self.jax_followers: List[CardData] = []
        self.jhin_followers: List[CardData] = []
        self.kayn_and_varus_followers: List[CardData] = []
        self.ryze_followers: List[CardData] = []
        self.RUNETERRA_CHAMPS_NAMES_FOLLOWER_LIST_DICT: Dict[str, List[CardData]] = {
            "Aatrox": self.aatrox_followers,
            "Bard": self.bard_followers,
            "Evelynn": self.evelynn_followers,
            "Jax": self.jax_followers,
            "Jhin": self.jhin_followers,
            "Kayn": self.kayn_and_varus_followers,
            "Ryze": self.ryze_followers,
            "Varus": self.kayn_and_varus_followers
        }
        # Aatrox
        for non_champ in self.all_non_champs:
            if "DARKIN" in non_champ.subtypes:
                self.aatrox_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.aatrox_followers)} Cards for Aatrox")
        # Bard
        for non_champ in self.all_non_champs:
            # "06RU001T3" is the Chime Card
            CHIME_CARD_CARD_CODE = "06RU001T3"
            if CHIME_CARD_CARD_CODE in non_champ.associated_card_refs:
                self.bard_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.bard_followers)} Cards for Bard")
        # Evelynn
        for non_champ in self.all_non_champs:
            if "Husk" in non_champ.description_raw:
                self.evelynn_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.evelynn_followers)} Cards for Evelynn")
        # Jax
        for non_champ in self.all_non_champs:
            if "WEAPONMASTER" in non_champ.subtypes:
                self.jax_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.jax_followers)} Cards for Jax")
        # Jhin
        for non_champ in self.all_non_champs:
            for associated_card in non_champ.associated_card_refs:
                for uncollectible_card in self.uncollectible_cards:
                    if uncollectible_card.card_code == associated_card:
                        if "Skill" in uncollectible_card.keyword_refs:
                            self.jhin_followers.append(non_champ)
                            break
        print(f"CardPool initialized with {len(self.jhin_followers)} Cards for Jhin")
        # Kayn and Varus
        for non_champ in self.all_non_champs:
            if "CULTIST" in non_champ.subtypes:
                self.kayn_and_varus_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.kayn_and_varus_followers)} Cards for Kayn and Varus")
        # Ryze
        for non_champ in self.all_non_champs:
            if non_champ.name in ryze_follower_names:
                self.ryze_followers.append(non_champ)
        print(f"CardPool initialized with {len(self.ryze_followers)} Cards for Ryze")

    def get_card_by_card_code(self, card_code: str) -> CardData:
        for card in self.all_cards:
            if card.card_code == card_code:
                return card
        raise ValueError(f"No Card with card code {card_code} found")
    
    def create_txt_file_with_card_names(self) -> None:
        '''Creates a text file with all card names from collectible cards, which can be used for scribbl for example'''
        ALLOWED_LETTERS: List[str] = list(string.ascii_letters + "!" + "?" + "." + " ")
        card_names_formatted: List[str] = []
        for card in self.collectible_cards:
            card_name = card.name
            card_name_formatted = ""
            for letter in card_name:
                if letter in ALLOWED_LETTERS:
                    card_name_formatted += letter
            card_names_formatted.append(card_name_formatted)
        date_today = str(date.today())
        filename = "card_names.txt"
        with open(filename, "w") as file:
            file.write(str(sorted(card_names_formatted)))

@cache
def get_all_cards(api_or_local: Literal["API", "LOCAL"]) -> List[CardData]:
    """Get all cards from API or local files and convert them with CardData class"""
    all_cards = []
    if api_or_local == "API":
        print("Started fetching card sets from the API")
        card_sets = CARD_SETS
        for card_set in card_sets:
            r = requests.get(f"https://dd.b.pvp.net/latest/{card_set}-lite-en_us.zip")
            if r.status_code == 200:
                card_set_zip = ZipFile(BytesIO(r.content))
                card_set_json_path = f"en_us/data/{card_set}-en_us.json"
                card_set_json = json.loads(card_set_zip.open(card_set_json_path).read())
                for card in card_set_json:
                    all_cards.append(CardData(card))
            else:
                raise ConnectionError(f"Getting card set for {card_set} failed - Status Code: {r.status_code}")
            print(f"{card_set} fetched and parsed from the API succesfully")
    if api_or_local == "LOCAL":
        print("Started fetching card sets from local files")
        CARD_SETS_DIR = "card_sets"
        for card_set in os.listdir(CARD_SETS_DIR):
            with open(os.path.join(CARD_SETS_DIR, card_set), 'r', encoding='UTF-8') as f:
                card_set_json = json.loads(f.read())
                for card in card_set_json:
                    all_cards.append(CardData(card))
    print(f"CardPool initialized with {len(all_cards)} cards in total")
    return all_cards
