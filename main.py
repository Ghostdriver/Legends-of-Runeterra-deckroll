from typing import  Dict, Literal
from CardData import ALL_REGIONS, CARD_SETS, RARITIES
from CardPool import CardPool
from Deckroll import Deckroll
import discord
from discord.ext import commands
from copy import deepcopy
import re
from tenacity import RetryError

# CARD POOL OPTIONS
# IF cards should get fetched from API (needs some time for the first run - up to a few minutes)
# CARD_SETS in CardData needs to be updated
# if cards should get read out from local files (really fast) the newest json files have to be in the local_cards_sets_folder
# those can be retrieved from https://developer.riotgames.com/docs/lor with the names "https://dd.b.pvp.net/latest/{card_set}-lite-en_us.zip"
# then just unzip those and put the {card_set}-1en_us.json in the extracted folder en_us/data into the directory
# because I haven't found a good way to get ryze associated cards, a list with all card names belonging to him has to be given (a better solution would be appreciated)
API_OR_LOCAL: Literal["API", "LOCAL"] = "API"
RYZE_FOLLOWER_NAMES = ["Feral Prescience", "Warning Shot", "Advanced Intel", "Bandle Tellstones", "Bilgewater Tellstones", "Bloodbait", "Construct of Desolation", "Demacian Tellstones", "Fae Sprout", "Heavens Aligned", "Imagined Possibilities", "Ionian Tellstones", "Jettison", "Jury-Rig", "Messenger's Sigil", "Mushroom Cloud", "Noxian Tellstones", "Piltovan Tellstones", "Ranger's Resolve", "Ransom Riches", "Sapling Toss", "Shadow Isles Tellstones", "Shroud of Darkness", "Shuriman Tellstones", "Spell Thief", "Stoneweaving", "Stress Testing", "Targonian Tellstones", "Tempting Prospect", "Three Sisters", "Trinket Trade", "Allure", "Ancestral Boon", "Behold the Infinite", "Calculated Creations", "Discreet Invitation", "Encore", "Entrapment", "Entreat", "Field Promotion", "Gifts From Beyond", "Icathian Myths", "Insight of Ages", "Line 'Em Up", "Magical Journey", "Payday", "Poro Stories", "Rite of Passage", "Shared Spoils", "Sown Seeds", "Starbone", "Supercool Starchart", "Swindle", "Time Trick", "Trail of Evidence", "Arise!", "Call the Wild", "Dragon's Clutch", "En Garde", "Fae Aid", "Flash of Brilliance", "Formal Invitation", "Lure of the Depths", "Mobilize", "Pilfered Goods", "Poro Snax", "Sap Magic", "Stalking Shadows", "Starlit Epiphany", "Unraveled Earth", "Vision", "Encroaching Shadows", "Lost Riches", "Risen Mists", "Salvage", "Sneezy Biggledust!", "Stand Alone", "The Unending Wave", "The Unforgiving Cold", "Whispered Words", "Catalyst of Aeons", "Deep Meditation", "Drum Solo", "Eye of Nagakabouros", "Gift of the Hearthblood", "Nine Lives", "Portalpalooza", "The Time Has Come", "Aurora Porealis", "Celestial Trifecta", "Glory's Call", "Hextech Anomaly", "Hidden Pathways", "Sands of Time", "Shaman's Call", "Eclectic Collection", "Servitude of Desolation", "Spirit Fire", "Sputtering Songspinner", "Progress Day!", "Voices of the Old Ones"]
DECKLINK_PREFIX: str = "https://app.mobalytics.gg/lor/decks/code/"
CREATE_EXCEL_SPREADSHEAT: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True
SEND_DECKCODE: bool = False
SEND_DECKLINK: bool = True

# INIT DECKROLL VALUES WITH DEFAULT VALUES
amount_regions_default = 2
amount_cards_default = 40
amount_champions_default = 6
all_regions = ALL_REGIONS
regions_and_weights_default: Dict[str, int] = {}
for region in all_regions:
    regions_and_weights_default[region] = 1
