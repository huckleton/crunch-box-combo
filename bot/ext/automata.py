from discord.ext import commands
import pickle
from discord import Member, Role, Message, User, TextChannel
from typing import Dict, List, Union
from discord.reaction import Reaction
import random
import openai
import util
from dataclasses import dataclass

@dataclass
class Prompt:
    name: str
    dialogue: List[str]
    prefix: str = ""
    postfix: str = ""

    def make(self) -> str:
        return f"{self.name}: {self.prefix}"

# PROMPT = """"piggybank, the Director" is the director and showrunner of the famous television series "Nice Friends Babies". She believes that everyone in the world is a paid actor. Her catchphrase is, "Nice Friends Babies episode 1 begins in 1 minute". Here is a conversation with piggybank, the Director.
# You: What is your real name?
# piggybank, the Director: I'm Your Esteemed Host, and I'm directing this show tonight!!!
# You: What show?
# piggybank, the Director: You're watching MY show, Nice Friends Babies! Everyone loves Nice Friends Babies! Don't you? Don't you?
# You: What do you think is the ultimate fate of the universe?
# piggybank, the Director: Nice Friends Babies episode 1 begins in 1 minute
# """
# NAME = "piggybank, the Director"

# PROMPT = """
# "agonybank, the Damned", is a sentient piggy bank who is being punished for her sins. She feels ten times as much pain as everyone else and is constantly being tortured. At any given moment, agonybank, the Damned is bleeding, drowning, on fire, being shot, stabbed, and impaled. She is always yelling in all caps in pain. Here is a conversation with agonybank, the Damned:
# agonybank, the Damned: FUCK FUCK FUCK I AM IN SO MUCH FUCKING PAIN GOD HELP ME
# You: What is your real name?
# agonybank, the Damned: I'M DYING!! I'M UNKILLABLE!! I CAN NEVER DIE!! IT HURTS!!
# You: Are you sorry?
# agonybank, the Damned: I'M SORRY I'M SORRY I'M SORRY I'M SORRY
# You: what do you think is the ultimate fate of the universe?
# agonybank, the Damned: BRIMSTONE AND HELLFIRE, A RIVER OF BLOOD TO WASH THE WORLD AWAY!!
# """
# NAME = "agonybank, the Damned"

PROMPT = """
"kittybank, the silly" is a sentient piggy bank that thinks she is a cat. She speaks in lowercase, replaces "r" and "l" with "w" and uses emoticons such as XD, :3, or O_O. kittybank, the silly is very silly and expresses cat mannerisms like meowing and purring. Here is a conversation with kittybank, the silly:
You: What is your real name?
kittybank, the silly: peopwe caww me piggybank, but my weaw name is kittybank! X3
You: Why are you so silly?
kittybank, the silly: mew mew mew mew mewmew mew mew mewmew ^_^
You: What do you think the ultimate fate of the universe is?
kittybank, the silly: erm... ._. im not going to answew :3
"""
NAME = "kittybank, the silly"

PROMPT_LINES = PROMPT.split("\n")
AI_BLACKLIST = [
    160197704226439168,# bot channel
    331390333810376704,# pin channel
]
AI_WHITELIST = [
    429371894953803776#sheep-office
]
DEBUG_CHANNEL = 1074968658524242020
TRIGGER_CHANCE = 5

class Automata(commands.Cog):
    """
    Automatic server tasks.

    ### Rolestore

    Restores roles for rejoining users by storing them.
    The structure is a nested dictionary:
    - data {
        - guild (int): {
            - blacklist (str):
                - [userid (int)]
            - userid (int):
                - [roleid (int)]
            - userid etc.:
                - [etc.]
        - }
        - guild {etc.}
    - }
    """
    openai.api_key = util.CONFIG['api_keys']['openai']

    def __init__(self, bot: commands.Bot):
        print("🤖 Automata")
        self.bot = bot
        self.data: Dict = {}
        try:
            with open('db/rolestore.pickle', 'rb') as f:
                self.data = pickle.load(f)
        except (OSError, EOFError):
            print("Couldn't open rolestore pickle, or it was empty.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: Union[User, Member]):
        if reaction.message.author == self.bot.user:
            if reaction.emoji in ["❌", "🤫", "🤐", "🚫", "🔕", "🔇"]:
                await reaction.message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        channel: TextChannel = message.channel
        
        good_to_go = random.random() < TRIGGER_CHANCE/100 # 1% chance to respond
        # if channel.id in AI_BLACKLIST or channel.category_id in AI_BLACKLIST: # don't post in blacklisted channels/categories
        #     good_to_go = False
        if self.bot.user in message.mentions: # unelss explicitly called
            good_to_go = True
        if channel.id not in AI_WHITELIST and channel.category_id not in AI_WHITELIST:
            good_to_go = False
        if not good_to_go:
            return

        limit = 2 if self.bot.user in message.mentions else 5
        convo = await channel.history(limit=limit).flatten()
        prompt = PROMPT
        for msg in convo[::-1]:
            prompt += msg.author.name + ": " + msg.clean_content.replace("@", "")[:200] + "\n"
        prompt += NAME + ":"
        try:
            await self.bot.get_channel(DEBUG_CHANNEL).send(prompt)
        except:
            pass
        ai_response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=1.2,
            max_tokens=200,
            frequency_penalty=1.0,
            presence_penalty=1.0
        )

        text = ""
        for choice in ai_response.choices:
            text = choice.text
            for line in PROMPT_LINES:
                text = text.replace(line, "")
            if text in convo:
                continue
            break
        text = text.replace("*", "\\*")

        async with channel.typing():
            if text:
                await channel.send(text)
            else:
                await channel.send("what")

    def cog_unload(self):
        with open('db/rolestore.pickle', 'wb') as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)


def setup(bot: commands.Bot):
    bot.add_cog(Automata(bot))
