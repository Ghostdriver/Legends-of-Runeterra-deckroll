# Discord Bot Invite Link
https://discord.com/api/oauth2/authorize?client_id=1074070984124014632&permissions=3072&scope=bot

# Legends-of-Runeterra-deckroll was created to create random decks with a lot of configuration options and the ability to create decks for a whole tournament.
If you have questions or ideas on how to improve this tool feel free to ask/suggest them.
I hope the main.py is self-explanatory, otherwise ask questions and I will comment it for better understanding (and yes without programming background it can be quite hard to understand any code).
Happy deckrolling everyone!

If you want to use it, you need to clone the repository with:
git clone https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll.git
Necessary for using it is Python 3.10 - I would recommend to download the last LTS version from https://www.python.org/downloads/ 
I use poetry as packet manager. It can be installed following the steps on https://python-poetry.org/docs/ -- afterwards you have to use poetry install in the project folder, it will install the packages specified in the pyproject.toml, so everyone, who clones this repository downloads the same packages, which should lead to device independant funcionality.
For programming I use Visual Studio Code, but there are a lot of alternatives, which should work aswell.

The most important part is the deckroll function:
def deckroll(allowed_cards: List[lor_card] = collectible_cards, weight_cards: bool = False, card_weights: List[int] = card_weights, total_amount_cards: int = 40, amount_champs: int = 6, regions: List[str] = all_regions, weight_regions: bool = False, region_weights: List[int] = region_weights, mono_region_chance: int = 0, allow_two_runeterra_champs: bool = True, one_of_chance: int = 20, two_of_chance: int = 30, three_of_chance: int = 50, fill_up_one_and_two_ofs_if_out_of_rollable_cards: bool = True) -> str:
This is only the defintiion of the function and parameteres ... it takes a lot of parameters to make it customizable in the ways I thought of, but has default parameters, that I think are the best for the standard use case.
So if you want to roll a deck you write at the end of the main.py deck = deckroll() and then you can print(deck) and have the deckcode printed in the console.
You can customize it, by giving a smaller list of allowed cards to the function, if you have custom cards or want to exclude cards, you can change the chances to get cards with saying weight_cards=True and giving card weights -- it's built in a way that you have an array of cards allowed cards [card1, card2, card3 ... cardn] and give an array of card_weights [weight1, weight2, weight3, ... weightn], so every card has a weight. If card1 is Vladimir and weight1 is 10 and card2 is Katarina with weight2 of 1, then Vladimir is 10 times as likely as Katarina, when rolling the champions for the deck. you can change the amount of cards, if you maybe just want 20 cards and then built from there or you give 60 cards and cut down to 40 yourself or whatever, I think more than 100 cards is not possible in the LoR-Client so I said this is the maximum. The same applies to champions. regions and their weights are customizable aswell, so you can take out demacia, if you don't like that region. mono_region_chance is the chance to just roll 1 region and have a mono_region_deck. two runeterra champs leads to pretty streamlined decks, because these champs don't have a lot of cards, so there is the option to disable it by setting allow_two_runeterra_champs to False, chances for one, two and three ofs mean a card gets rolled: e.g. treasured thrash and then the amount of this card gets rolled based on the given values.

So you can use deckroll for one deck. You can put it in a for-loop for multiple decks and that's what I did already in create_tournament_spreadsheat: you have to set the amount_players, have some bonus options for the spreadsheat, the options for the deckrolls and then will roll a deck for each of them and paste the code in a excel spreadsheat in the same folder. (10000 decks take my PC around 18 seconds).
There are two other related functions made for Monday Madness, a tournament worth checking out.
Use these functions, if they better suit your usecase.

Examples for modifying a deckroll:
- Make Region Runeterra very likely:
region_weights[all_regions.index("Runeterra")] = 20
- Exclude a region:
region_weights[all_regions.index("Demacia")] = 0
- Make newest cards more likely:
for index, card in enumerate(collectible_cards):
    if card.card_set == "Set6":
        card_weights[index] = 10
