from typing import  Dict
from CardData import ALL_REGIONS, CARD_SETS, RARITIES, LANGUAGES
from CardPool import CardPool
from Deckroll import Deckroll
import discord
from discord.ext import commands
from copy import deepcopy
import re
import random
from tenacity import RetryError
from discord_images import assemble_card_image, screenshot_deck_from_runeterrra_ar

# CARD_SETS in CardData needs to be updated
# because I haven't found a good way to get ryze associated cards, a list with all card names belonging to him has to be given (a better solution would be appreciated)
RYZE_FOLLOWER_NAMES = ["Feral Prescience", "Warning Shot", "Advanced Intel", "Bandle Tellstones", "Bilgewater Tellstones", "Bloodbait", "Construct of Desolation", "Demacian Tellstones", "Fae Sprout", "Heavens Aligned", "Imagined Possibilities", "Ionian Tellstones", "Jettison", "Jury-Rig", "Messenger's Sigil", "Mushroom Cloud", "Noxian Tellstones", "Piltovan Tellstones", "Ranger's Resolve", "Ransom Riches", "Sapling Toss", "Shadow Isles Tellstones", "Shroud of Darkness", "Shuriman Tellstones", "Spell Thief", "Stoneweaving", "Stress Testing", "Targonian Tellstones", "Tempting Prospect", "Three Sisters", "Trinket Trade", "Allure", "Ancestral Boon", "Behold the Infinite", "Calculated Creations", "Discreet Invitation", "Encore", "Entrapment", "Entreat", "Field Promotion", "Gifts From Beyond", "Icathian Myths", "Insight of Ages", "Line 'Em Up", "Magical Journey", "Payday", "Poro Stories", "Rite of Passage", "Shared Spoils", "Sown Seeds", "Starbone", "Supercool Starchart", "Swindle", "Time Trick", "Trail of Evidence", "Arise!", "Call the Wild", "Dragon's Clutch", "En Garde", "Fae Aid", "Flash of Brilliance", "Formal Invitation", "Lure of the Depths", "Mobilize", "Pilfered Goods", "Poro Snax", "Sap Magic", "Stalking Shadows", "Starlit Epiphany", "Unraveled Earth", "Vision", "Encroaching Shadows", "Lost Riches", "Risen Mists", "Salvage", "Sneezy Biggledust!", "Stand Alone", "The Unending Wave", "The Unforgiving Cold", "Whispered Words", "Winter's Touch", "Catalyst of Aeons", "Deep Meditation", "Drum Solo", "Eye of Nagakabouros", "Gift of the Hearthblood", "Nine Lives", "Portalpalooza", "The Time Has Come", "Aurora Porealis", "Celestial Trifecta", "Formula", "Glory's Call", "Hextech Anomaly", "Hidden Pathways", "Sands of Time", "Shaman's Call", "Eclectic Collection", "Servitude of Desolation", "Spirit Fire", "Sputtering Songspinner", "Progress Day!", "Voices of the Old Ones"]
SCREENSHOT_PREFIX = "https://runeterra.ar/decks/bot/"
DECKLINK_PREFIX: str = "https://runeterra.ar/decks/code/"
DECKROLL_DECK_PREFIX: str = "https://app.mobalytics.gg/lor/decks/code/"
CREATE_EXCEL_SPREADSHEAT: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True

# INIT DECKROLL VALUES WITH DEFAULT VALUES
language_default = "en_us"
amount_regions_default = 2
amount_cards_default = 40
amount_champions_default = 6
all_regions = ALL_REGIONS
regions_and_weights_default: Dict[str, int] = {}
for region in all_regions:
    regions_and_weights_default[region] = 1
card_pool = CardPool(ryze_follower_names=RYZE_FOLLOWER_NAMES)
# Creates the file card_names.txt, which has all card names of collectible cards and can be used for scribbl for example
# card_pool.create_txt_file_with_card_names()
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

# INDIVIDUAL DECKROLL FOR EXCEL SPREADSHEAT - change the values to fit your needs!
amount_regions = amount_regions_default
amount_cards = amount_cards_default
amount_champions = amount_champions_default
regions_and_weights = deepcopy(regions_and_weights_default)
cards_and_weights = deepcopy(cards_and_weights_default)
count_chances = deepcopy(count_chances_default)
count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
# deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
# print(deck_roll.roll_deck())

