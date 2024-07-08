from collections import defaultdict
from typing import DefaultDict, Dict, List, Literal

import lor_deckcodes

from CardData import CARD_TYPES_COLLECTIBLE_CARDS, CardData
from CardPool import CardPool


class Deck:
    def __init__(self, card_pool: CardPool) -> None:
        self.card_pool = card_pool
        self.max_cards = 40
        self.max_champions = 6
        self.cards_and_counts: DefaultDict[str, int] = defaultdict(lambda: 0)

    @property
    def amount_cards(self) -> int:
        return sum(list(self.cards_and_counts.values()))

    @property
    def remaining_cards(self) -> int:
        return self.max_cards - self.amount_cards

    @property
    def amount_champions(self) -> int:
        amount = 0
        for card in self.card_pool.all_champions:
            amount += self.cards_and_counts[card.card_code]
        return amount

    @property
    def remaining_champions(self) -> int:
        return self.max_champions - self.amount_champions

    @property
    def deckcode(self) -> str:
        deck_formatted = []
        for card_code, count in self.cards_and_counts.items():
            deck_formatted.append(f"{count}:{card_code}")
        lor_deck = lor_deckcodes.LoRDeck(deck_formatted)
        deck_code = lor_deck.encode()
        return deck_code

    @property
    def regions(self) -> List[str]:
        regions = []
        runeterra_champions: List[str] = []
        for champion in self.deck_sorted_by_card_type["Champion"]:
            if self.cards_and_counts[champion.card_code] > 0 and len(champion.region_refs) == 1:
                if champion.region_refs[0] == "Runeterra":
                    regions.append(champion.name)
                    runeterra_champions.append(champion.name)
                elif champion.region_refs[0] not in regions:
                    regions.append(champion.region_refs[0])
        for card_code in self.cards_and_counts.keys():
            for card in self.card_pool.collectible_cards:
                if card.card_code == card_code and self.cards_and_counts[card_code] > 0 and not card.is_champion and len(card.region_refs) == 1 and card.region_refs[0] not in regions:
                    card_is_a_runeterra_champion_follower = False
                    for runeterra_champion in runeterra_champions:
                        for runeterra_champion_follower in self.card_pool.RUNETERRA_CHAMPIONS_NAMES_FOLLOWER_LIST_DICT[runeterra_champion]:
                            if runeterra_champion_follower.card_code == card_code:
                                card_is_a_runeterra_champion_follower = True
                    if not card_is_a_runeterra_champion_follower:
                        regions.append(card.region_refs[0])
        return regions

    @property
    def deck_sorted_by_card_type(self) -> Dict[str, List[CardData]]:
        deck_sorted_by_card_type = {}
        for card_type in CARD_TYPES_COLLECTIBLE_CARDS:
            deck_sorted_by_card_type[card_type] = []
        for card_code in self.cards_and_counts.keys():
            for card in self.card_pool.collectible_cards:
                if card.card_code == card_code and self.cards_and_counts[card_code] > 0:
                    if card.is_champion:
                        deck_sorted_by_card_type["Champion"].append(card)
                    else:
                        deck_sorted_by_card_type[card.card_type].append(card)
        return deck_sorted_by_card_type

    def add_card_and_count(self, card_code: str, count: int) -> None:
        card = self.card_pool.get_card_by_card_code(card_code=card_code)
        if not (0 <= self.cards_and_counts[card_code] + count <= 3):
            raise ValueError("With the addition of the specified count to the card the count for this card would be out of the range 0-3")
        if self.amount_cards + count > self.max_cards:
            raise ValueError("With the addition of the card the maximum amount of cards would be exceeded")
        if card.is_champion and self.amount_champions + count > self.max_champions:
            raise ValueError("With the addition of the card the maximum amount of champions would be exceeded")
        self.cards_and_counts[card_code] += count

    def load_deck_from_deckcode(self, deckcode: str) -> None:
        self.max_cards = 100
        self.max_champions = 100
        deck = lor_deckcodes.LoRDeck.from_deckcode(deckcode)
        for card in deck:
            count, card_code = card.split(":")
            self.add_card_and_count(card_code=card_code, count=int(count))

    def get_cards_by_card_type_sorted_by_cost_and_alphabetical(self, card_type: Literal["Champion", "Equipment", "Landmark", "Spell", "Unit"]) -> List[CardData]:
        return sorted(self.deck_sorted_by_card_type[card_type], key=lambda card: (card.cost, card.name))
