from CardData import CardData
from CardPool import CardPool
from typing import List, Dict
import random
from Deck import Deck
import datetime
import xlsxwriter
import os
from tenacity import retry, stop_after_attempt, RetryError

DECKROLL_ATTEMPTS = 10

class Deckrolls:
    def __init__(self, amount_deck_rolls: int, disallow_duplicated_regions_and_champions: bool, card_pool: CardPool, amount_regions: int, amount_cards: int, amount_champions: int, max_runeterra_regions: int, regions_and_weights: Dict[str, int], cards_and_weights: Dict[CardData, int], count_chances: Dict[int, int], count_chances_two_remaining_deck_slots: Dict[int, int]) -> None:
        self.amount_deck_rolls = amount_deck_rolls
        self.disallow_duplicated_regions_and_champions = disallow_duplicated_regions_and_champions
        self.deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, max_runeterra_regions=max_runeterra_regions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
    
    def roll_deck_spreadsheat(self, amount_players: int, decklink_prefix: str) -> None:
        start_time = datetime.datetime.now()
        DECKROLL_PATH = "created_deckroll_excel_spreadsheats/"
        workbook_name: str = f"Deckroll-{datetime.date.today().isoformat()}.xlsx"
        with xlsxwriter.Workbook(os.path.join(DECKROLL_PATH, workbook_name)) as workbook:
            worksheet = workbook.add_worksheet("rolled decks")
            first_line = ["Player"] + ["Deck Link"] * self.amount_deck_rolls
            for column, element in enumerate(first_line):
                worksheet.write(0, column, element)
            for row in range(1, amount_players + 1):
                regions_and_weights = self.deck_roll.regions_and_weights.copy()
                cards_and_weights = self.deck_roll.cards_and_weights.copy()
                deckcodes = self.roll_decks()
                self.deck_roll.regions_and_weights = regions_and_weights
                self.deck_roll.cards_and_weights = cards_and_weights
                if isinstance(deckcodes, str):
                    deckcodes = [deckcodes]
                for index, deckcode in enumerate(deckcodes):
                    worksheet.write(row, index + 1, decklink_prefix + deckcode)
        end_time = datetime.datetime.now()
        needed_time = end_time - start_time
        print(
            f"Created Excel {workbook_name} with {amount_players * self.amount_deck_rolls} rolled decks in {needed_time}"
        )

    def roll_decks(self) -> str | List[str]:
        if self.amount_deck_rolls == 1:
            try:
                deckcode = self.deck_roll.roll_deck()
            except RetryError as e:
                raise RetryError(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
            return deckcode
        else:
            deckcodes: List[str] = []
            for _ in range(self.amount_deck_rolls):
                try:
                    deckcode = self.deck_roll.roll_deck()
                except RetryError as e:
                    raise RetryError(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                deckcodes.append(deckcode)
                if self.disallow_duplicated_regions_and_champions:
                    for region in self.deck_roll.rolled_regions:
                        self.deck_roll.regions_and_weights[region] = 0
                    for champion in self.deck_roll.deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical("Champion"):
                        self.deck_roll.cards_and_weights[champion] = 0
            return deckcodes

class Deckroll:
    def __init__(self, card_pool: CardPool, amount_regions: int, amount_cards: int, amount_champions: int, max_runeterra_regions: int, regions_and_weights: Dict[str, int], cards_and_weights: Dict[CardData, int], count_chances: Dict[int, int], count_chances_two_remaining_deck_slots: Dict[int, int]) -> None:
        self.card_pool = card_pool
        self.amount_regions = amount_regions
        self.amount_cards = amount_cards
        self.amount_champions = amount_champions
        if self.amount_champions > self.amount_cards:
            self.amount_champions = self.amount_cards
        self.max_runeterra_regions = max_runeterra_regions
        self.regions_and_weights = regions_and_weights
        self.cards_and_weights = cards_and_weights
        self.cards_and_weights_runeterra_champions: Dict[CardData, int] = {}
        for card in self.card_pool.runeterra_champions:
            self.cards_and_weights_runeterra_champions[card] = self.cards_and_weights[card]
        self.count_chances = count_chances
        self.count_chances_two_remaining_deck_slots = count_chances_two_remaining_deck_slots

    @retry(stop=stop_after_attempt(DECKROLL_ATTEMPTS))
    def roll_deck(self) -> str:
        # init Deck
        self.deck = Deck(card_pool=self.card_pool)
        self.deck.max_cards = self.amount_cards
        self.deck.max_champions = self.amount_champions
        # init new values, that only apply to this roll
        self._roll_regions()
        self._roll_runeterra_champions()
        self._roll_non_runeterra_champions()
        self._roll_non_champions()
        return self.deck.deckcode

    def _roll_regions(self) -> None:
        '''return the regionRefs of the rolled regions'''
        # deepcopy to not screw up subsequent rolls
        regions_and_weights_roll = self.regions_and_weights.copy()
        self.rolled_regions: List[str] = []
        for _ in range(self.amount_regions):
            # Prevent Runeterra from getting rolled, if not enough champions are allowed
            if self.rolled_regions.count("Runeterra") == self.amount_champions or self.rolled_regions.count("Runeterra") == self.max_runeterra_regions:
                regions_and_weights_roll["Runeterra"] = 0
            rolled_region = random.choices(list(regions_and_weights_roll.keys()), weights=list(regions_and_weights_roll.values()))[0]
            self.rolled_regions.append(rolled_region)
            # Prevent duplicated rolled region (except Runeterra can be rolled multiple times if there are enough champions allowed)
            if rolled_region != "Runeterra":
                regions_and_weights_roll[rolled_region] = 0
    
    def _roll_runeterra_champions(self) -> None:
        '''rolls the runeterra champions and count and adds them to the deck'''
        # deepcopy to not screw up subsequent rolls
        cards_and_weights_runeterra_champions_roll = self.cards_and_weights_runeterra_champions.copy()
        # roll which runeterra champions are taken and add them as 1 ofs
        self.rolled_runeterra_champions: List[CardData] = []
        for _ in range(self.rolled_regions.count("Runeterra")):
            rolled_runeterra_champion = random.choices(list(cards_and_weights_runeterra_champions_roll.keys()), weights=list(cards_and_weights_runeterra_champions_roll.values()))[0]
            self.rolled_runeterra_champions.append(rolled_runeterra_champion)
            self.deck.add_card_and_count(rolled_runeterra_champion.card_code, 1)
            cards_and_weights_runeterra_champions_roll[rolled_runeterra_champion] = 0
        # roll the amount of runeterra champions
        for rolled_runeterra_champion in self.rolled_runeterra_champions:
            self._roll_card_count(rolled_runeterra_champion)
    
    def _roll_non_runeterra_champions(self) -> None:
        '''rolls the non runeterra champions'''
        # init cards and weights rollable champs for this roll (depends on the rolled regions)
        cards_and_weights_rollable_champions_roll: Dict[CardData, int] = {}
        for rolled_region in self.rolled_regions:
            if rolled_region != "Runeterra":
                for non_runeterra_champion in self.card_pool.non_runeterra_champions:
                    if rolled_region in non_runeterra_champion.region_refs:
                        cards_and_weights_rollable_champions_roll[non_runeterra_champion] = self.cards_and_weights[non_runeterra_champion]
        # roll champions
        while self.deck.remaining_champions > 0:
            rolled_champion = random.choices(list(cards_and_weights_rollable_champions_roll.keys()), weights=list(cards_and_weights_rollable_champions_roll.values()))[0]
            self._roll_card_count(rolled_champion)
            cards_and_weights_rollable_champions_roll[rolled_champion] = 0
        
    def _roll_non_champions(self) -> None:
        '''rolls all non champions'''
        # init cards and weights rollable non champions for this roll (depends on the rolled regions)
        cards_and_weights_rollable_non_champions_roll: Dict[CardData, int] = {}
        # add non champions belonging to the rolled runeterra champions
        for rolled_runeterra_champion in self.rolled_runeterra_champions:
            for non_champion in self.card_pool.RUNETERRA_CHAMPIONS_NAMES_FOLLOWER_LIST_DICT[rolled_runeterra_champion.name]:
                cards_and_weights_rollable_non_champions_roll[non_champion] = self.cards_and_weights[non_champion]
        # add non champions from normal regions to the rollable non champions
        for rolled_region in self.rolled_regions:
            if rolled_region != "Runeterra":
                for non_champion in self.card_pool.all_non_champions:
                    if rolled_region in non_champion.region_refs:
                        cards_and_weights_rollable_non_champions_roll[non_champion] = self.cards_and_weights[non_champion]
        # roll non champions
        while self.deck.remaining_cards > 0:
            rolled_non_champion = random.choices(list(cards_and_weights_rollable_non_champions_roll.keys()), weights=list(cards_and_weights_rollable_non_champions_roll.values()))[0]
            self._roll_card_count(rolled_non_champion)
            cards_and_weights_rollable_non_champions_roll[rolled_non_champion] = 0

    def _roll_card_count(self, card: CardData) -> None:
        '''rolls the amount, how often a card is present in the deck'''
        # Calculate max rollable count
        max_rollable_count: int = 3
        if card.is_champion and self.deck.remaining_champions < 3:
            max_rollable_count = self.deck.remaining_champions
        elif self.deck.remaining_cards < 3:
            max_rollable_count = self.deck.remaining_cards
        # special case, because Runeterra champions are added as 1 ofs to make the region eligible - the one of gets removed, max rollable count adjusted and normal roll occurs
        if "Runeterra" in card.region_refs:
            self.deck.cards_and_counts[card.card_code] = 0
            if max_rollable_count < 3:
                max_rollable_count += 1
        # Roll count depending on the max rollable count and the given count chances
        if max_rollable_count == 1:
            count = 1
        elif max_rollable_count == 2:
            count = random.choices(list(self.count_chances_two_remaining_deck_slots.keys()), list(self.count_chances_two_remaining_deck_slots.values()))[0]
        else:
            count = random.choices(list(self.count_chances.keys()), list(self.count_chances.values()))[0]
        self.deck.add_card_and_count(card.card_code, count)