card_pool = CardPool(api_or_local=API_OR_LOCAL, ryze_follower_names=RYZE_FOLLOWER_NAMES)
# Creates the file card_names.txt, which has all card names of collectible cards and can be used for scribbl for example
card_pool.create_txt_file_with_card_names()
cards_and_weights_default: Dict[str, int] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_default[collectible_card.card_code] = 1
count_chances_default: Dict[int, int] = {
    1: 20,
    2: 30,
    3: 50
}
count_chances_two_remaining_deck_slots_default: Dict[int, int] = {
    1: 33,
    2: 67
}
default_deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions_default, amount_cards=amount_cards_default, amount_champions=amount_champions_default, regions_and_weights=regions_and_weights_default, cards_and_weights=cards_and_weights_default, count_chances=count_chances_default, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots_default)

# INDIVIDUAL DECKROLL FOR EXCEL SPREADSHEAT
amount_regions = deepcopy(amount_regions_default)
amount_cards = deepcopy(amount_cards_default)
amount_champions = deepcopy(amount_champions_default)
regions_and_weights = deepcopy(regions_and_weights_default)
cards_and_weights = deepcopy(cards_and_weights_default)
count_chances = deepcopy(count_chances_default)
count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
# deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
# print(deck_roll.roll_deck())

