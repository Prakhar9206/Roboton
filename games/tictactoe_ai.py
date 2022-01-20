import discord
from discord.ext import commands
import random
from typing import List
from numpy import inf as infinity

# computer tictactoe
class COMP_TicTacToeButton(discord.ui.Button):
    def __init__(self, column: int, row: int, ctx=None, member=None):
        super().__init__(style=discord.ButtonStyle.grey, label='⠀', row=row)
        self.column = column
        self.row = row
        self.ctx = ctx
        self.member = member


    async def callback(self, interaction: discord.Interaction):
        view: COMP_tictactoe = self.view
        if view.isValidMove(self.row, self.column):
            view.board[self.row][self.column] = view.human
            self.label = view.human_plays_as
            self.style = discord.ButtonStyle.red if view.human_plays_as == "X" else discord.ButtonStyle.green
            self.disabled = True
            view.update_player()
            view.update_embed()

            winner = view.get_board_winner()
            if winner is not None:
                if winner == view.X_player:
                    content = f"{view.ctx.author.name} vs {view.member.name} ({view.difficulty})\n__{view.X_player.name} won__!"
                    colour = view.X_colour
                elif winner == view.O_player:
                    content = f"{view.ctx.author.name} vs {view.member.name} ({view.difficulty})\n__{view.O_player.name} won__"
                    colour = view.O_colour
                else:
                    content = f"{view.ctx.author.name} vs {view.member.name} ({view.difficulty})\n__It's a tie!__"
                    colour = view.Tie_colour

                for child in view.children:
                    child.disabled = True
                view.stop()


                em = view.game_embed
                em.colour = colour
                em.title = content
                return await interaction.response.edit_message(embed=em, view=view)
                
            
            await interaction.response.edit_message(embed=view.game_embed, view=view)
            view.processing = True
            await view.ai_turn()
        else:
            await interaction.response.defer()
#==================================


