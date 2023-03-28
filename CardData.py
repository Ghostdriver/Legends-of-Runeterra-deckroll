from typing import List, Dict

CARD_SETS = ["set1", "set2", "set3", "set4", "set5", "set6", "set6cde", "set7"]
CARD_TYPES_COLLECTIBLE_CARDS = ["Champion", "Equpment", "Landmark", "Spell", "Unit"]
RARITIES = ["Common", "Rare", "Epic", "Champion"]
ALL_REGIONS = ["BandleCity", "Bilgewater", "Demacia", "Freljord", "Ionia", "Noxus", "PiltoverZaun", "ShadowIsles", "Shurima", "Targon", "Runeterra"]
LANGUAGES = {
    "de": "de_de",
    "en": "en_us",
    "es": "es_es",
    "mx": "es_mx",
    "fr": "fr_fr",
    "it": "it_it",
    "ja": "ja_jp",
    "ko": "ko_kr",
    "pl": "pl_pl",
    "pt": "pt_br",
    "th": "th_th",
    "tr": "tr_tr",
    "ru": "ru_ru",
    "zh": "zh_tw"
}

class CardData:
    def __init__(self, card: Dict) -> None:
        self.associated_card_refs: List[str] = card["associatedCardRefs"]
        self.game_absolute_path = card["assets"][0]["gameAbsolutePath"]
        self.region_refs: List[str] = card["regionRefs"]
        self.attack: int = card["attack"]
        self.cost: int = card["cost"]
        self.health: int = card["health"]
        self.description: str = card["description"]
        self.description_raw: str = card["descriptionRaw"]
        self.level_up_description: str = card["levelupDescription"]
        self.level_up_description_raw: str = card["levelupDescriptionRaw"]
        self.flavor_text: str = card["flavorText"]
        self.artist_name: str = card["artistName"]
        self.name: str = card["name"]
        self.card_code: str = card["cardCode"]
        self.keyword_refs: List[str] = card["keywordRefs"]
        self.spell_speed_ref: str = card["spellSpeedRef"]
        self.rarity_ref: str = card["rarityRef"]
        self.subtypes: List[str] = card["subtypes"]
        self.supertype: str = card["supertype"]
        self.card_type: str = card["type"]
        self.is_collectible: bool = card["collectible"]
        self.card_set: str = card["set"]
        
        if card["rarityRef"] == "Champion":
            self.is_champion: bool = True
        else:
            self.is_champion: bool = False