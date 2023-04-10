## LoR Deckroll
# Script + Discord Bot

# Discord Bot Invite Link
https://discord.com/api/oauth2/authorize?client_id=1074070984124014632&permissions=11328&scope=bot

# execute main
poetry run Python ./main.py

# Formatting
poetry run black .

# Legends-of-Runeterra-deckroll was created to create random decks with a lot of configuration options and the ability to create decks for a whole tournament.
If you have questions or ideas on how to improve this tool feel free to ask/suggest them.
I hope the main.py is self-explanatory, otherwise ask questions and I will comment it for better understanding (and yes without programming background it can be quite hard to understand any code).
Happy deckrolling everyone!

# Some tips for using it yourself
If you want to use it, you need to clone the repository with:
git clone https://github.com/Ghostdriver/Legends-of-Runeterra-deckroll.git
Necessary for using it is Python 3.10 - I would recommend to download the last LTS version from https://www.python.org/downloads/ 
I use poetry as packet manager. It can be installed following the steps on https://python-poetry.org/docs/ -- afterwards you have to use poetry install in the project folder, it will install the packages specified in the pyproject.toml, so everyone, who clones this repository downloads the same packages, which should lead to device independant funcionality.
