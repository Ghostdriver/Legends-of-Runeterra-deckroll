from typing import  Dict, Literal
from CardData import ALL_REGIONS
from CardPool import CardPool
from Deckroll import Deckroll
import discord
from discord.ext import commands

# CARD POOL OPTIONS
# IF cards should get fetched from API (needs some time for the first run - up to a few minutes)
# CARD_SETS in CardData needs to be updated
# if cards should get read out from local files (really fast) the newest json files have to be in the local_cards_sets_folder
# those can be retrieved from https://developer.riotgames.com/docs/lor with the names "https://dd.b.pvp.net/latest/{card_set}-lite-en_us.zip"
# then just unzip those and put the {card_set}-1en_us.json in the extracted folder en_us/data into the directory
# because I haven't found a good way to get ryze associated cards, a list with all card names belonging to him has to be given (a better solution would be appreciated)
API_OR_LOCAL: Literal["API", "LOCAL"] = "LOCAL"
RYZE_FOLLOWER_NAMES = ["Feral Prescience", "Warning Shot", "Advanced Intel", "Bandle Tellstones", "Bilgewater Tellstones", "Bloodbait", "Construct of Desolation", "Demacian Tellstones", "Fae Sprout", "Heavens Aligned", "Imagined Possibilities", "Ionian Tellstones", "Jettison", "Jury-Rig", "Messenger's Sigil", "Mushroom Cloud", "Noxian Tellstones", "Piltovan Tellstones", "Ranger's Resolve", "Ransom Riches", "Sapling Toss", "Shadow Isles Tellstones", "Shroud of Darkness", "Shuriman Tellstones", "Spell Thief", "Stoneweaving", "Stress Testing", "Targonian Tellstones", "Tempting Prospect", "Three Sisters", "Trinket Trade", "Allure", "Ancestral Boon", "Behold the Infinite", "Calculated Creations", "Discreet Invitation", "Encore", "Entrapment", "Entreat", "Field Promotion", "Gifts From Beyond", "Icathian Myths", "Insight of Ages", "Line 'Em Up", "Magical Journey", "Payday", "Poro Stories", "Rite of Passage", "Shared Spoils", "Sown Seeds", "Starbone", "Supercool Starchart", "Swindle", "Time Trick", "Trail of Evidence", "Arise!", "Call the Wild", "Dragon's Clutch", "En Garde", "Fae Aid", "Flash of Brilliance", "Formal Invitation", "Lure of the Depths", "Mobilize", "Pilfered Goods", "Poro Snax", "Sap Magic", "Stalking Shadows", "Starlit Epiphany", "Unraveled Earth", "Vision", "Encroaching Shadows", "Lost Riches", "Risen Mists", "Salvage", "Sneezy Biggledust!", "Stand Alone", "The Unending Wave", "The Unforgiving Cold", "Whispered Words", "Catalyst of Aeons", "Deep Meditation", "Drum Solo", "Eye of Nagakabouros", "Gift of the Hearthblood", "Nine Lives", "Portalpalooza", "The Time Has Come", "Aurora Porealis", "Celestial Trifecta", "Glory's Call", "Hextech Anomaly", "Hidden Pathways", "Sands of Time", "Shaman's Call", "Eclectic Collection", "Servitude of Desolation", "Spirit Fire", "Sputtering Songspinner", "Progress Day!", "Voices of the Old Ones"]
DECKLINK_PREFIX: str = "https://app.mobalytics.gg/lor/decks/code/"
CREATE_EXCEL_SPREADSHEAT: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True
SEND_DECKCODE: bool = False
SEND_DECKLINK: bool = True

# INIT REGION AND CARD POOLS AND THEIR WEIGHTS
all_regions = ALL_REGIONS
regions_and_weights: Dict[str, float] = {}
for region in all_regions:
    regions_and_weights[region] = 1.0
card_pool = CardPool(api_or_local=API_OR_LOCAL, ryze_follower_names=RYZE_FOLLOWER_NAMES)
# Creates the file card_names.txt, which has all card names of collectible cards and can be used for scribbl for example
card_pool.create_txt_file_with_card_names()
cards_and_weights: Dict[str, float] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights[collectible_card.card_code] = 1.0
count_chances: Dict[int, float] = {
    1: 0.2,
    2: 0.3,
    3: 0.5
}
count_chances_two_remaining_deck_slots: Dict[int, float] = {
    1: 0.33,
    2: 0.66
}
default_deck_roll = Deckroll(card_pool=card_pool, amount_regions=2, amount_cards=40, amount_champs=6, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
    
def run_discord_bot() -> None:
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
            ) and message_content.__contains__("help"):
                title = "This bot can process default and individual deckrolls"
                help_message = """
                This bot can process default and individual deckrolls


                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await channel.send(embed=embed)

            # individual deckroll

    client.run(token=TOKEN)


if __name__ == "__main__":
    if CREATE_EXCEL_SPREADSHEAT:
        deck_roll = Deckroll(card_pool=card_pool, amount_regions=2, amount_cards=40, amount_champs=6, regions_and_weights=regions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
        deck_roll.roll_deck_spreadsheat(amount_decks=AMOUNT_DECKS, decklink_prefix=DECKLINK_PREFIX)
    if START_DISCORD_BOT:
        run_discord_bot()
