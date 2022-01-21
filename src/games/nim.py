import discord
from discord.ext import commands
import random

class NimButton(discord.ui.Button):
    def __init__(self, row: int, column: int):
        super().__init__(style=discord.ButtonStyle.gray, emoji="\N{LARGE RED CIRCLE}", row=row)
        self.row = row # 0,1,2,3,4
        self.column = column # 0,1,2,3,4

    async def callback(self, interaction: discord.Interaction):
        view: NimView = self.view
        self.index = view.children.index(self)
        view.update_grid(self.row, self.column)
        view.update_buttons()
        view.update_embed()

        await interaction.response.edit_message(embed=view.embed, view=view)


class NimView(discord.ui.View):

    def __init__(self, ctx: commands.Context, member: discord.Member):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.member = member
        self.current_player = random.choice((self.ctx.author, self.member))
        self.embed = discord.Embed(title=f"__**{self.current_player.name}'s turn**__")

        # 1 -> ball is present, 0 -> ball is removed
        self.grid = [
            [1],
            [1,1],
            [1,1,1],
            [1,1,1,1],
            [1,1,1,1,1],
        ]
    
        for i in range(1, 6): # rows - 1,2,3,4,5
            for j in range(i): # column - 0,1,2,3,4
                self.add_item(NimButton(row = i-1, column=j))
    

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (interaction.user.id != self.ctx.author.id) and (interaction.user.id != self.member.id):
            return await interaction.response.send_message("You cannot play this game. Consider starting a new game by typing `[prefix]nim [member]`", ephemeral=True)

        if interaction.user.id == self.current_player.id:
            return True

        return await interaction.response.send_message("It's not your turn now.", ephemeral=True)
        
    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True
        await self.message.edit(content="Timeout reached", view=self)

    def update_grid(self, row: int, clicked_column: int):

        first_1 = self.grid[row].index(1) # gets the column of first occurence of 1
        # index = self.grid[row][clicked_column]

        for col in range(first_1, clicked_column+1):
            self.grid[row][col] = 0

    def update_buttons(self) -> None:
        """Clears the buttons and adds a fresh set of buttons based of `self.grid`"""
        self.clear_items()

        for row_index, row in enumerate(self.grid):
            for col_index, col in enumerate(row):
                if col == 0:
                    self.add_item(discord.ui.Button(style=discord.ButtonStyle.grey, emoji="<:blank:885545215065206856>", disabled=True, row=row_index))
                elif col == 1:
                    self.add_item(NimButton(row = row_index, column=col_index))

    def check_for_winning(self) -> bool:
        """Returns `True` if a winner is found, else `False`"""
        for row in self.grid:
            for col in row:
                if col: # 1 found
                    return False
        return True # no 1 was found

    def update_embed(self):

        if self.check_for_winning():
            self.embed.title = f"__**{self.current_player}**__ won!"
            self.embed.colour = 0x03fc17
            self.stop()
        else:
            if self.current_player.id == self.ctx.author.id:
                self.current_player = self.member
            elif self.current_player.id == self.member.id:
                self.current_player = self.ctx.author

            self.embed.title = f"__**{self.current_player.name}'s turn**__"
            

