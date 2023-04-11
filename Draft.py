from CardPool import CardPool
from typing import Dict, List, Literal
import discord
from Deck import Deck
from discord_images import assemble_deck_embed
import random
import numpy as np
from CardData import ALL_REGIONS

REACTIONS_NUMBERS = {
    "0️⃣": 0,
    "1️⃣": 1,
    "2️⃣": 2,
    "3️⃣": 3,
    "4️⃣": 4,
    "5️⃣": 5,
    "6️⃣": 6,
    "7️⃣": 7,
    "8️⃣": 8,
    "9️⃣": 9
}

NUMBERS_REACTIONS = { value: key for key, value in REACTIONS_NUMBERS.items() }

class Draft:
    def __init__(self, draft_init_message_content: str, draft_message: discord.Message, discord_bot_user: discord.User, user: discord.User, card_pool: CardPool, amount_regions: int, region_offers_per_pick: int, regions_to_choose_per_pick: int, regions_and_weights: Dict[str, int], amount_cards: int, card_offers_per_pick: int, cards_to_choose_per_pick: int, cards_and_weights: Dict[str, int], max_amount_champions: int, draft_champions_first: bool) -> None:
        self.draft_init_message_content = draft_init_message_content
        self.draft_message = draft_message
        self.discord_bot_user = discord_bot_user
        self.user = user
        self.card_pool = card_pool
        self.amount_regions = amount_regions
        self.picked_regions: List[str] = []
        self.region_offers_per_pick = region_offers_per_pick
        self.regions_to_choose_per_pick = regions_to_choose_per_pick
        self.regions_and_weights = regions_and_weights
        self.card_offers_per_pick = card_offers_per_pick
        self.cards_to_choose_per_pick = cards_to_choose_per_pick
        self.champions_to_choose_per_pick = cards_to_choose_per_pick
        self.non_champions_to_choose_per_pick = cards_to_choose_per_pick
        self.cards_and_weights = cards_and_weights
        # Used for the region rolls
        self.cards_and_weights_runeterra_champions: Dict[str, int] = {}
        # These weights are used for the rolls, when picking cards, and populated by using the picked regions -- which list is used depends on draft champions first
        self.cards_and_weights_champions: Dict[str, int] = {}
        self.cards_and_weights_non_champions: Dict[str, int] = {}
        self.cards_and_weights_champions_and_non_champions_combined: Dict[str, int] = {}
        for card in self.card_pool.runeterra_champions:
            self.cards_and_weights_runeterra_champions[card.name] = self.cards_and_weights[card.card_code]
        self.draft_champions_first = draft_champions_first
        self.drafted_deck = Deck(card_pool=self.card_pool)
        self.drafted_deck.max_cards = amount_cards
        self.drafted_deck.max_champions = max_amount_champions
        self.current_choices: List[str] = []
        self.current_reactions: List[discord.Reaction] = []
        self.status: Literal["Init", "Picking Regions", "Picking Champions", "Picking Non-Champions", "Picking Champions and Non Champions together", "Draft Completed"] = "Init"
        self.user_task: str = ""
        self.deck_embed: discord.Embed = None
        self.maximum_offers = max(region_offers_per_pick, card_offers_per_pick)

    async def _update_deck_embed(self) -> None:
        self.deck_embed = assemble_deck_embed(card_pool=self.card_pool, deckcode=self.drafted_deck.deckcode, language="en_us")

    async def update_draft_message(self) -> None:
        current_choices_message = ""
        for index, current_choice in enumerate(self.current_choices):
            current_choices_message += f"{NUMBERS_REACTIONS[index]} {current_choice}\n"
        message = f"""
{self.draft_init_message_content}
Picked Regions: {self.picked_regions}
{self.status}
{self.user_task}

{current_choices_message}
        """
        await self.draft_message.edit(content=message, embed=self.deck_embed)

    async def abandon(self) -> None:
        await self.draft_message.edit(content="Draft abandoned!", embed=self.deck_embed)
        await self._remove_own_reactions()

    async def start_draft(self) -> None:
        self.status = "Picking Regions"
        await self._roll_choices()
        await self._add_reactions()
        await self.update_draft_message()

    async def user_adds_reaction(self, reaction: discord.Reaction) -> bool: 
        self.current_reactions.append(reaction)
        if self.status == "Picking Regions":
            if len(self.current_reactions) == self.regions_to_choose_per_pick:
                await self._add_chosen_regions()
                if len(self.picked_regions) == self.amount_regions:
                    await self._prepare_card_weights()
                    if self.draft_champions_first:
                        self.status = "Picking Champions"
                    else:
                        self.status = "Picking Champions and Non Champions together"
                await self._prepare_next_choices()
        elif self.status == "Picking Champions":
            if len(self.current_reactions) == self.champions_to_choose_per_pick:
                await self._add_chosen_cards()
                if self.drafted_deck.remaining_champions == 0:
                    self.status = "Picking Non-Champions"
                await self._prepare_next_choices()
        elif self.status == "Picking Non-Champions":
            if len(self.current_reactions) == self.non_champions_to_choose_per_pick:
                await self._add_chosen_cards()
                if self.drafted_deck.remaining_cards == 0:
                    self.status = "Draft Completed"
                    await self._finish_draft()
                    return True
                await self._prepare_next_choices()
        elif self.status == "Picking Champions and Non Champions together":
            if len(self.current_reactions) == self.cards_to_choose_per_pick:
                await self._add_chosen_cards()
                if self.drafted_deck.remaining_cards == 0:
                    self.status = "Draft Completed"
                    await self._finish_draft()
                    return True
                await self._prepare_next_choices()
        return False
    
    async def _prepare_next_choices(self) -> None:
        await self._roll_choices()
        await self._remove_user_reactions()
        await self.update_draft_message()

    async def _roll_choices(self) -> None:
        if self.status == "Picking Regions":
            await self._roll_region_choices()
        elif self.status == "Picking Champions":
            await self._roll_champion_choices()
        elif self.status == "Picking Non-Champions":
            await self._roll_non_champion_choices()
        elif self.status == "Picking Champions and Non Champions together":
            await self._roll_champion_and_non_champion_choices_together()

    async def _roll_region_choices(self) -> None:
        if self.amount_regions < len(self.picked_regions) + self.regions_to_choose_per_pick:
            self.regions_to_choose_per_pick = self.amount_regions - len(self.picked_regions)
        # exclude Runeterra, if no more free champ slot
        if self.drafted_deck.remaining_champions == 0:
            self.regions_and_weights["Runeterra"] = 0
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.regions_and_weights.values())
        for key, value in self.regions_and_weights.items():
            self.regions_and_weights[key] = value / total_weight
        self.current_choices = np.random.choice(a=list(self.regions_and_weights.keys()), size=self.region_offers_per_pick, replace=False, p=list(self.regions_and_weights.values()))
        if "Runeterra" in self.current_choices:
            rolled_runeterra_champion = random.choices(list(self.cards_and_weights_runeterra_champions.keys()), weights=list(self.cards_and_weights_runeterra_champions.values()))[0]
            self.current_choices = [rolled_runeterra_champion if choice == "Runeterra" else choice for choice in self.current_choices]
        self.user_task = f"Pick {self.regions_to_choose_per_pick} Region(s) by reacting"

    async def _add_chosen_regions(self) -> None:
        for reaction in self.current_reactions:
            picked_region = self.current_choices[REACTIONS_NUMBERS[reaction.emoji]]
            self.picked_regions.append(picked_region)
            if picked_region in ALL_REGIONS:
                self.regions_and_weights[picked_region] = 0
            else:
                runeterra_champion = self.card_pool.get_card_by_card_name(picked_region)
                self.drafted_deck.add_card_and_count(runeterra_champion.card_code, 1)
                self.cards_and_weights_runeterra_champions[picked_region] = 0
                await self._update_deck_embed()

    async def _prepare_card_weights(self) -> None:
        for region in self.picked_regions:
            if region in ALL_REGIONS:
                for champion in self.card_pool.non_runeterra_champions:
                    if region in champion.region_refs:
                        self.cards_and_weights_champions[champion.name] = self.cards_and_weights[champion.card_code]
                for non_champion in self.card_pool.all_non_champions:
                    if region in non_champion.region_refs:
                        self.cards_and_weights_non_champions[non_champion.name] = self.cards_and_weights[champion.card_code]

            else:
                runeterra_champion = self.card_pool.get_card_by_card_name(region)
                self.cards_and_weights_champions[runeterra_champion.name] = self.cards_and_weights[runeterra_champion.card_code]
                for non_champion in self.card_pool.RUNETERRA_CHAMPIONS_NAMES_FOLLOWER_LIST_DICT[runeterra_champion.name]:
                    self.cards_and_weights_non_champions[non_champion.name] = self.cards_and_weights[non_champion.card_code]

        for card_name, weight in self.cards_and_weights_champions.items():
            self.cards_and_weights_champions_and_non_champions_combined[card_name] = weight
        for card_name, weight in self.cards_and_weights_non_champions.items():
            self.cards_and_weights_champions_and_non_champions_combined[card_name] = weight

    async def _roll_champion_choices(self) -> None:
        if self.drafted_deck.remaining_champions < self.champions_to_choose_per_pick:
            self.champions_to_choose_per_pick = self.drafted_deck.remaining_champions
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_champions.values())
        for key, value in self.cards_and_weights_champions.items():
            self.cards_and_weights_champions[key] = value / total_weight
        self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions.values()))
        self.user_task = f"Pick {self.champions_to_choose_per_pick} Champion(s) by reacting"

    async def _roll_non_champion_choices(self) -> None:
        if self.drafted_deck.remaining_cards < self.non_champions_to_choose_per_pick:
            self.non_champions_to_choose_per_pick = self.drafted_deck.remaining_cards
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_non_champions.values())
        for key, value in self.cards_and_weights_non_champions.items():
            self.cards_and_weights_non_champions[key] = value / total_weight
        self.current_choices = np.random.choice(a=list(self.cards_and_weights_non_champions.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_non_champions.values()))
        self.user_task = f"Pick {self.non_champions_to_choose_per_pick} Non-Champion(s) by reacting"

    async def _roll_champion_and_non_champion_choices_together(self) -> None:
        if self.drafted_deck.remaining_cards < self.cards_to_choose_per_pick:
            self.cards_to_choose_per_pick = self.drafted_deck.remaining_cards
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_champions_and_non_champions_combined.values())
        for key, value in self.cards_and_weights_champions_and_non_champions_combined.items():
            self.cards_and_weights_champions_and_non_champions_combined[key] = value / total_weight
        if self.drafted_deck.remaining_champions > self.cards_to_choose_per_pick:
            self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions_and_non_champions_combined.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions_and_non_champions_combined.values()))
        # Prevent the possibility to add more champions than intended
        else:
            for _ in range(1000):
                self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions_and_non_champions_combined.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions_and_non_champions_combined.values()))
                amount_rolled_champions = 0
                for card_name in self.current_choices:
                    card = self.card_pool.get_card_by_card_name(card_name)
                    if card.is_champion:
                        amount_rolled_champions += 1
                if amount_rolled_champions <= self.drafted_deck.remaining_champions:
                    break
        self.user_task = f"Pick {self.non_champions_to_choose_per_pick} Card(s) by reacting"

    async def _add_chosen_cards(self) -> None:
        for reaction in self.current_reactions:
            picked_card_name = self.current_choices[REACTIONS_NUMBERS[reaction.emoji]]         
            card = self.card_pool.get_card_by_card_name(picked_card_name)
            self.drafted_deck.add_card_and_count(card.card_code, 1)
            if self.drafted_deck.cards_and_counts[card.card_code] == 3:
                self.cards_and_weights_champions[picked_card_name] = 0
        await self._update_deck_embed()

    async def _finish_draft(self) -> None:
        self.user_task = ""
        self.current_choices = []
        await self._remove_user_reactions()
        await self._remove_own_reactions()
        await self.update_draft_message()

    async def _add_reactions(self) -> None:
        for number in range(self.maximum_offers):
            await self.draft_message.add_reaction(NUMBERS_REACTIONS[number])

    async def _remove_own_reactions(self) -> None:
        for number in reversed(range(self.maximum_offers)):
            await self.draft_message.remove_reaction(NUMBERS_REACTIONS[number], self.discord_bot_user)

    async def _remove_user_reactions(self) -> None:
        for reaction in reversed(self.current_reactions):
            await reaction.remove(user=self.user)
