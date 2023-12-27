from typing import List, Dict, Literal
from CardData import CardData, CARD_SETS, LANGUAGES
import requests
import json
import string
import logging

DEFAULT_LOCALE = "en_us"

# Formatter, Stream Handler, Logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)


class CardPool:
    def __init__(self, format: Literal["client_Formats_Eternal_name", "client_Formats_Standard_name"] = "client_Formats_Standard_name") -> None:
        '''init card pool'''
        RYZE_FOLLOWER_NAMES = ["Feral Prescience", "Warning Shot", "Bandle Tellstones", "Bilgewater Tellstones", "Bloodbait", "Bursting Backpack", "Construct of Desolation", "Demacian Tellstones", "Facecheck", "Fae Sprout", "Heavens Aligned", "Imagined Possibilities", "Ionian Tellstones", "Jettison", "Jury-Rig", "Messenger's Sigil", "Mushroom Cloud", "Noxian Tellstones", "Piltovan Tellstones", "Ranger's Resolve", "Ransom Riches", "Sapling Toss", "Shadow Isles Tellstones", "Shroud of Darkness", "Shuriman Tellstones", "Spell Thief", "Stoneweaving", "Stress Testing", "Stylish Shot", "Targonian Tellstones", "Tempting Prospect", "Three Sisters", "Trinket Trade", "Advanced Intel", "Allure", "Ancestral Boon", "Behold the Infinite", "Calculated Creations", "Cosmic Call", "Discreet Invitation", "En Garde", "Encore", "Entrapment", "Entreat", "Field Promotion", "Gifts From Beyond", "Icathian Myths", "Insight of Ages", "Line 'Em Up", "Magical Journey", "Payday", "Poro Stories", "Rite of Passage", "Shared Spoils", "Sown Seeds", "Starbone", "Supercool Starchart", "Swindle", "Time Trick", "Trail of Evidence", "Arise!", "Call the Wild", "Dragon's Clutch", "Fae Aid", "Flash of Brilliance", "Formal Invitation", "Joy Unending", "Lure of the Depths", "Mobilize", "Pilfered Goods", "Poro Snax", "Sap Magic", "Stalking Shadows", "Starlit Epiphany", "Unraveled Earth", "Vision", "Barbed Chain", "Encroaching Shadows", "Lost Riches", "Risen Mists", "Salvage", "Sneezy Biggledust!", "Stand Alone", "The Unending Wave", "Whispered Words", "Winter's Touch", "Catalyst of Aeons", "Deep Meditation", "Drum Solo", "Eye of Nagakabouros", "Gift of the Hearthblood",  "Glory's Call", "Mimic", "Nine Lives", "Place Your Bets", "Portalpalooza", "Rejuvenating Breeze", "The Time Has Come", "The Unforgiving Cold", "Aurora Porealis", "Celestial Trifecta", "Formula", "Hextech Anomaly", "Hidden Pathways", "Sands of Time", "Shaman's Call", "Eclectic Collection", "Servitude of Desolation", "Spirit Fire", "Sputtering Songspinner", "Progress Day!", "Voices of the Old Ones"]
        self.format = format
        self.all_cards_with_localization: Dict[str, List[CardData]] = {language: [] for language in LANGUAGES.values()}
        self.collectible_cards_with_localization: Dict[str, List[CardData]] = {language: [] for language in LANGUAGES.values()}
        self.uncollectible_cards_with_localization: Dict[str, List[CardData]] = {language: [] for language in LANGUAGES.values()}
        self.collectible_cards: List[CardData] = []
        self.uncollectible_cards: List[CardData] = []
        self.all_champions: List[CardData] = []
        self.runeterra_champions: List[CardData] = []
        self.non_runeterra_champions: List[CardData] = []
        self.all_non_champions: List[CardData] = []
        # RUNETERRA CHAMPS
        self.aatrox_followers: List[CardData] = []
        self.bard_followers: List[CardData] = []
        self.elder_dragon_followers: List[CardData] = []
        self.evelynn_followers: List[CardData] = []
        self.jax_followers: List[CardData] = []
        self.jhin_followers: List[CardData] = []
        self.kayn_and_varus_followers: List[CardData] = []
        self.neeko_followers: List[CardData] = []
        self.ryze_followers: List[CardData] = []
        self.the_poro_king_followers: List[CardData] = []
        self.RUNETERRA_CHAMPIONS_NAMES_FOLLOWER_LIST_DICT: Dict[str, List[CardData]] = {
            "Aatrox": self.aatrox_followers,
            "Bard": self.bard_followers,
            "Elder Dragon": self.elder_dragon_followers,
            "Evelynn": self.evelynn_followers,
            "Jax": self.jax_followers,
            "Jhin": self.jhin_followers,
            "Kayn": self.kayn_and_varus_followers,
            "Neeko": self.neeko_followers,
            "Ryze": self.ryze_followers,
            "The Poro King": self.the_poro_king_followers,
            "Varus": self.kayn_and_varus_followers
        }

        logger.debug(f"Initializing CardPool for format {self.format}")
        # get all cards in all languages
        for language in self.all_cards_with_localization.keys():
            for card_set in CARD_SETS:
                r = requests.get(f"https://dd.b.pvp.net/latest/{card_set}/{language}/data/{card_set}-{language}.json")
                if r.status_code == 200:
                    card_set_json = json.loads(r.content)
                    for card in card_set_json:
                        card_data = CardData(card)
                        if self.format in card_data.format_refs:
                            self.all_cards_with_localization[language].append(CardData(card))
                else:
                    raise ConnectionError(f"Getting card set for {card_set} failed - Status Code: {r.status_code}")
            
            logger.debug(f"CardPool for locale {language} initialized with {len(self.all_cards_with_localization[language])} total cards")

        # divide all cards in all languages into collectible and uncollectible cards
        for language, cards in self.all_cards_with_localization.items():
            for card in cards:
                if card.is_collectible:
                    self.collectible_cards_with_localization[language].append(card)
                else:
                    self.uncollectible_cards_with_localization[language].append(card)

        # categorize cards
        for card in self.all_cards_with_localization[DEFAULT_LOCALE]:
            if card.is_collectible:
                self.collectible_cards.append(card)
                if card.is_champion:
                    self.all_champions.append(card)
                    if "Runeterra" in card.region_refs:
                        self.runeterra_champions.append(card)
                    else:
                        self.non_runeterra_champions.append(card)
                else:
                    self.all_non_champions.append(card)
            else:
                self.uncollectible_cards.append(card)
        logger.debug(f"CardPool initialized with {len(self.collectible_cards)} collectible cards")
        logger.debug(f"CardPool initialized with {len(self.uncollectible_cards)} uncollectible cards")
        logger.debug(f"CardPool initialized with {len(self.all_champions)} champion cards")
        logger.debug(f"CardPool initialized with {len(self.runeterra_champions)} runeterra champion cards")
        logger.debug(f"CardPool initialized with {len(self.non_runeterra_champions)} non runeterra champion cards")
        logger.debug(f"CardPool initialized with {len(self.all_non_champions)} non champion cards")

        # get followers of runeterra champions
        # Aatrox
        for non_champion in self.all_non_champions:
            if "DARKIN" in non_champion.subtypes:
                self.aatrox_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.aatrox_followers)} Cards for Aatrox")

        # Bard
        for non_champion in self.all_non_champions:
            # "06RU001T3" is the Chime Card
            CHIME_CARD_CARD_CODE = "06RU001T3"
            if CHIME_CARD_CARD_CODE in non_champion.associated_card_refs or non_champion.name == "Mister Thrift":
                self.bard_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.bard_followers)} Cards for Bard")

        # Elder Dragon
        for non_champion in self.all_non_champions:
            if non_champion.card_type == "Unit" and non_champion.cost >= 6:
                self.elder_dragon_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.elder_dragon_followers)} Cards for the Elder Dragon")

        # Evelynn
        for non_champion in self.all_non_champions:
            if "Husk" in non_champion.description_raw:
                self.evelynn_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.evelynn_followers)} Cards for Evelynn")

        # Jax
        for non_champion in self.all_non_champions:
            if "WEAPONMASTER" in non_champion.subtypes:
                self.jax_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.jax_followers)} Cards for Jax")

        # Jhin
        for non_champion in self.all_non_champions:
            for associated_card in non_champion.associated_card_refs:
                for uncollectible_card in self.uncollectible_cards:
                    if uncollectible_card.card_code == associated_card:
                        if "Skill" in uncollectible_card.keyword_refs:
                            self.jhin_followers.append(non_champion)
                            break
        logger.debug(f"CardPool initialized with {len(self.jhin_followers)} Cards for Jhin")

        # Kayn and Varus
        for non_champion in self.all_non_champions:
            if "CULTIST" in non_champion.subtypes:
                self.kayn_and_varus_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.kayn_and_varus_followers)} Cards for Kayn and Varus")

        # Neeko
        neeko_follower_subtypes = ["BIRD", "CAT", "DOG", "ELNUK", "FAE", "REPTILE", "SPIDER"]
        for non_champion in self.all_non_champions:
            for subtype in non_champion.subtypes:
                if subtype in neeko_follower_subtypes:
                    self.neeko_followers.append(non_champion)
                    break
        logger.debug(f"CardPool initialized with {len(self.neeko_followers)} Cards for Neeko")

        # Ryze
        for non_champion in self.all_non_champions:
            if non_champion.name in RYZE_FOLLOWER_NAMES:
                self.ryze_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.ryze_followers)} Cards for Ryze")

        # The Poro King
        for non_champion in self.all_non_champions:
            if "PORO" in non_champion.subtypes or "poro" in non_champion.description_raw.lower():
                self.the_poro_king_followers.append(non_champion)
        logger.debug(f"CardPool initialized with {len(self.the_poro_king_followers)} Cards for The Poro King")

    def get_card_by_card_code(self, card_code: str, language: str = "en_us") -> CardData:
        for card in self.all_cards_with_localization[language]:
            if card.card_code == card_code:
                return card
        raise ValueError(f"No Card with card code {card_code} found")
    
    def get_card_by_card_name(self, card_name: str, language: str = "en_us") -> CardData:
        for card in self.all_cards_with_localization[language]:
            if card_name.lower() == card.name.lower():
                return card
        for card in self.all_cards_with_localization[language]:
            if card_name.lower() in card.name.lower():
                return card
        if language != DEFAULT_LOCALE:
            return self.get_card_by_card_name(card_name=card_name, language=DEFAULT_LOCALE)
        raise ValueError(f"No Card with card name {card_name} found")
    
    def get_collectible_card_by_card_name(self, card_name: str, language: str = "en_us") -> CardData:
        for card in self.collectible_cards_with_localization[language]:
            if card_name.lower() == card.name.lower():
                return card
        for card in self.collectible_cards_with_localization[language]:
            if card_name.lower() in card.name.lower():
                return card
        if language != DEFAULT_LOCALE:
            return self.get_collectible_card_by_card_name(card_name=card_name, language=DEFAULT_LOCALE)
        raise ValueError(f"No Card with card name {card_name} found")

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
        filename = "card_names.txt"
        with open(filename, "w") as file:
            file.write(str(sorted(card_names_formatted)))