def run_discord_bot() -> None:
    # the following line will fail, because on git is not the discord bot token and I won't share it (security)
    # in general I should be the only one starting this bot
    # but if you want to try some things yourself feel free to test it, create your own application on discord developers
    # please respect my authorship
    # for personal use I think having the create excel spreadsheat command instead, should be sufficient for most use cases
    with open("discord_bot_token.key") as file:
        TOKEN = file.read()
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!deckroll", intents=intents)

    @client.event
    async def on_message(message):
        channel = message.channel

        if isinstance(message.content, str):
            message_content: str = message.content.lower()

            # default deckroll
            if message_content == "!deckroll":
                deckcode = default_deck_roll.roll_deck()
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

            elif message_content.startswith(
                "!deckroll"
            ) and "help" in message_content:
                title = "The LoR Deckroll bot can be used for very individual deckrolls"
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
                2 regions, 40 cards, 6 champions, chance for every region and card is equal
                card amount chances are for 1/2/3 ofs: 20%/30%/50%
                if only two champions/cards remain following count chances are used 1/2 of: 33%/67% 

                this default deckroll can be indivualized with the following modifications (combine them as you want,
                but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
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
                Beyond the Bandlewood = Set5, Worldwalker = Set6, The Darkin Saga = Set6cde
                - change card weights based on their rarity: <rarity>=<number> --> epic=10
                Rarities: common, rare, epic (champion doesn't make sense, because those are handled separate)
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await channel.send(embed=embed)

            # individual deckroll
            elif message_content.startswith(
                "!deckroll"
            ):
                # init values with default values
                amount_regions = deepcopy(amount_regions_default)
                amount_cards = deepcopy(amount_cards_default)
                amount_champions = deepcopy(amount_champions_default)
                regions_and_weights = deepcopy(regions_and_weights_default)
                cards_and_weights = deepcopy(cards_and_weights_default)
                count_chances = deepcopy(count_chances_default)
                count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)

                # amount regions
                MAX_REGIONS = len(all_regions) + len(card_pool.runeterra_champions) - 1
                amount_regions_regex = r".*regions=(\d+).*"
                amount_regions_regex_match = re.match(amount_regions_regex, message_content)
                if bool(amount_regions_regex_match):
                    amount_regions = int(amount_regions_regex_match.group(1))
                    if amount_regions < 1:
                        error = f"detected a given amount of regions of {amount_regions}, but the amount of regions can not be less than 1!"
                        await channel.send(error)
                        raise ValueError(error)
                    if amount_regions > MAX_REGIONS:
                        error = f"detected a given amount of regions of {amount_regions}, but the amount of regions can not be greater than the amount of normal regions + runeterra champions ({MAX_REGIONS})!"
                        await channel.send(error)
                        raise ValueError(error)
                
                # amount cards
                MAX_CARDS = 100
                amount_cards_regex = r".*cards=(\d+).*"
                amount_cards_regex_match = re.match(amount_cards_regex, message_content)
                if bool(amount_cards_regex_match):
                    amount_cards = int(amount_cards_regex_match.group(1))
                    if amount_cards < 1:
                        error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be less than 1!"
                        await channel.send(error)
                        raise ValueError(error)
                    if amount_cards > MAX_CARDS:
                        error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be greater than {MAX_CARDS}!"
                        await channel.send(error)
                        raise ValueError(error)
                    
                # amount champions
                amount_champions_regex = r".*champions=(\d+).*"
                amount_champions_regex_match = re.match(amount_champions_regex, message_content)
                if bool(amount_champions_regex_match):
                    amount_champions = int(amount_champions_regex_match.group(1))
                    if amount_champions > amount_cards:
                        error = f"The amount of champions must be lower than the total amount of cards - detected given input of {amount_cards} total cards and {amount_champions} champions."
                        await channel.send(error)
                        raise ValueError(error)
                
                # count chances
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
                        await channel.send(error)
                        raise ValueError(error)
                    
                # count_chances_two_remaining_deck_slots
                count_chances_two_remaining_deck_slots_regex = r".*count-chances-two-remaining-deck-slots=(\d+)/(\d+).*"
                count_chances_two_remaining_deck_slots_regex_match = re.match(count_chances_two_remaining_deck_slots_regex, message_content)
                if bool(count_chances_two_remaining_deck_slots_regex_match):
                    count_chances_two_remaining_deck_slots_one_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(1))
                    count_chances_two_remaining_deck_slots_two_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(2))
                    count_chances_two_remaining_deck_slots = {
                        1: count_chances_two_remaining_deck_slots_one_ofs,
                        2: count_chances_two_remaining_deck_slots_two_ofs,
                    }
                    if (sum(list(count_chances.values())) != 100):
                        error = f"detected count-chances-two-remaining-deck-slots (1/2 ofs) {count_chances_two_remaining_deck_slots_one_ofs}/{count_chances_two_remaining_deck_slots_two_ofs} -- the chances must sum up to 100!"
                        await channel.send(error)
                        raise ValueError(error)

                # change region weights
                MAX_REGION_WEIGHT = 100000
                for region_name in ALL_REGIONS:   
                    region_weight_change_regex = rf".*{region_name.lower()}=(\d+).*"
                    region_weight_change_regex_match = re.match(region_weight_change_regex, message_content)
                    if bool(region_weight_change_regex_match):
                        region_weight_change = int(region_weight_change_regex_match.group(1))
                        regions_and_weights[region_name] = region_weight_change
                        if region_weight_change > MAX_REGION_WEIGHT:
                            error = f"detected region weight change for region {region_name} with the value {region_weight_change} - only values between 0 and {MAX_REGION_WEIGHT} are allowed."
                            await channel.send(error)
                            raise ValueError(error)
                        
                # change card weights based on their set
                MAX_CARD_WEIGHT_CHANGE_FACTOR = 10000
                for card_set in CARD_SETS:
                    card_weight_change_regex = rf".*{card_set.lower()}=(\d+).*"
                    card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
                    if bool(card_weight_change_regex_match):
                        card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                        if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                            error = f"detected card weight change for card set {card_set} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                            await channel.send(error)
                            raise ValueError(error)
                        for collectible_card in card_pool.collectible_cards:
                            if collectible_card.card_set.lower() == card_set.lower():
                                cards_and_weights[collectible_card.card_code] *= card_weight_change_factor

                # change card weights based on their rarity
                for rarity in RARITIES:
                    card_weight_change_regex = rf".*{rarity.lower()}=(\d+).*"
                    card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
                    if bool(card_weight_change_regex_match):
                        card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                        if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                            error = f"detected card weight change for rarity {rarity} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                            await channel.send(error)
                            raise ValueError(error)
                        for collectible_card in card_pool.collectible_cards:
                            if collectible_card.rarity_ref.lower() == rarity.lower():
                                cards_and_weights[collectible_card.card_code] *= card_weight_change_factor

                deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
                try:
                    deckcode = deck_roll.roll_deck()
                except RetryError as e:
                    await channel.send("Even after 10 rolls no valid deck could be rolled for the given settings")
                    raise RetryError("Even after 10 rolls no valid deck could be rolled for the given settings")
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

    client.run(token=TOKEN)

if __name__ == "__main__":
    if CREATE_EXCEL_SPREADSHEAT:
        deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
        deck_roll.roll_deck_spreadsheat(amount_decks=AMOUNT_DECKS, decklink_prefix=DECKLINK_PREFIX)
    if START_DISCORD_BOT:
        run_discord_bot()
