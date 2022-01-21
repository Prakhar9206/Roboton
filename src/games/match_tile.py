import discord
from discord.ext import commands
import asyncio
import random


# match tile
class match_tile_buttons(discord.ui.Button):
    ZERO_WIDTH = "\u200b"
    question_mark_emoji = "❓"

    def __init__(self, ctx):
        super().__init__(style= discord.ButtonStyle.grey, label=self.ZERO_WIDTH, emoji=self.question_mark_emoji)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        view: match_tile_view = self.view

        _index = view.children.index(self)
        await view.open_tile(_index)
        clown_check = await view.check_for_clown(_index, self)
        if clown_check is True:
            return

        view.total_opened_tiles += 1
        check = view.check_if_2_tiles_are_open()

        # if 2 tiles are open
        if check is True:
            view.processing = True
            matched = view.match_open_tiles()
            # if 2 tiles are open and they match
            if matched is True:
                view.edit_matching_tiles()

                win = await view.check_for_winning()
                if win is False:
                    em = discord.Embed(title=view.get_embed_title())
                    await interaction.response.edit_message(embed=em, view=view)
                    await asyncio.sleep(1.5)
                    await view.make_matched_buttons_blank()
                    view.processing = False
            else:
                # if 2 tiles are open but they DONT match
                em = discord.Embed(title=view.get_embed_title())
                await interaction.response.edit_message(embed=em, view=view) # just edits to show the 2nd open tile

                await asyncio.sleep(1.5)
                await view.reset_non_matching_tiles()
                view.processing = False
        else:
            win = await view.check_for_winning()
            if win is False:
                em = discord.Embed(title=view.get_embed_title())
                await interaction.response.edit_message(embed=em, view=view)


