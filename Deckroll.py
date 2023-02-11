from CardPool import CardPool
from typing import List, Dict
import random
from copy import deepcopy
from Deck import Deck
import datetime
import xlsxwriter
import os

class Deckroll:
    def __init__(self, card_pool: CardPool, amount_regions: int, amount_cards: int, amount_champs: int, regions_and_weights: Dict[str, float], cards_and_weights: Dict[str, float], count_chances: Dict[int, float], count_chances_two_remaining_deck_slots: Dict[int, float]) -> None:
        self.card_pool: CardPool = card_pool
        self.amount_regions: int = amount_regions
        self.amount_cards: int = amount_cards
        self.amount_champs: int = amount_champs
        self.regions_and_weights: Dict[str, float] = regions_and_weights
        self.cards_and_weights: Dict[str, float] = cards_and_weights
        self.cards_and_weights_runeterra_champs: Dict[str, float] = {}
        for card in self.card_pool.runeterra_champs:
            self.cards_and_weights_runeterra_champs[card.card_code] = self.cards_and_weights[card.card_code]
        self.count_chances: Dict[int, float] = count_chances
        self.count_chances_two_remaining_deck_slots: Dict[int, float] = count_chances_two_remaining_deck_slots

    def roll_deck(self) -> str:
        # init Deck
        self.deck = Deck(card_pool=self.card_pool)
        self.deck.max_cards = self.amount_cards
        self.deck.max_champs = self.amount_champs
        # init new values, that only apply to this roll
        self.roll_regions()
        self.roll_runeterra_champs()
        self.roll_non_runeterra_champs()
        self.roll_non_champs()
        return self.deck.get_deckcode()

    def roll_regions(self) -> List[str]:
        '''return the regionRefs of the rolled regions'''
        # deepcopy to not screw up subsequent rolls
        regions_and_weights_roll = deepcopy(self.regions_and_weights)
        self.rolled_regions: List[str] = []
        for _ in range(self.amount_regions):
            # Prevent Runeterra from getting rolled, if not enough champions are allowed
            if self.rolled_regions.count("Runeterra") == self.amount_champs:
                regions_and_weights_roll["Runeterra"] = 0
            rolled_region = random.choices(list(regions_and_weights_roll.keys()), weights=list(regions_and_weights_roll.values()))[0]
            self.rolled_regions.append(rolled_region)
            # Prevent duplicated rolled region (except Runeterra can be rolled multiple times if there are enough champions allowed)
            if rolled_region != "Runeterra":
                regions_and_weights_roll[rolled_region] = 0
    
    def roll_runeterra_champs(self) -> List[str]:
        '''rolls the runeterra champs and count and adds them to the deck'''
        # deepcopy to not screw up subsequent rolls
        cards_and_weights_runeterra_champs_roll = deepcopy(self.cards_and_weights_runeterra_champs)
        # roll which runeterra champions are taken and add them as 1 ofs
        self.rolled_runeterra_champs: List[str] = []
        for _ in range(self.rolled_regions.count("Runeterra")):
            rolled_runeterra_champ = random.choices(list(cards_and_weights_runeterra_champs_roll.keys()), weights=list(cards_and_weights_runeterra_champs_roll.values()))[0]
            self.rolled_runeterra_champs.append(rolled_runeterra_champ)
            self.deck.add_card_and_count(rolled_runeterra_champ, 1)
            cards_and_weights_runeterra_champs_roll[rolled_runeterra_champ] = 0
        # roll the amount of runeterra champs
        for rolled_runeterra_champ in self.rolled_runeterra_champs:
            self.roll_count(rolled_runeterra_champ)
    
    def roll_non_runeterra_champs(self) -> None:
        '''Rolls the non runeterra champions'''
        # init cards and weights rollable champs for this roll (depends on the rolled regions)
        cards_and_weights_rollable_champs_roll: Dict[str, float] = {}
        for rolled_region in self.rolled_regions:
            if rolled_region != "Runeterra":
                for non_runeterra_champ in self.card_pool.non_runeterra_champs:
                    if rolled_region in non_runeterra_champ.region_refs:
                        cards_and_weights_rollable_champs_roll[non_runeterra_champ.card_code] = self.cards_and_weights[non_runeterra_champ.card_code]
        # roll champs
        while self.deck.remaining_champs > 0:
            rolled_champ = random.choices(list(cards_and_weights_rollable_champs_roll.keys()), weights=list(cards_and_weights_rollable_champs_roll.values()))[0]
            self.roll_count(rolled_champ)
            cards_and_weights_rollable_champs_roll[rolled_champ] = 0
        
    def roll_non_champs(self) -> None:
        '''Rolls all non champions'''
        # init cards and weights rollable non champs for this roll (depends on the rolled regions)
        cards_and_weights_rollable_non_champs_roll: Dict[str, float] = {}
        # add non champs from normal regions to the rollable non champs
        for rolled_region in self.rolled_regions:
            if rolled_region != "Runeterra":
                for non_champ in self.card_pool.all_non_champs:
                    if rolled_region in non_champ.region_refs:
                        cards_and_weights_rollable_non_champs_roll[non_champ.card_code] = self.cards_and_weights[non_champ.card_code]
        # add non champs belonging to the rolled runeterra champs
        for rolled_runeterra_champ in self.rolled_runeterra_champs:
            rolled_runeterra_champ_name = self.card_pool.get_card_by_card_code(rolled_runeterra_champ).name
            for non_champ in self.card_pool.RUNETERRA_CHAMPS_NAMES_FOLLOWER_LIST_DICT[rolled_runeterra_champ_name]:
                cards_and_weights_rollable_non_champs_roll[non_champ.card_code] = self.cards_and_weights[non_champ.card_code]
        # roll non champs
        while self.deck.remaining_cards > 0:
            rolled_non_champ = random.choices(list(cards_and_weights_rollable_non_champs_roll.keys()), weights=list(cards_and_weights_rollable_non_champs_roll.values()))[0]
            self.roll_count(rolled_non_champ)
            cards_and_weights_rollable_non_champs_roll[rolled_non_champ] = 0

    def roll_count(self, card_code: str):
        '''rolls the amount, how often a card is present in the deck'''
        card = self.card_pool.get_card_by_card_code(card_code=card_code)
        # Calculate max rollable count
        max_rollable_count: int = 3
        if card.is_champ and self.deck.remaining_champs < 3:
            max_rollable_count = self.deck.remaining_champs
        elif self.deck.remaining_cards < 3:
            max_rollable_count = self.deck.remaining_cards
        # special case, because Runeterra champs are added as 1 ofs to make the region eligible - the one of gets removed, max rollable count adjusted and normal roll occurs
        if "Runeterra" in card.region_refs:
            self.deck.cards_and_counts[card.card_code] = 0
            if max_rollable_count < 3:
                max_rollable_count += 1
        # Roll count depending on the max rollable count and the given count chances
        if max_rollable_count == 1:
            count = 1
        elif max_rollable_count == 2:
            count = random.choices(
                list(self.count_chances_two_remaining_deck_slots.keys()),
                list(self.count_chances_two_remaining_deck_slots.values()),
            )[0]
        else:
            count = random.choices(
                list(self.count_chances.keys()), list(self.count_chances.values())
            )[0]
        self.deck.add_card_and_count(card.card_code, count)

    def roll_deck_spreadsheat(self, amount_decks: int, decklink_prefix: str) -> None:
        PATH: str = "created_deckroll_excel_spreadsheats/"
        start_time = datetime.datetime.now()
        workbook_name: str = f"Deckroll-{datetime.date.today().isoformat()}.xlsx"
        with xlsxwriter.Workbook(os.path.join(PATH, workbook_name)) as workbook:
            worksheet = workbook.add_worksheet("rolled decks")
            first_line = ["Player", "Deck Link", "Deck Code"]
            for column, element in enumerate(first_line):
                worksheet.write(0, column, element)
            for row in range(1, amount_decks + 1):
                deckcode = self.roll_deck()
                worksheet.write(row, 0, row)
                worksheet.write(row, 1, deckcode)
                worksheet.write(row, 2, decklink_prefix + deckcode)
        end_time = datetime.datetime.now()
        needed_time = end_time - start_time
        print(
            f"Created Excel {workbook_name} with {amount_decks} rolled decks in {needed_time}"
        )
        


            