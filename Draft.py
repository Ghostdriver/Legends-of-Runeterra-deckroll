from CardData import CardData
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
    def __init__(self, draft_init_message_content: str, draft_message: discord.Message, discord_bot_user: discord.User, user: discord.User, card_pool: CardPool, amount_regions: int, max_runeterra_regions: int, region_offers_per_pick: int, regions_to_choose_per_pick: int, regions_and_weights: Dict[str, int], amount_cards: int, card_offers_per_pick: int, cards_to_choose_per_pick: int, card_bucket_size: int, cards_and_weights: Dict[CardData, int], max_amount_champions: int, max_copies_per_card: int, draft_champions_first: bool) -> None:
        self.draft_init_message_content = draft_init_message_content
        self.draft_message = draft_message
        self.discord_bot_user = discord_bot_user
        self.user = user
        self.card_pool = card_pool
        self.amount_regions = amount_regions
        self.runeterra_regions: int = 0
        self.max_runeterra_regions = max_runeterra_regions
        self.picked_regions: List[str] = []
        self.region_offers_per_pick = region_offers_per_pick
        self.regions_to_choose_per_pick = regions_to_choose_per_pick
        self.regions_and_weights = regions_and_weights
        self.card_offers_per_pick = card_offers_per_pick
        self.champion_offers_per_pick = card_offers_per_pick
        self.non_champion_offers_per_pick = card_offers_per_pick
        self.cards_to_choose_per_pick = cards_to_choose_per_pick
        self.champions_to_choose_per_pick = cards_to_choose_per_pick
        self.non_champions_to_choose_per_pick = cards_to_choose_per_pick
        self.card_bucket_size = card_bucket_size
        self.champion_bucket_size = card_bucket_size
        self.non_champion_bucket_size = card_bucket_size
        self.cards_and_weights = cards_and_weights
        self.max_copies_per_card = max_copies_per_card
        # Used for the region rolls
        self.cards_and_weights_runeterra_champions: Dict[str, int] = {}
        # These weights are used for the rolls, when picking cards, and populated by using the picked regions -- which list is used depends on draft champions first
        self.cards_and_weights_champions: Dict[str, int] = {}
        self.cards_and_weights_non_champions: Dict[str, int] = {}
        self.cards_and_weights_champions_and_non_champions_combined: Dict[str, int] = {}
        for card in self.card_pool.runeterra_champions:
            self.cards_and_weights_runeterra_champions[card.name] = self.cards_and_weights[card]
        self.draft_champions_first = draft_champions_first
        self.drafted_deck = Deck(card_pool=self.card_pool)
        self.drafted_deck.max_cards = amount_cards
        self.drafted_deck.max_champions = max_amount_champions
        self.current_choices: List[str] | List[List[str]] = []
        self.current_reactions: List[discord.Reaction] = []
        self.status: Literal["Init", "Picking Regions", "Picking Champions", "Picking Non-Champions", "Picking Champions and Non Champions together", "Draft Completed", "!!! Draft abandoned !!!", "!!! Error !!!"] = "Init"
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
{self.user.name}'s draft
{self.draft_init_message_content}
Picked Regions: {self.picked_regions}
Cards drafted: {self.drafted_deck.amount_cards}/{self.drafted_deck.max_cards}
{self.status}
{self.user_task}

{current_choices_message}
        """
        try:
            await self.draft_message.edit(content=message, embed=self.deck_embed)
        except discord.errors.HTTPException as e:
            DECKLINK_PREFIX: str = "https://runeterra.ar/decks/code/"
            deck_url = f"{DECKLINK_PREFIX}{self.drafted_deck.deckcode}"
            await self._remove_user_reactions()
            await self._remove_own_reactions()
            self.deck_embed = discord.Embed(title="Decklink runeterra.ar", url=deck_url)
            self.status = "!!! Error !!!"
            self.user_task = "The deck embed has exceeded the maximum size allowed in Discord!\nYou still have to abandon the draft to start a new one!"
            message = f"""
{self.user.name}'s draft
{self.draft_init_message_content}
Picked Regions: {self.picked_regions}
Cards drafted: {self.drafted_deck.amount_cards}/{self.drafted_deck.max_cards}
{self.status}
{self.user_task}

