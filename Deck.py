from typing import DefaultDict
from collections import defaultdict
from CardPool import CardPool
import lor_deckcodes
from typing import List, Dict
from CardData import CardData


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

    def sort_deck_by_cost(self) -> List[CardData]:
        deck_with_card_data: List[CardData] = []
        for card_code in self.cards_and_counts.keys():
            if self.cards_and_counts[card_code] > 0:
                card_data = self.card_pool.get_card_by_card_code(card_code=card_code)
                deck_with_card_data.append(card_data)
        sorted_deck = sorted(deck_with_card_data, key=lambda x:x.cost)
        return sorted_deck
    
    def sort_deck_by_card_type(self) -> Dict[str, str]:
        sorted_deck = self.sort_deck_by_cost()
        deck_by_card_type = {
            "champions": "",
            "non_champions": "",
            "spells": "",
            "other": ""
        }
        for card in sorted_deck:
            card_representation = f"{self.cards_and_counts[card.card_code]}x {card.name}"
            if card.is_champion:
                deck_by_card_type["champions"] += card_representation + "\n"
            elif card.card_type == "Unit" and not card.is_champion:
                deck_by_card_type["non_champions"] += card_representation + "\n"
            elif card.card_type == "Spell":
                deck_by_card_type["spells"] += card_representation + "\n"
            else:
                deck_by_card_type["other"] += card_representation + "\n"
        return deck_by_card_type