def run_discord_bot() -> None:
    # the following line will fail, because on git is not the discord bot token and I won't share it (security)
    # for personal use I think having the create excel spreadsheat command should be sufficient for most use cases
    # so if the script fails here please set START_DISCORD_BOT = False
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

            # DISPLAY DECK
            if message_content.startswith("!deck "):
                deckcode = ""
                language = language_default
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
                
                # screenshot and send embed in Discord
                deck_url = f"{DECKLINK_PREFIX}{deckcode}?lang={language}"
                embed = discord.Embed(title="Decklink runeterra.ar", url=deck_url)
                screenshot_url = f"{SCREENSHOT_PREFIX}{deckcode}?lang={language}"
                await screenshot_deck_from_runeterrra_ar(screenshot_url=screenshot_url)
                file = discord.File("./images/screenshot.png", filename="screenshot.png")
                embed.set_image(url="attachment://screenshot.png")
                await message.channel.send(file=file, embed=embed)


            # SHOW CARD INFO
            elif message_content.startswith("!card "):
                language = language_default
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
                    
                card = card_pool.get_card_by_card_name(card_name=card_name, language=language)
                found_card_name = card.name
                assemble_card_image(card_pool=card_pool, card=card, language=language)
                embed = discord.Embed(title=found_card_name)
                file = discord.File("./images/card.jpg", filename="card.jpg")
                embed.set_image(url="attachment://card.jpg")

                await message.channel.send(file=file, embed=embed)
            
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
                2 regions, 40 cards, 6 champions, chance for every region and card is equal
                card amount chances are for 1/2/3 ofs: 20%/30%/50%
                if only two champions/cards remain following count chances are used 1/2 of: 33%/67% 

                this default deckroll can be indivualized with the following modifications (combine them as you want,
                but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
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
                await channel.send(embed=embed)

            # DECKROLL
            elif message_content.startswith("!deckroll"):
                # init values with default values
                language = language_default
                amount_regions = amount_regions_default
                amount_cards = amount_cards_default
                amount_champions = amount_champions_default
                regions_and_weights = deepcopy(regions_and_weights_default)
                cards_and_weights = deepcopy(cards_and_weights_default)
                count_chances = deepcopy(count_chances_default)
                count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)

                # language
                language_regex = r".*lang=([a-z]{2}).*"
                language_regex_match = re.match(language_regex, message_content)
                if bool(language_regex_match):
                    for language_abbreviation in LANGUAGES:
                        language_match = language_regex_match.group(1)
                        if language_match == language_abbreviation:
                            language = LANGUAGES[language_match]
                            break

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
                # print(f"{message.author.name}: {message_content} --> {deckcode}")

                await message.channel.send(deckcode)

                # screenshot and send embed in Discord
                deck_url = f"{DECKLINK_PREFIX}{deckcode}?lang={language}"
                embed = discord.Embed(title="Decklink runeterra.ar", url=deck_url)
                screenshot_url = f"{SCREENSHOT_PREFIX}{deckcode}?lang={language}"
                await screenshot_deck_from_runeterrra_ar(screenshot_url=screenshot_url)
                file = discord.File("./images/screenshot.png", filename="screenshot.png")
                embed.set_image(url="attachment://screenshot.png")
                await message.channel.send(file=file, embed=embed)

            # CARDROLL HELP
            elif message_content == "!cardroll help":
                title = "Cardroll help"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll

                cardroll just picks one random card from all collectible cards

                the default cardroll can be indivualized with the following modifications (combine them as you want,
                but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                - lang=<language> --> lang=es
                de=German, en=English (default), es=Spanish, mx=Mexican Spanish, fr=French, it=Italian, ja=Japanese,
                ko=Korean, pl=Polish, pt=Portuguese, th=Thai, tr=Turkish, ru=Russian, zh=Chinese

                - when modifying the card weights the standard weight of 1 is multiplied with the modification
                --> e.g. passing Demacia=10 and Champion=10, Garen is 100 times as likely as non demacian, non champion cards
                
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
                await channel.send(embed=embed)
            # CARDROLLL
            elif message_content.startswith("!cardroll"):
                # init values with default values
                language = language_default
                regions_and_weights = deepcopy(regions_and_weights_default)
                cards_and_weights = deepcopy(cards_and_weights_default)

                # language
                language_regex = r".*lang=([a-z]{2}).*"
                language_regex_match = re.match(language_regex, message_content)
                if bool(language_regex_match):
                    for language_abbreviation in LANGUAGES:
                        language_match = language_regex_match.group(1)
                        if language_match == language_abbreviation:
                            language = LANGUAGES[language_match]
                            break
                
                MAX_CARD_WEIGHT_CHANGE_FACTOR = 10000
                # change card weights based on their region
                for region_name in ALL_REGIONS:   
                    card_weight_change_regex = rf".*{region_name.lower()}=(\d+).*"
                    card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
                    if bool(card_weight_change_regex_match):
                        card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                        if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                            error = f"detected card weight change for card set {card_set} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                            await channel.send(error)
                            raise ValueError(error)
                        for collectible_card in card_pool.collectible_cards:
                            card_region_refs_lower = [card_region_ref.lower() for card_region_ref in collectible_card.region_refs]
                            if region_name.lower() in card_region_refs_lower:
                                cards_and_weights[collectible_card.card_code] *= card_weight_change_factor
                        
                # change card weights based on their set              
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

                random_card_code = random.choices(list(cards_and_weights.keys()), weights=list(cards_and_weights.values()))[0]
                # print(f"{message.author.name}: {message_content} --> {deckcode}")

                card = card_pool.get_card_by_card_code(card_code=random_card_code, language=language)
                random_card_name = card.name
                assemble_card_image(card_pool=card_pool, card=card, language=language)
                embed = discord.Embed(title=random_card_name)
                file = discord.File("./images/card.jpg", filename="card.jpg")
                embed.set_image(url="attachment://card.jpg")

                await message.channel.send(file=file, embed=embed)

    client.run(token=TOKEN)

if __name__ == "__main__":
    if CREATE_EXCEL_SPREADSHEAT:
        deck_roll = Deckroll(card_pool=card_pool, amount_regions=amount_regions, amount_cards=amount_cards, amount_champions=amount_champions, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
        deck_roll.roll_deck_spreadsheat(amount_decks=AMOUNT_DECKS, decklink_prefix=DECKROLL_DECK_PREFIX)
    if START_DISCORD_BOT:
        run_discord_bot()