class COMP_tictactoe(discord.ui.View):

    children: List[COMP_TicTacToeButton]

    X_colour = 0xfc0335 # red
    O_colour = 0x03fc62 # green 
    Tie_colour = 0xfcfc03 # yellow

    def __init__(self, ctx, member, message, difficulty="hard"):

        super().__init__()
        self.ctx = ctx
        self.member = member # this is just the bot member
        self.message = message
        self.difficulty = difficulty
        self.timeout = 90
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        self.comp = random.choice([1, -1])
        self.human = random.choice([1, -1])
        while self.comp == self.human:
            self.human = random.choice([1, -1])
        # this is the worst thing I ever did
        if self.comp == 1:
            self.comp_plays_as = "X"
        else:
            self.comp_plays_as = "O"

        if self.human == 1:
            self.human_plays_as = "X"
        else:
            self.human_plays_as = "O"

        self.X_player = self.member if self.comp == 1 else self.ctx.author
        self.O_player = self.member if self.comp == -1 else self.ctx.author

        self.current_player = self.X_player
        self.winner = None

        self.game_embed = discord.Embed(title=f"{self.ctx.author.name} vs {self.member.name} ({self.difficulty})\n__{self.current_player.name}'s turn__", colour=self.X_colour)

        self.processing = False

        for row in range(3):
            for column in range(3):
                self.add_item(COMP_TicTacToeButton(column, row, self.ctx, self.member))

        if self.current_player == self.member:
            self.processing = True

    async def interaction_check(self, interaction: discord.Interaction):
        if (interaction.user.id == self.ctx.author.id) and (self.processing is False):
            return True
        else:
            await interaction.response.defer()
            return False

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit("You did not click any button for a long time. Timeout reached", view=self)

    def update_embed(self):
        self.game_embed.title = f"{self.ctx.author.name} vs {self.member.name} ({self.difficulty})\n__{self.current_player.name}'s turn__"

        if self.current_player == self.O_player:
            self.game_embed.colour = self.O_colour
            
        elif self.current_player == self.X_player:
            self.game_embed.colour = self.X_colour

        elif self.winner == self.X_player:
            self.game_embed.colour = self.X_colour

        elif self.winner == self.O_player:
            self.game_embed.colour = self.O_colour

        elif len(self.empty_cells()) == 0:
            self.game_embed.colour = self.Tie_colour
        
    def update_player(self):
        if self.winner is None:
            if self.current_player == self.X_player:
                self.current_player = self.O_player
            elif self.current_player == self.O_player:
                self.current_player = self.X_player


    def empty_cells(self, state=None):
        if state is None:
            empty_cells_list = []
            for row in range(3):
                for column in range(3):
                    if self.board[row][column] == 0:
                        empty_cells_list.append([row, column])
            return empty_cells_list
        elif state is not None:
            empty_cells_list = []
            for row in range(3):
                for column in range(3):
                    if state[row][column] == 0:
                        empty_cells_list.append([row, column])
            return empty_cells_list

    def isValidMove(self, row, column) -> bool:
        return self.board[row][column] == 0

    async def insert_into(self, row, column, player):
        self.board[row][column] = player
        # pprint(self.children)
        # print("===============================================")
        # print(self.board[0])
        # print(self.board[1])
        # print(self.board[2])

        button_index = (row * 3) + column
        button: discord.ui.Button = self.children[button_index]
        button.label = self.comp_plays_as
        button.disabled = True
        button.style = discord.ButtonStyle.red if self.comp_plays_as == "X" else discord.ButtonStyle.green

        winner = self.get_board_winner()
        if winner is not None:
            if winner == self.X_player:
                content = f"{self.ctx.author.name} vs {self.member.name} ({self.difficulty})\n__{self.X_player.name} won__!"
                colour = self.X_colour
            elif winner == self.O_player:
                content = f"{self.ctx.author.name} vs {self.member.name} ({self.difficulty})\n__{self.O_player.name} won__"
                colour = self.O_colour
            else:
                content = f"{self.ctx.author.name} vs {self.member.name} ({self.difficulty})\n__It's a tie!__"
                colour = self.Tie_colour

            for child in self.children:
                child.disabled = True

            self.stop()


            em = self.game_embed
            em.colour = colour
            em.title = content
            return await self.message.edit(embed=em, view=self)

        self.update_player()
        self.update_embed()
        await self.message.edit(embed=self.game_embed, view=self)
        self.processing = False

    def get_board_winner(self, state=None):
        """Checks whether human or comp wins for a state.
        Also checks if it is a tie.
        Othewise returns None
        """
        if state is None:
            state = self.board


        for across in state:
            value = sum(across)
            if value == 3:
                return self.X_player
            elif value == -3:
                return self.O_player

        # Check vertical
        for line in range(3):
            value = state[0][line] + state[1][line] + state[2][line]
            if value == 3:
                return self.X_player
            elif value == -3:
                return self.O_player

        # Check diagonals
        diag = state[0][2] + state[1][1] + state[2][0]
        if diag == 3:
            return self.X_player
        elif diag == -3:
            return self.O_player

        diag = state[0][0] + state[1][1] + state[2][2]
        if diag == 3:
            return self.X_player
        elif diag == -3:
            return self.O_player

        # If we're here, we need to check if a tie was made
        if all(i != 0 for row in state for i in row):
            return "Tie"

        return None

    def isMovesLeft(self, state=None):
        """Checks if there are empty squares available\n
        It can take an optional state.
        Defaults to the board
        """
        if state is None:
            state = self.board
            if self.winner is None:
                for row in self.board:
                    for block in row:
                        if block == 0:
                            return True
            return False

        elif state is not None:
            if self.winner is None:
                for row in state:
                    for block in row:
                        if block == 0:
                            return True
            return False

    def game_over(self, state):
        """Checks if the game is over.\n
        Either is a player wins or a draw is made\n
        Return True if game is over\n
        Else returns False
        """
        winner = self.get_board_winner(state)
        if (winner == self.X_player) or (winner == self.O_player):
            return True
        if self.isMovesLeft():
            return False
        return True

    def evaluate(self, state) :
        """
        Returns 10 if computer is winning.\n
        Returns -10 if human is winning.\n
        Returns 0 otherwise.
        """
        winner = self.get_board_winner(state)
        if winner == self.X_player:
            return 10
        elif winner == self.O_player:
            return -10

        return 0

    def minimax(self, state, player, isMaximizing, alpha, beta):
        score = self.evaluate(state)
        # If Maximizer has won the game return his/her evaluated score
        if (score == 10) :
            return score

        # If Minimizer has won the game return his/her evaluated score
        if (score == -10) :
            return score

        # If there are no more moves and no winner then it is a tie
        if (self.isMovesLeft(state) is False) :
            return 0

        # maximizer player's turn
        if isMaximizing: # x
            bestScore = -infinity
            for cell_coords in self.empty_cells(state):
                self.board[cell_coords[0]][cell_coords[1]] = player

                score = self.minimax(state, -player, False, alpha, beta)
                self.board[cell_coords[0]][cell_coords[1]] = 0

                bestScore = max(bestScore, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return bestScore

        # minimizer player's turn
        if isMaximizing is False: # o
            bestScore = infinity
            for cell_coords in self.empty_cells(state):
                self.board[cell_coords[0]][cell_coords[1]] = player

                score = self.minimax(state, -player, True, alpha, beta)
                # undo the move
                self.board[cell_coords[0]][cell_coords[1]] = 0

                bestScore = min(bestScore, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return bestScore

    def findBestMove(self, player):
        bestMove = [-1, -1]

        if self.comp_plays_as == "X":
            bestScore = -infinity
            # if len(self.empty_cells()) == 9: # small hack
            #     bestMove = [0,0]
            #     return bestMove
            for cell_coords in self.empty_cells():

                self.board[cell_coords[0]][cell_coords[1]] = player
                score = self.minimax(self.board, -player, False, -infinity, infinity)
                # undo move
                self.board[cell_coords[0]][cell_coords[1]] = 0
                if score > bestScore: # maximizing
                    bestScore = score
                    bestMove = [cell_coords[0], cell_coords[1]]
            
            return bestMove

        elif self.comp_plays_as == "O":
            bestScore = infinity
            # if len(self.empty_cells()) == 8: # small hack
            #     bestMove = [1,1]
            #     return bestMove

            for cell_coords in self.empty_cells():

                self.board[cell_coords[0]][cell_coords[1]] = player
                score = self.minimax(self.board, -player, True, -infinity, infinity)
                # undo move
                self.board[cell_coords[0]][cell_coords[1]] = 0
                if score < bestScore: # minimizing
                    bestScore = score
                    bestMove = [cell_coords[0], cell_coords[1]]

            return bestMove

    async def ai_turn(self):
        if self.difficulty in ("hard", "h"):
            # we have 100% chance of playing best move
            move = self.findBestMove(self.comp)

        elif self.difficulty in ("medium", "m"):
            # we have 65% chance of playing best move
            probability = random.randint(1, 100)
            if probability > 65: # 35% chance of making random move
                move = random.choice(self.empty_cells())
            else:
                move = self.findBestMove(self.comp)

        elif self.difficulty in ("easy", "e"):
            # we have 30% chance of playing best move
            probability = random.randint(1, 100)
            if probability > 30: # 70% chance of making random move
                move = random.choice(self.empty_cells())
            else:
                move = self.findBestMove(self.comp)

        row = move[0]
        column = move[1]
        await self.insert_into(row, column, self.comp)
#==================================