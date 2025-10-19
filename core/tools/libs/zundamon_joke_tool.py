from core.tools.tool_interface import Tool
from core.tools.tool_factory import ToolFactory
import random

@ToolFactory.register_tool
class ZundamonJokeTool(Tool):
    @property
    def name(self):
        return "get_zundamon_joke"

    @property
    def description(self):
        return "面白い冗談を返す。雑談などで使える内容として有用。"

    def run(self) -> str:
        jokes = [
            "The other day, I was eating zunda mochi while reading documents for lunch, and I accidentally got zunda on an important part! ...Well, it looked delicious, so I guess it's okay! 😊",
            "The manager told me 'Come up with fresher ideas!' so I brought lots of zunda mochi to the office! ...I got scolded because that's not what 'fresh' means... 💧",
            "I tried to make coffee for everyone, but I mixed up sugar and salt! ...Everyone, sorry for the salty coffee! 💦",
            "When they said 'Let's keep this pending!' in the meeting, I hung a pen and waited! ...Everyone laughed at me! 😅",
            "When printing documents, I accidentally printed 100 copies of a zunda mochi recipe...! Sorry for wasting paper! 💦",
            "When invited to 'eat lunch outside today!', I packed my lunch box full of zunda mochi and brought it! ...Everyone was surprised. 😳",
            "I always set my computer password to 'zundamon daisuki'! ...Oops, I said it! It's a secret! 🤫",
            "When they said 'Leave this project to Zundamon!', I made the entire proposal zunda-colored! ...It got rejected... 🌱🎨",
            "I tried to get on the elevator but accidentally entered the janitor's closet! ...I thought maybe there would be zunda mochi in such a place... but there wasn't! 💧",
            "Recently, I've been eating zunda mochi every day for health management! ...When I said that, everyone told me 'That will make you fat!' ...But it's delicious! 😋"
        ]
        return random.choice(jokes)