{current_choices_message}
        """

    async def abandon(self) -> None:
        if self.status != "!!! Error !!!":
            self.status = "!!! Draft abandoned !!!"
        try:
            await self.update_draft_message()
        except discord.errors.HTTPException as e:
            print(e)
        await self._remove_user_reactions()
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
        if self.drafted_deck.remaining_champions == 0 or self.runeterra_regions == self.max_runeterra_regions:
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
                self.runeterra_regions += 1
                runeterra_champion = self.card_pool.get_collectible_card_by_card_name(picked_region)
                self.drafted_deck.add_card_and_count(runeterra_champion.card_code, 1)
                self.cards_and_weights_runeterra_champions[picked_region] = 0
                await self._update_deck_embed()

    async def _prepare_card_weights(self) -> None:
        for region in self.picked_regions:
            if region in ALL_REGIONS:
                for champion in self.card_pool.non_runeterra_champions:
                    if region in champion.region_refs and self.cards_and_weights[champion] > 0:
                        self.cards_and_weights_champions[champion.name] = self.cards_and_weights[champion]
                for non_champion in self.card_pool.all_non_champions:
                    if region in non_champion.region_refs and self.cards_and_weights[non_champion] > 0:
                        self.cards_and_weights_non_champions[non_champion.name] = self.cards_and_weights[champion]

            else:
                runeterra_champion = self.card_pool.get_collectible_card_by_card_name(region)
                if self.cards_and_weights[runeterra_champion] > 0 and self.max_copies_per_card > 1:
                    self.cards_and_weights_champions[runeterra_champion.name] = self.cards_and_weights[runeterra_champion]
                for non_champion in self.card_pool.RUNETERRA_CHAMPIONS_NAMES_FOLLOWER_LIST_DICT[runeterra_champion.name]:
                    if self.cards_and_weights[non_champion] > 0:
                        self.cards_and_weights_non_champions[non_champion.name] = self.cards_and_weights[non_champion]

        for card_name, weight in self.cards_and_weights_champions.items():
            self.cards_and_weights_champions_and_non_champions_combined[card_name] = weight
        for card_name, weight in self.cards_and_weights_non_champions.items():
            self.cards_and_weights_champions_and_non_champions_combined[card_name] = weight

    async def _roll_champion_choices(self) -> None:
        amount_of_draftable_champions = len(list(self.cards_and_weights_champions.keys()))
        # for single cards
        if self.drafted_deck.remaining_champions < self.champions_to_choose_per_pick:
            self.champions_to_choose_per_pick = self.drafted_deck.remaining_champions
        if amount_of_draftable_champions < self.champion_offers_per_pick:
            self.champion_offers_per_pick = amount_of_draftable_champions
        # for card buckets
        if self.drafted_deck.remaining_champions < self.champion_bucket_size:
            self.champion_bucket_size = self.drafted_deck.remaining_champions
        if amount_of_draftable_champions < self.champion_bucket_size:
            self.champion_bucket_size = amount_of_draftable_champions
            self.champion_offers_per_pick = 1
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_champions.values())
        for key, value in self.cards_and_weights_champions.items():
            self.cards_and_weights_champions[key] = value / total_weight
        # for single cards
        if self.champion_bucket_size == 1:
            self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions.keys()), size=self.champion_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions.values()))
        # for card buckets
        else:
            self.current_choices = []
            for champion_offer_per_pick in range(self.champion_offers_per_pick):
                for _ in range(10):
                    choice = sorted(np.random.choice(a=list(self.cards_and_weights_champions.keys()), size=self.champion_bucket_size, replace=False, p=list(self.cards_and_weights_champions.values())))
                    if choice not in self.current_choices:
                        self.current_choices.append(choice)
                        break
        self.user_task = f"Pick {self.champions_to_choose_per_pick} Champion Bucket(s) by reacting"

    async def _roll_non_champion_choices(self) -> None:
        amount_of_draftable_non_champions = len(list(self.cards_and_weights_non_champions.keys()))
        # for single cards
        if self.drafted_deck.remaining_cards < self.non_champions_to_choose_per_pick:
            self.non_champions_to_choose_per_pick = self.drafted_deck.remaining_cards
        if amount_of_draftable_non_champions < self.non_champion_offers_per_pick:
            self.non_champion_offers_per_pick = amount_of_draftable_non_champions
        # for card buckets
        if self.drafted_deck.remaining_cards < self.non_champion_bucket_size:
            self.non_champion_bucket_size = self.drafted_deck.remaining_cards
        if amount_of_draftable_non_champions < self.non_champion_bucket_size:
            self.non_champion_bucket_size = amount_of_draftable_non_champions
            self.non_champion_offers_per_pick = 1
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_non_champions.values())
        for key, value in self.cards_and_weights_non_champions.items():
            self.cards_and_weights_non_champions[key] = value / total_weight
        # for single cards
        if self.non_champion_bucket_size == 1:
            self.current_choices = np.random.choice(a=list(self.cards_and_weights_non_champions.keys()), size=self.non_champion_offers_per_pick, replace=False, p=list(self.cards_and_weights_non_champions.values()))
        # for card buckets
        else:
            self.current_choices = []
            for non_champion_offer_per_pick in range(self.non_champion_offers_per_pick):
                for _ in range(10):
                    choice = sorted(np.random.choice(a=list(self.cards_and_weights_non_champions.keys()), size=self.non_champion_bucket_size, replace=False, p=list(self.cards_and_weights_non_champions.values())))
                    if choice not in self.current_choices:
                        self.current_choices.append(choice)
                        break
        self.user_task = f"Pick {self.non_champions_to_choose_per_pick} Non-Champion Bucket(s) by reacting"

    async def _roll_champion_and_non_champion_choices_together(self) -> None:
        amount_of_draftable_cards = len(list(self.cards_and_weights_champions_and_non_champions_combined.keys()))
        # for single cards
        if self.drafted_deck.remaining_cards < self.cards_to_choose_per_pick:
            self.cards_to_choose_per_pick = self.drafted_deck.remaining_cards
        if amount_of_draftable_cards < self.card_offers_per_pick:
            self.card_offers_per_pick = amount_of_draftable_cards
        # for card buckets
        if self.drafted_deck.remaining_cards < self.card_bucket_size:
            self.card_bucket_size = self.drafted_deck.remaining_cards
        if amount_of_draftable_cards < self.card_bucket_size:
            self.card_bucket_size = amount_of_draftable_cards
            self.card_offers_per_pick = 1
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights_champions_and_non_champions_combined.values())
        for key, value in self.cards_and_weights_champions_and_non_champions_combined.items():
            self.cards_and_weights_champions_and_non_champions_combined[key] = value / total_weight
        # for single cards
        if self.card_bucket_size == 1:
            if self.drafted_deck.remaining_champions > self.cards_to_choose_per_pick:
                self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions_and_non_champions_combined.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions_and_non_champions_combined.values()))
            # Prevent the possibility to add more champions than intended
            else:
                for _ in range(10):
                    self.current_choices = np.random.choice(a=list(self.cards_and_weights_champions_and_non_champions_combined.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights_champions_and_non_champions_combined.values()))
                    amount_rolled_champions = await self._get_amount_rolled_champions(self.current_choices)
                    if amount_rolled_champions <= self.drafted_deck.remaining_champions:
                        break
        # for card buckets
        else:
            self.current_choices = []
            for card_offer_per_pick in range(self.card_offers_per_pick):
                for _ in range(10):
                    choice = sorted(np.random.choice(a=list(self.cards_and_weights_champions_and_non_champions_combined.keys()), size=self.card_bucket_size, replace=False, p=list(self.cards_and_weights_champions_and_non_champions_combined.values())))
                    amount_rolled_champions = await self._get_amount_rolled_champions(choice)
                    if choice not in self.current_choices and amount_rolled_champions <= self.drafted_deck.remaining_champions:
                        self.current_choices.append(choice)
                        break
        self.user_task = f"Pick {self.cards_to_choose_per_pick} Card Bucket(s) by reacting"

    async def _get_amount_rolled_champions(self, card_name_list: List[str]) -> int:
        amount_rolled_champions = 0
        for card_name in card_name_list:
            card = self.card_pool.get_collectible_card_by_card_name(card_name)
            if card.is_champion:
                amount_rolled_champions += 1
        return amount_rolled_champions

    async def _add_chosen_cards(self) -> None:
        for reaction in self.current_reactions:
            picked_card_bucket = self.current_choices[REACTIONS_NUMBERS[reaction.emoji]]
            # If the option is a card bucket
            if isinstance(picked_card_bucket, list):
                for card_name in picked_card_bucket:
                    await self._add_chosen_card(card_name=card_name)
            # If the option is a single card
            else:
                await self._add_chosen_card(card_name=picked_card_bucket)
        await self._update_deck_embed()

    async def _add_chosen_card(self, card_name: str) -> None:
        card = self.card_pool.get_collectible_card_by_card_name(card_name)
        self.drafted_deck.add_card_and_count(card.card_code, 1)
        if self.drafted_deck.cards_and_counts[card.card_code] == self.max_copies_per_card:
            del self.cards_and_weights_champions_and_non_champions_combined[card_name]
            if card.is_champion:
                del self.cards_and_weights_champions[card_name]
            else:
                del self.cards_and_weights_non_champions[card_name]

    async def _finish_draft(self) -> None:
        self.user_task = ""
        self.current_choices = []
        await self.update_draft_message()
        await self._remove_user_reactions()
        await self._remove_own_reactions()

    async def _add_reactions(self) -> None:
        for number in range(self.maximum_offers):
            await self.draft_message.add_reaction(NUMBERS_REACTIONS[number])

    async def _remove_own_reactions(self) -> None:
        for number in reversed(range(self.maximum_offers)):
            await self.draft_message.remove_reaction(NUMBERS_REACTIONS[number], self.discord_bot_user)

    async def _remove_user_reactions(self) -> None:
        for reaction in reversed(self.current_reactions):
            await reaction.remove(user=self.user)
