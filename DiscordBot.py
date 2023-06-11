from typing import  Dict, Literal
from CardData import ALL_REGIONS, CARD_SETS, RARITIES, LANGUAGES
from CardPool import CardPool
from Deckroll import Deckroll, DECKROLL_ATTEMPTS
from Draft import Draft, REACTIONS_NUMBERS
import discord
from copy import deepcopy
import re
import random
from tenacity import RetryError
from discord_images import assemble_card_image, screenshot_deck_from_runeterrra_ar, assemble_deck_embed
import logging
import textwrap

MAX_CARD_WEIGHT_CHANGE_FACTOR = 10000
MAX_REGION_WEIGHT = 100000
MAX_CARDS = 100

# Formatter, Stream Handler, Logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ch)
logger.addHandler(fh)

class DiscordBot(discord.Client):
    def __init__(self, screenshot_prefix: str, decklink_prefix: str, deckroll_deck_prefix: str, card_pool_standard: CardPool, card_pool_eternal: CardPool, format_default: Literal["standard", "eternal"], language_default: str, amount_regions_default: int, amount_cards_default: int, amount_champions_default: int, regions_and_weights_default: Dict[str, int], cards_and_weights_standard_default: Dict[str, int], cards_and_weights_eternal_default: Dict[str, int], count_chances_default: Dict[int, int], count_chances_two_remaining_deck_slots_default: Dict[str, int], region_offers_per_pick_default: int, regions_to_choose_per_pick_default: int, card_offers_per_pick_default: int, cards_to_choose_per_pick_default: int, card_bucket_size_default: int, draft_champions_first_default: bool) -> None:
        # Prefixes
        self.screenshot_prefix = screenshot_prefix
        self.decklink_prefix = decklink_prefix
        self.deckroll_deck_prefix = deckroll_deck_prefix
        # Card Pools
        self.card_pool_standard = card_pool_standard
        self.card_pool_eternal = card_pool_eternal
        # Default values
        self.format_default = format_default
        self.language_default = language_default
        self.amount_regions_default = amount_regions_default
        self.amount_cards_default = amount_cards_default
        self.amount_champions_default = amount_champions_default
        self.regions_and_weights_default = deepcopy(regions_and_weights_default)
        self.cards_and_weights_standard_default = deepcopy(cards_and_weights_standard_default)
        self.cards_and_weights_eternal_default = deepcopy(cards_and_weights_eternal_default)
        self.count_chances_default = deepcopy(count_chances_default)
        self.count_chances_two_remaining_deck_slots_default = deepcopy(count_chances_two_remaining_deck_slots_default)
        self.region_offers_per_pick_default = region_offers_per_pick_default
        self.regions_to_choose_per_pick_default = regions_to_choose_per_pick_default
        self.card_offers_per_pick_default = card_offers_per_pick_default
        self.cards_to_choose_per_pick_default = cards_to_choose_per_pick_default
        self.card_bucket_size_default = card_bucket_size_default
        self.draft_champions_first_default = draft_champions_first_default
        # Drafts
        self.drafts: Dict[int, Draft] = {}

        # START DISCORD BOT
        with open("discord_bot_token.key") as file:
            token = file.read()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.run(token=token)

    async def on_ready(self):
        logger.info("I am ready to start rolling!")

    async def on_message(self, message: discord.Message):
        if isinstance(message.content, str):
            message_content: str = message.content.lower()
            if message_content.startswith("!deck ") or message_content.startswith("!deckroll") or message_content.startswith("!card ") or message_content.startswith("!cardroll") or message_content.startswith("!draft"):
                logger.info(f"Message from {message.author}: {message_content}")

            # DISPLAY DECK
            if message_content.startswith("!deck "):
                deckcode = ""
                language = self.language_default
                split_message = message_content.split(" ")
                if len(split_message) == 2:
                    deckcode = split_message[1]
                if len(split_message) == 3 and len(split_message[1]) == 2:
                    language = split_message[1]
                    language_found = False
                    for language_abbreviation in LANGUAGES.keys():
                        if language == language_abbreviation:
                            language=LANGUAGES[language]
                            language_found = True
                            break
                    if not language_found:
                        await message.channel.send(f"It seems, that you want to display a deck with localization, but the given language was not found. Following languages are available: {LANGUAGES.keys()}")
                    deckcode = split_message[2]
                
                embed = assemble_deck_embed(card_pool=self.card_pool_eternal, deckcode=deckcode, language=language)
                
                await message.channel.send(embed=embed)

            # SHOW CARD INFO
            elif message_content.startswith("!card "):
                language = self.language_default
                language_found = False
                split_message = message_content.split(" ")
                if len(split_message) > 2 and len(split_message[1]) == 2:
                    for language_abbreviation in LANGUAGES.keys():
                        if split_message[1] == language_abbreviation:
                            language=LANGUAGES[split_message[1]]
                            language_found = True
                            break
                if language_found:
                    card_name = " ".join(split_message[2:])
                else:
                    card_name = " ".join(split_message[1:])
                    
                embed, file = assemble_card_image(card_pool=self.card_pool_eternal, card_name=card_name, language=language)

                await message.channel.send(embed=embed, file=file)

            # DECKROLL HELP
            elif message_content == "!deckroll help":
                title = "Deckroll help"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll

                Short explanation of the deckroll functionality:
                - At first the regions are rolled
                (Runeterra is considered a region and if rolled it is replaced through a Runeterra champion later on,
                Runeterra can be rolled multiple times, but for a 2 region deck the chance is 1/10 * 1/10 = 1%)
                - the cards to roll are filtered for the rolled regions
                - then the champions and the card amount is rolled until all champion slots are used
                - then all non-champions and their amount is rolled until all total card slots are used

                For the default deckroll just use !deckroll - the default settings are:
                standard format, american english
                2 regions, 40 cards, 6 champions, chance for every region and card is equal
                card amount chances are for 1/2/3 ofs: 20%/30%/50%
                if only two champions/cards remain following count chances are used 1/2 of: 33%/67% 

                this default deckroll can be indivualized with the following modifications (combine them as you want,
                but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                - eternal for eternal format
                - lang=<language> --> lang=es
                de=German, en=English (default), es=Spanish, mx=Mexican Spanish, fr=French, it=Italian, ja=Japanese,
                ko=Korean, pl=Polish, pt=Portuguese, th=Thai, tr=Turkish, ru=Russian, zh=Chinese
                - regions=<number> --> regions=10)
                - cards=<number> --> cards=60)
                - champions=<number> --> champions=10)
                - count-chances=<number>/<number>/<number> --> count-chances=33/33/34 (1/2/3 ofs)
                - count-chances-two-remaining-deck-slots=<number>/<number> --> count-chances-two-remaining-deck-slots=50/50 (1/2 ofs)
                - change region weights (standard weight is 1) with <region-name>=<number>
                e.g. exclude region Demacia=0 // make region very very likely Runeterra=1000
                the region names, that have to be used, so the modification gets recognized are:
                BandleCity, Bilgewater, Demacia, Freljord, Ionia, Noxus, PiltoverZaun, ShadowIsles, Shurima, Targon, Runeterra
                - change card weights based on their set (standard weight is 1): <set>=<number> --> Set6cde=10
                Foundations = Set1, Rising Tides = Set2, Call of the Mountain = Set3, Empires of the Ascended = Set4,
                Beyond the Bandlewood = Set5, Worldwalker = Set6, The Darkin Saga = Set6cde, Glory In Navori = Set7
                - change card weights based on their rarity: <rarity>=<number> --> epic=10
                Rarities: common, rare, epic (champion doesn't make sense, because those are handled separate)
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await message.channel.send(embed=embed)

            # DECKROLL
            elif message_content.startswith("!deckroll"):
                format = await self._get_format(message_content=message_content)
                # card pool and card weights based on format
                if format == "standard":
                    card_pool = self.card_pool_standard
                    cards_and_weights = deepcopy(self.cards_and_weights_standard_default)
                else:
                    card_pool = self.card_pool_eternal
                    cards_and_weights = deepcopy(self.cards_and_weights_eternal_default)
                language = await self._get_language(message_content=message_content)
                amount_regions = await self._get_amount_regions(message_content=message_content, message=message, card_pool=card_pool)
                amount_cards = await self._get_amount_cards(message_content=message_content, message=message)
                amount_champions = await self._get_amount_champions(message_content=message_content, message=message, amount_cards=amount_cards)
                regions_and_weights = await self._get_regions_and_weights(message_content=message_content, message=message)
                count_chances = await self._get_count_chances(message_content=message_content, message=message)
                count_chances_two_remaining_deck_slots = await self._get_count_chances_two_remaining_deck_slots(message_content=message_content, message=message)
                        
                await self._change_card_weights_based_on_their_set(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                await self._change_card_weights_based_on_their_rarity(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)

                deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
                try:
                    deckcode = deck_roll.roll_deck()
                except RetryError as e:
                    await message.channel.send(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                    raise RetryError(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                logger.info(f"the deckroll gave: {deckcode}")

                await message.channel.send(deckcode)

                embed = assemble_deck_embed(card_pool=card_pool, deckcode=deckcode, language=language)
                
                await message.channel.send(embed=embed)
            
            # CARDROLL HELP
            elif message_content == "!cardroll help":
                title = "Cardroll help"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll

                cardroll just picks one random card from all collectible cards

                the default cardroll (!cardroll) can be indivualized with the following modifications
                (combine them as you want, but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                - eternal for eternal format
                - lang=<language> --> lang=es
                de=German, en=English (default), es=Spanish, mx=Mexican Spanish, fr=French, it=Italian, ja=Japanese,
                ko=Korean, pl=Polish, pt=Portuguese, th=Thai, tr=Turkish, ru=Russian, zh=Chinese

                - when modifying the card weights the standard weight of 1 is multiplied with the modification
                --> e.g. passing Demacia=100 and Champion=100, Garen is 10000 times as likely as non demacian, non champion cards
                
                - change card weights based on their region (standard weight is 1) with <region-name>=<number>
                e.g. exclude region Demacia=0 // make region very very likely Runeterra=10000
                the region names, that have to be used, so the modification gets recognized are:
                BandleCity, Bilgewater, Demacia, Freljord, Ionia, Noxus, PiltoverZaun, ShadowIsles, Shurima, Targon, Runeterra

                - change card weights based on their set (standard weight is 1): <set>=<number> --> Set6cde=10
                Foundations = Set1, Rising Tides = Set2, Call of the Mountain = Set3, Empires of the Ascended = Set4,
                Beyond the Bandlewood = Set5, Worldwalker = Set6, The Darkin Saga = Set6cde, Glory In Navori = Set7

                - change card weights based on their rarity: <rarity>=<number> --> epic=10
                Rarities: common, rare, epic champion
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await message.channel.send(embed=embed)
            # CARDROLLL
            elif message_content.startswith("!cardroll"):
                format = await self._get_format(message_content=message_content)
                # card pool and card weights based on format
                if format == "standard":
                    card_pool = self.card_pool_standard
                    cards_and_weights = deepcopy(self.cards_and_weights_standard_default)
                else:
                    card_pool = self.card_pool_eternal
                    cards_and_weights = deepcopy(self.cards_and_weights_eternal_default)
                language = await self._get_language(message_content=message_content)
                
                await self._change_card_weights_based_on_their_region(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                await self._change_card_weights_based_on_their_set(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                await self._change_card_weights_based_on_their_rarity(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)

                random_card_code = random.choices(list(cards_and_weights.keys()), weights=list(cards_and_weights.values()))[0]

                card = card_pool.get_card_by_card_code(card_code=random_card_code, language=language)
                random_card_name = card.name
                logger.info(f"the cardroll gave: {random_card_name}")
                
                embed, file = assemble_card_image(card_pool=card_pool, card_name=random_card_name, language=language)

                await message.channel.send(embed=embed, file=file)

            # DRAFT HELP
            elif message_content == "!draft help":
                title = "Draft help"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll

                The implemented drafting function lets you draft a deck with individual modifications with only reactions!

                the default draft (!draft) can be indivualized with the following modifications
                (combine them as you want, but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                You can use all the modifications from deckroll (except changing the language (I will work on that soon))!
                --> use "!deckroll help" to get more information
                Additionally the following modifications are possible:
                The champions are randomly in the pool with all the other cards, except when you include "draft_champions_first" in the command
                Using draft-champion-first makes it so, that the champions are drafted immediately after drafting the regions until the given amount is reached
                (remark changing the card weights for champions without draft-champions-first enabled can be considered (use champion=x to do so))

                region-offers-per-pick=x --> How many regions you want to get offered, while drafting the regions (has to be between 2 and 10)
                regions-to-choose-per-pick=x --> How many of the offered regions have to be picked with every pick

                card-offers-per-pick=x --> How many cards you want to get offered, while drafting the cards (has to be between 2 and 10)
                cards-to-choose-per-pick=x --> How many of the offered cards have to be picked with every pick

                card-bucket-size=x --> The deck is drafted from buckets with multiple cards (up to 5 for now)
                (can't be used together with cards_to_choose_per_pick (atleast for now))
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await message.channel.send(embed=embed)

            elif message_content == "!abandon draft":
                message_id_of_ongoing_draft = False
                for message_id, draft in self.drafts.items():
                    if draft.user == message.author:
                        message_id_of_ongoing_draft = message_id
                if  message_id_of_ongoing_draft:
                    await self.drafts[message_id].abandon()
                    del self.drafts[message_id]

            elif message_content.startswith("!draft"):
                user_has_ongoing_draft = False
                for draft in self.drafts.values():
                    if draft.user == message.author:
                        user_has_ongoing_draft = True
                        await message.channel.send(content=textwrap.dedent(f"""
                            You have an already ongoing draft!
                            You can go to the draft message with this link ({draft.draft_message.jump_url})
                            or abandon that draft with the command:
                            !abandon draft
                        """))
                if not user_has_ongoing_draft:
                    format = await self._get_format(message_content=message_content)
                    # card pool and card weights based on format
                    if format == "standard":
                        card_pool = self.card_pool_standard
                        cards_and_weights = deepcopy(self.cards_and_weights_standard_default)
                    else:
                        card_pool = self.card_pool_eternal
                        cards_and_weights = deepcopy(self.cards_and_weights_eternal_default)
                    language = await self._get_language(message_content=message_content)
                    amount_regions = await self._get_amount_regions(message_content=message_content, message=message, card_pool=card_pool)
                    amount_cards = await self._get_amount_cards(message_content=message_content, message=message)
                    # here max amount champions, because it can (likely) happen without the option draft_champions_first, that not a fix amount of champions is chosen
                    max_amount_champions = await self._get_amount_champions(message_content=message_content, message=message, amount_cards=amount_cards)
                    regions_and_weights = await self._get_regions_and_weights(message_content=message_content, message=message)
                    count_chances = await self._get_count_chances(message_content=message_content, message=message)
                    count_chances_two_remaining_deck_slots = await self._get_count_chances_two_remaining_deck_slots(message_content=message_content, message=message)
                            
                    await self._change_card_weights_based_on_their_set(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                    await self._change_card_weights_based_on_their_rarity(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                    
                    region_offers_per_pick = await self._get_region_offers_per_pick(message_content=message_content, message=message)
                    regions_to_choose_per_pick = await self._get_regions_to_choose_per_pick(message_content=message_content, message=message, region_offers_per_pick=region_offers_per_pick)
                    card_offers_per_pick = await self._get_card_offers_per_pick(message_content=message_content, message=message)
                    cards_to_choose_per_pick = await self._get_cards_to_choose_per_pick(message_content=message_content, message=message, card_offers_per_pick=card_offers_per_pick)
                    card_bucket_size = await self._get_card_bucket_size(message_content=message_content, message=message, cards_to_choose_per_pick=cards_to_choose_per_pick)
                    draft_champions_first = await self._get_draft_champions_first(message_content=message_content)

                    draft_message = await message.channel.send(content="Let's start drafting :)")
                    self.drafts[draft_message.id] = Draft(draft_init_message_content=message_content, draft_message=draft_message, discord_bot_user=self.user, user=message.author, card_pool=card_pool, amount_regions=amount_regions, region_offers_per_pick=region_offers_per_pick, regions_to_choose_per_pick=regions_to_choose_per_pick, regions_and_weights=regions_and_weights, amount_cards=amount_cards, card_offers_per_pick=card_offers_per_pick, cards_to_choose_per_pick=cards_to_choose_per_pick, card_bucket_size=card_bucket_size, cards_and_weights=cards_and_weights, max_amount_champions=max_amount_champions, draft_champions_first=draft_champions_first)
                    await self.drafts[draft_message.id].start_draft()

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user != self.user and reaction.emoji in REACTIONS_NUMBERS.keys() and reaction.message.id in self.drafts.keys() and user == self.drafts[reaction.message.id].user:
            # Prevents the user to add reaction, that are out of bounds for the current choices
            if REACTIONS_NUMBERS[reaction.emoji] >= len(self.drafts[reaction.message.id].current_choices):
                await reaction.remove(user)
            else:
                draft_finished = await self.drafts[reaction.message.id].user_adds_reaction(reaction=reaction)
                await self.drafts[reaction.message.id].update_draft_message()
                if draft_finished:
                    del self.drafts[reaction.message.id]
            

        # Prevents other users to add emojis and other emojis to be added to drafting messages
        elif user != self.user and reaction.message.id in self.drafts.keys():
            await reaction.remove(user)
    
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if user != self.user and reaction.emoji in REACTIONS_NUMBERS.keys() and reaction.message.id in self.drafts.keys() and user == self.drafts[reaction.message.id].user:
            if reaction in self.drafts[reaction.message.id].current_reactions:
                self.drafts[reaction.message.id].current_reactions.remove(reaction)


    async def _get_format(self, message_content: str) -> str:
        format = self.format_default
        format_regex = r".*eternal.*"
        format_regex_match = re.match(format_regex, message_content)
        if bool(format_regex_match):
            format = "eternal"
        return format

    async def _get_language(self, message_content: str) -> str:
        language = self.language_default
        language_regex = r".*lang=([a-z]{2}).*"
        language_regex_match = re.match(language_regex, message_content)
        if bool(language_regex_match):
            for language_abbreviation in LANGUAGES:
                language_match = language_regex_match.group(1)
                if language_match == language_abbreviation:
                    language = LANGUAGES[language_match]
                    break
        return language
    
    async def _get_amount_regions(self, message_content: str, message: discord.Message, card_pool: CardPool) -> int:
        amount_regions = self.amount_regions_default
        max_regions = len(ALL_REGIONS) + len(card_pool.runeterra_champions) - 1
        amount_regions_regex = r".*regions=(\d+).*"
        amount_regions_regex_match = re.match(amount_regions_regex, message_content)
        if bool(amount_regions_regex_match):
            amount_regions = int(amount_regions_regex_match.group(1))
            if amount_regions < 1:
                error = f"detected a given amount of regions of {amount_regions}, but the amount of regions can not be less than 1!"
                await message.channel.send(error)
                raise ValueError(error)
            if amount_regions > max_regions:
                error = f"detected a given amount of regions of {amount_regions}, but the amount of regions can not be greater than the amount of normal regions + runeterra champions ({max_regions})!"
                await message.channel.send(error)
                raise ValueError(error)
        return amount_regions
    
    async def _get_amount_cards(self, message_content: str, message: discord.Message) -> int:
        amount_cards = self.amount_cards_default
        amount_cards_regex = r".*cards=(\d+)(\-(\d+))?.*"
        amount_cards_regex_match = re.match(amount_cards_regex, message_content)
        if bool(amount_cards_regex_match):
            min_amount_cards = int(amount_cards_regex_match.group(1))
            max_amount_cards = int(amount_cards_regex_match.group(3)) if amount_cards_regex_match.group(3) else int(amount_cards_regex_match.group(1))
            if max_amount_cards < min_amount_cards:
                error = f"the maximum amount cards can't be smaller than the minimum amount of cards!"
                await message.channel.send(error)
                raise ValueError(error)
            if min_amount_cards < 1:
                error = f"detected a given amount of cards of {min_amount_cards}, but the amount of cards can not be less than 1!"
                await message.channel.send(error)
                raise ValueError(error)
            if max_amount_cards > MAX_CARDS:
                error = f"detected a given amount of cards of {max_amount_cards}, but the amount of cards can not be greater than {MAX_CARDS}!"
                await message.channel.send(error)
                raise ValueError(error)
            amount_cards = random.randint(min_amount_cards, max_amount_cards)
        return amount_cards
    
    async def _get_amount_champions(self, message_content: str, message: discord.Message, amount_cards: int) -> int:
        amount_champions = self.amount_champions_default
        amount_champions_regex = r".*champions=(\d+)(\-(\d+))?.*"
        amount_champions_regex_match = re.match(amount_champions_regex, message_content)
        if bool(amount_champions_regex_match):
            min_amount_champions = int(amount_champions_regex_match.group(1))
            max_amount_champions = int(amount_champions_regex_match.group(3)) if amount_champions_regex_match.group(3) else int(amount_champions_regex_match.group(1))
            if max_amount_champions < min_amount_champions:
                error = f"the maximum amount champions can't be smaller than the minimum amount of champions!"
                await message.channel.send(error)
                raise ValueError(error)        
            amount_champions = random.randint(min_amount_champions, max_amount_champions)
            if amount_champions > amount_cards:
                amount_champions = amount_cards
        return amount_champions
    
    async def _get_count_chances(self, message_content: str, message: discord.Message) -> Dict[int, int]:
        count_chances = deepcopy(self.count_chances_default)
        count_chances_regex = r".*count-chances=(\d+)/(\d+)/(\d+).*"
        count_chances_regex_match = re.match(count_chances_regex, message_content)
        if bool(count_chances_regex_match):
            count_chances_one_ofs = int(count_chances_regex_match.group(1))
            count_chances_two_ofs = int(count_chances_regex_match.group(2))
            count_chances_three_ofs = int(count_chances_regex_match.group(3))
            count_chances = {
                1: count_chances_one_ofs,
                2: count_chances_two_ofs,
                3: count_chances_three_ofs,
            }
            if (sum(list(count_chances.values())) != 100):
                error = f"detected count-chances (1/2/3 ofs) {count_chances_one_ofs}/{count_chances_two_ofs}/{count_chances_three_ofs} -- the chances must sum up to 100!"
                await message.channel.send(error)
                raise ValueError(error)
        return count_chances
    
    async def _get_count_chances_two_remaining_deck_slots(self, message_content: str, message: discord.Message) -> Dict[int, int]:
        count_chances_two_remaining_deck_slots = deepcopy(self.count_chances_two_remaining_deck_slots_default)
        count_chances_two_remaining_deck_slots_regex = r".*count-chances-two-remaining-deck-slots=(\d+)/(\d+).*"
        count_chances_two_remaining_deck_slots_regex_match = re.match(count_chances_two_remaining_deck_slots_regex, message_content)
        if bool(count_chances_two_remaining_deck_slots_regex_match):
            count_chances_two_remaining_deck_slots_one_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(1))
            count_chances_two_remaining_deck_slots_two_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(2))
            count_chances_two_remaining_deck_slots = {
                1: count_chances_two_remaining_deck_slots_one_ofs,
                2: count_chances_two_remaining_deck_slots_two_ofs,
            }
            if (sum(list(count_chances_two_remaining_deck_slots.values())) != 100):
                error = f"detected count-chances-two-remaining-deck-slots (1/2 ofs) {count_chances_two_remaining_deck_slots_one_ofs}/{count_chances_two_remaining_deck_slots_two_ofs} -- the chances must sum up to 100!"
                await message.channel.send(error)
                raise ValueError(error)
        return count_chances_two_remaining_deck_slots
    
    async def _get_regions_and_weights(self, message_content: str, message: discord.Message) -> Dict[str, int]:
        regions_and_weights = deepcopy(self.regions_and_weights_default)
        for region_name in ALL_REGIONS:   
            region_weight_change_regex = rf".*{region_name.lower()}=(\d+).*"
            region_weight_change_regex_match = re.match(region_weight_change_regex, message_content)
            if bool(region_weight_change_regex_match):
                region_weight_change = int(region_weight_change_regex_match.group(1))
                regions_and_weights[region_name] = region_weight_change
                if region_weight_change > MAX_REGION_WEIGHT:
                    error = f"detected region weight change for region {region_name} with the value {region_weight_change} - only values between 0 and {MAX_REGION_WEIGHT} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
        return regions_and_weights
    
    # cardroll exclusive -- for deckroll and drafting the chances to get a region are adapted 
    async def _change_card_weights_based_on_their_region(self, message_content: str, message: discord.Message, cards_and_weights: Dict[str, int], card_pool: CardPool) -> None:
        for region_name in ALL_REGIONS:   
            card_weight_change_regex = rf".*{region_name.lower()}=(\d+).*"
            card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
            if bool(card_weight_change_regex_match):
                card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                    error = f"detected card weight change for region {region_name} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
                for collectible_card in card_pool.collectible_cards:
                    card_region_refs_lower = [card_region_ref.lower() for card_region_ref in collectible_card.region_refs]
                    if region_name.lower() in card_region_refs_lower:
                        cards_and_weights[collectible_card.card_code] *= card_weight_change_factor

    async def _change_card_weights_based_on_their_set(self, message_content: str, message: discord.Message, cards_and_weights: Dict[str, int], card_pool: CardPool) -> None:
        for card_set in CARD_SETS:
            card_weight_change_regex = rf".*{card_set.lower()}=(\d+).*"
            card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
            if bool(card_weight_change_regex_match):
                card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                    error = f"detected card weight change for card set {card_set} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
                for collectible_card in card_pool.collectible_cards:
                    if collectible_card.card_set.lower() == card_set.lower():
                        cards_and_weights[collectible_card.card_code] *= card_weight_change_factor

    async def _change_card_weights_based_on_their_rarity(self, message_content: str, message: discord.Message, cards_and_weights: Dict[str, int], card_pool: CardPool) -> None:
        for rarity in RARITIES:
            card_weight_change_regex = rf".*{rarity.lower()}=(\d+).*"
            card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
            if bool(card_weight_change_regex_match):
                card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                    error = f"detected card weight change for rarity {rarity} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
                for collectible_card in card_pool.collectible_cards:
                    if collectible_card.rarity_ref.lower() == rarity.lower():
                        cards_and_weights[collectible_card.card_code] *= card_weight_change_factor

    # DRAFTING MODIFICATIONS
    async def _get_region_offers_per_pick(self, message_content: str, message: discord.Message) -> int:
        region_offers_per_pick = self.region_offers_per_pick_default
        region_offers_per_pick_regex = r".*region-offers-per-pick=(\d+).*"
        region_offers_per_pick_regex_match = re.match(region_offers_per_pick_regex, message_content)
        if bool(region_offers_per_pick_regex_match):
            region_offers_per_pick = int(region_offers_per_pick_regex_match.group(1))
            if region_offers_per_pick < 1 or region_offers_per_pick > 10:
                error = f"detected a given amount of region_offers_per_pick of {region_offers_per_pick}, but the amount of region_offers_per_pick has to be between 1 and 10!"
                await message.channel.send(error)
                raise ValueError(error)
        return region_offers_per_pick
    
    async def _get_regions_to_choose_per_pick(self, message_content: str, message: discord.Message, region_offers_per_pick: int) -> int:
        regions_to_choose_per_pick = self.regions_to_choose_per_pick_default
        regions_to_choose_per_pick_regex = r".*regions-to-choose-per-pick=(\d+).*"
        regions_to_choose_per_pick_regex_match = re.match(regions_to_choose_per_pick_regex, message_content)
        if bool(regions_to_choose_per_pick_regex_match):
            regions_to_choose_per_pick = int(regions_to_choose_per_pick_regex_match.group(1))
            if regions_to_choose_per_pick < 1 or regions_to_choose_per_pick > 10:
                error = f"detected a given amount of region_offers_per_pick of {regions_to_choose_per_pick}, but the amount of regions_to_choose_per_pick has to be between 1 and 10!"
                await message.channel.send(error)
                raise ValueError(error)
            if regions_to_choose_per_pick > region_offers_per_pick:
                error = f"detected a given amount of region_offers_per_pick of {regions_to_choose_per_pick} and a given amount of region_offers_per_pick of {region_offers_per_pick}, but the amount of regions_to_choose_per_pick has to be smaller or equal to the amount of region_offers_per_pick"
                await message.channel.send(error)
                raise ValueError(error)
        return regions_to_choose_per_pick
    
    async def _get_card_offers_per_pick(self, message_content: str, message: discord.Message) -> int:
        card_offers_per_pick = self.card_offers_per_pick_default
        card_offers_per_pick_regex = r".*card-offers-per-pick=(\d+).*"
        card_offers_per_pick_regex_match = re.match(card_offers_per_pick_regex, message_content)
        if bool(card_offers_per_pick_regex_match):
            card_offers_per_pick = int(card_offers_per_pick_regex_match.group(1))
            if card_offers_per_pick < 2 or card_offers_per_pick > 10:
                error = f"detected a given amount of card_offers_per_pick of {card_offers_per_pick}, but the amount of card_offers_per_pick has to be between 2 and 10!"
                await message.channel.send(error)
                raise ValueError(error)
        return card_offers_per_pick
    
    async def _get_cards_to_choose_per_pick(self, message_content: str, message: discord.Message, card_offers_per_pick: int) -> int:
        cards_to_choose_per_pick = self.cards_to_choose_per_pick_default
        cards_to_choose_per_pick_regex = r".*cards-to-choose-per-pick=(\d+).*"
        cards_to_choose_per_pick_regex_match = re.match(cards_to_choose_per_pick_regex, message_content)
        if bool(cards_to_choose_per_pick_regex_match):
            cards_to_choose_per_pick = int(cards_to_choose_per_pick_regex_match.group(1))
            if cards_to_choose_per_pick < 1 or cards_to_choose_per_pick > 9:
                error = f"detected a given amount of card_offers_per_pick of {cards_to_choose_per_pick}, but the amount of cards_to_choose_per_pick has to be between 1 and 9!"
                await message.channel.send(error)
                raise ValueError(error)
            if cards_to_choose_per_pick >= card_offers_per_pick:
                error = f"detected a given amount of card_offers_per_pick of {cards_to_choose_per_pick} and a given amount of card_offers_per_pick of {card_offers_per_pick}, but the amount of cards_to_choose_per_pick has to be smaller than the amount of card_offers_per_pick"
                await message.channel.send(error)
                raise ValueError(error)
        return cards_to_choose_per_pick
    
    async def _get_card_bucket_size(self, message_content: str, message: discord.Message, cards_to_choose_per_pick: int) -> int:
        card_bucket_size = self.card_bucket_size_default
        card_bucket_size_regex = r".*card-bucket-size=(\d+).*"
        card_bucket_size_regex_match = re.match(card_bucket_size_regex, message_content)
        if bool(card_bucket_size_regex_match):
            card_bucket_size = int(card_bucket_size_regex_match.group(1))
            if card_bucket_size < 1 or card_bucket_size > 5:
                error = f"detected a given card_bucket_size of {card_bucket_size}, but the card_bucket_size has to be between 1 and 5!"
                await message.channel.send(error)
                raise ValueError(error)
            if card_bucket_size > 1 and cards_to_choose_per_pick > 1:
                error = f"Only one of card_bucket_size and cards_to_choose_per_pick can be greater than 1"
                await message.channel.send(error)
                raise ValueError(error)
        return card_bucket_size
    
    async def _get_draft_champions_first(self, message_content: str) -> bool:
        draft_champions_first = self.draft_champions_first_default
        draft_champions_first_regex = r".*draft-champions-first.*"
        draft_champions_first_regex_match = re.match(draft_champions_first_regex, message_content)
        if bool(draft_champions_first_regex_match):
            draft_champions_first = True
        return draft_champions_first