class match_tile_view(discord.ui.View):
    RED_COLOUR = 0xfc0335 # red
    GREEN_COLOUR = 0x03fc62 # green 
    ZERO_WIDTH = "\u200b"

    def __init__(self, ctx: commands.Context, message: discord.Message):
        super().__init__()
        self.ctx = ctx
        self.timeout = 40
        self.message = message
        self.points = 0
        self.clown_clicked = False
        self.embed = discord.Embed(title=self.get_embed_title())
        self.raw_emojis = [
            "<:PeepoGGERS:884452661699706900>",
            "<:PepeCrying:884454914556833843>",
            "<:PepeHype:884452020805861486>",
            "<:m_pepeheart:884453418297618462>",
            "<:peepodumb:884454564122722314>",
            "<:peepolove:884452111566393394>",
            "<:pepeevil:884455575373635624>",
            "<:pepeheart:884453710497984552>",
            "<:pepepog:884454497160663040>",
            "<:pepepoint:884455084530991205>",
            "<:pepesmart:884453912101412865>",
            "<:pepewritethatdown:884454007354060840>"
        ]
        self.clown_emoji = "<:pepeclown:884455754533310545>"
        self.blank_emoji = "<:blank:885545215065206856>"
        self.question_mark_emoji = "❓"
        self.matched_buttons = [] #it will contain indexes of buttons which are opened and matched

        self.processing = False

        self.unshuffled_emojis = []
        for i in self.raw_emojis:
            self.unshuffled_emojis.append(i)
            self.unshuffled_emojis.append(i)
        self.unshuffled_emojis.append(self.clown_emoji)
        self.shuffled_emojis = random.sample(self.unshuffled_emojis, len(self.unshuffled_emojis))
        for i in range(25):
            self.add_item(match_tile_buttons(self.ctx))

        self.total_opened_tiles = 0
        self.previously_opened_tile = None
        self.opened_tile = None
        print(f"clown at {(self.shuffled_emojis.index(self.clown_emoji)) +1}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (interaction.user.id == self.ctx.author.id) and (self.processing is False):
            return True
        else:
            await interaction.response.defer()
            return False

    async def on_timeout(self):
        self.embed.title = "Timeout! You didn't click on any button for a long time!"
        self.embed.description = self.get_embed_title()
        self.embed.colour = self.RED_COLOUR
        self.disable_buttons()
        self.stop()
        await self.message.edit(embed=self.embed, view=self)

    def get_embed_title(self) -> str:
        if self.clown_clicked is True:
            return f"{self.ctx.author}'s game of match the tiles.\nPoints = {self.points}/12\nYou clicked on the clown! You lost."
        elif self.points == 12:
            return f"{self.ctx.author}'s game of match the tiles.\nPoints = {self.points}/12\nYou won! Congrats"
        else:
            return f"{self.ctx.author}'s game of match the tiles.\nPoints = {self.points}/12"

    def disable_buttons(self):
        for btn in self.children:
            btn.disabled = True

    async def open_tile(self, index):
        button: discord.ui.Button = self.children[index]
        button.emoji = self.shuffled_emojis[index]
        button.label = self.ZERO_WIDTH
        await self.change_opened_tiles_order(index)

    async def check_for_clown(self, index, button: discord.ui.Button):
        emoji = self.shuffled_emojis[index]
        if emoji == self.clown_emoji:
            button.style = discord.ButtonStyle.red
            self.disable_buttons()
            self.clown_clicked = True
            em = discord.Embed(title=self.get_embed_title(), colour=self.RED_COLOUR)
            await self.message.edit(embed=em, view=self)
            self.stop()
            return True
        else:
            return False

    def check_if_2_tiles_are_open(self) -> bool: # just checks current number of open tiles

        if self.total_opened_tiles == 2:
            return True
        else:
            return False

    def match_open_tiles(self): # matches 2 open tiles with their emojis
        
        button_1 = self.children[self.previously_opened_tile]
        button_2 = self.children[self.opened_tile]
        if (button_1.emoji == button_2.emoji) and (self.previously_opened_tile != self.opened_tile):
            return True
        else:
            return False

    async def change_opened_tiles_order(self, new_index): # just to change opened_tile to previously_opened_tile accordingly
        if self.previously_opened_tile is None and self.opened_tile is None:
            self.opened_tile = new_index

        elif self.previously_opened_tile is None and self.opened_tile is not None:
            self.previously_opened_tile = self.opened_tile
            self.opened_tile = new_index
        
        elif self.previously_opened_tile is not None and self.opened_tile is not None:
            check = self.check_if_2_tiles_are_open() # this will always be true but anyways two different checks for same things
            if check is True:
                if self.match_open_tiles():
                    self.edit_matching_tiles()
                else:
                    await self.reset_non_matching_tiles()

    async def reset_non_matching_tiles(self):
        for index, button in enumerate(self.children):
            button.emoji = self.question_mark_emoji
            if index in self.matched_buttons:
                button.emoji = self.blank_emoji

        self.previously_opened_tile = None
        self.opened_tile = None
        self.total_opened_tiles = 0
        em = discord.Embed(title=self.get_embed_title())
        await self.message.edit(embed=em, view=self)

    def edit_matching_tiles(self):
        button_1 = self.children[self.previously_opened_tile]
        button_2 = self.children[self.opened_tile]

        button_1.style = discord.ButtonStyle.green
        button_1.disabled = True
        button_2.style = discord.ButtonStyle.green
        button_2.disabled = True
        self.points += 1

        self.matched_buttons.append(self.previously_opened_tile)
        self.matched_buttons.append(self.opened_tile)

        self.previously_opened_tile = None
        self.opened_tile = None
        self.total_opened_tiles = 0

    async def make_matched_buttons_blank(self):
        for index in self.matched_buttons:
            button: discord.ui.Button = self.children[index]
            button.emoji = self.blank_emoji
        em = discord.Embed(title=self.get_embed_title())
        await self.message.edit(embed=em, view=self)

    async def check_for_winning(self):
        """Checks is the game is over based on points.
        If the players wins, it edits the message and stops the view.
        Otherwise returns False
        """
        if self.points == 12:
            em = discord.Embed(title=self.get_embed_title(), colour=self.GREEN_COLOUR)
            self.disable_buttons()
            self.stop()
            await self.message.edit(embed=em, view=self)
            return True
        else:
            return False
#==============================================================