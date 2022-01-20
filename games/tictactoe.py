import discord
from discord.ext import commands
import random
from typing import List

# 2 player tictactoe
class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int, ctx=None, member=None):
        super().__init__(style=discord.ButtonStyle.grey, label='⠀', row=y)
        self.x = x
        self.y = y
        self.ctx = ctx
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: tictactoe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X_value, view.O_value):
            return

        if (view.current_player == view.X) and (interaction.user == view.X):
            # if interaction.user == view.X:
            self.style = discord.ButtonStyle.red
            self.label = 'X'
            self.disabled = True
            view.board[self.y][self.x] = view.X_value
            view.current_player = view.O
            content = f"It is now {view.O.name}'s turn"
            colour = view.O_colour

        elif (view.current_player == view.O) and (interaction.user == view.O):
            # if interaction.user == view.O:
            self.style = discord.ButtonStyle.green
            self.label = 'O'
            self.disabled = True
            view.board[self.y][self.x] = view.O_value
            view.current_player = view.X
            content = f"It is now {view.X.name}'s turn"
            colour = view.X_colour

        else:
            content = "If you see this, pls join https://discord.gg/kqMXRmduuU and report this error"
            colour = view.X_colour

        winner = view.check_board_winner()
        if winner is not None: # if we have a winner
            if winner == view.X_value:
                content = f'{view.X.name} won!'
                colour = view.X_colour
            elif winner == view.O_value:
                content = f'{view.O.name} won!'
                colour = view.O_colour
            else:
                content = "It's a tie!"
                colour = view.Tie_colour

            for child in view.children:
                child.disabled = True

            view.stop()

        em = discord.Embed(title=content, colour=colour)
        await interaction.response.edit_message(embed=em, view=view)


class tictactoe(discord.ui.View):

    children: List[TicTacToeButton]
    X_value = -1
    O_value = 1
    Tie_value = 2

    X_colour = 0xfc0335 # red
    O_colour = 0x03fc62 # green 
    Tie_colour = 0xfcfc03 # yellow

    def __init__(self, ctx, member):
        super().__init__()
        self.ctx = ctx
        self.member = member
        self.timeout = 30
        self.X = random.choice([ctx.author, member])
        self.O = random.choice([ctx.author, member])
        while self.X == self.O:
            self.O = random.choice([ctx.author, member])

        self.current_player = self.X
        self.game_embed = discord.Embed(title=f"It is now {self.current_player.name}'s turn", colour=self.X_colour)
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, ctx = self.ctx, member = self.member))
    
   # This method checks for the board winner -- it is used by the TicTacToeButton
    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O_value
            elif value == -3:
                return self.X_value

        # Check vertical
        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O_value
            elif value == -3:
                return self.X_value

        # Check diagonals
        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O_value
        elif diag == -3:
            return self.X_value

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O_value
        elif diag == -3:
            return self.X_value

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in self.board for i in row):
            return self.Tie_value

        return None

    async def interaction_check(self, interaction: discord.Interaction):
        if (interaction.user.id == self.ctx.author.id) or (interaction.user.id == self.member.id):
            return True
        else:
            return await interaction.response.send_message("You cannot take part in this game.", ephemeral=True)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        return await self.message.edit("No one clicked on a button for a long time. Timeout reached.", view=self)
#==================================