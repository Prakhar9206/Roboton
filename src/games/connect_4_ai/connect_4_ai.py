import discord
from discord.ext import commands
import random
import textwrap
from typing import List, Tuple
from numpy import inf as infinity
import asyncio


# computer connect 4
class COMP_connect_4_buttons(discord.ui.Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.green, label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: COMP_connect_4_view = self.view
        column = (int(self.label)-1)
        confirm = view.check_if_valid(column) # counting begins from 0
        if confirm is True:
            row = view.get_next_row(column)

            if interaction.user.id == view.red.id:
                view.insert_to(row, column, "red")
            elif interaction.user.id == view.yellow.id:
                view.insert_to(row, column, "yellow")

            view.check_for_winning()
            embedAndView = view.prepare_edit()
            embed: discord.Embed = embedAndView[0]
            embed.colour = view.update_embed_colour()
            _view = embedAndView[1]
            await interaction.followup.edit_message(view.message.id, embed=embed, view=_view)
            if view.winner is None:
                view.processing = True
                await self.view.ai_turn()
            
        else:
            await interaction.followup.send_message(view.message.id, "That column is full! Select some other column.", ephemeral=True)
            self.disabled = True


class COMP_connect_4_view(discord.ui.View):

    HEIGHT = 6
    WIDTH = 7
    RED_EMOJI = '🔴'
    YELLOW_EMOJI = '🟡'
    BLUE_EMOJI = '⏺️'
    RED_COLOUR = 0xfc0335 # red
    YELLOW_COLOUR = 0xfcfc03 # yellow
    TIE_COLOUR = 0xff9a1f

    # yellow will be -1 and red will be 1

    def __init__(self, ctx: commands.Context, member: discord.Member, message: discord.Message, difficulty: str = "hard"):
        super().__init__()
        self.ctx = ctx
        self.timeout = 60
        self.member = member
        self.message = message
        self.difficulty = difficulty
        self.processing: bool = False # bot is not processing its moves
        self.total_games_searched = 0
        self.total_moves_played = 0

        self.board = [[0 for y in range(self.WIDTH)] for x in range(self.HEIGHT)]
        self.numbers_emojis = [
            "1️⃣",
            "2️⃣",
            "3️⃣",
            "4️⃣",
            "5️⃣",
            "6️⃣",
            "7️⃣",
            "8️⃣",
            "9️⃣",
            "🔟",
        ]
        
        self.red = random.choice([ctx.author, member])
        self.yellow = random.choice([ctx.author, member])
        while self.red == self.yellow:
            self.yellow = random.choice([ctx.author, member])

        if self.red.id == self.ctx.bot.user.id: # if red player is bot
            self.comp = 1 # red
            self.human = 2 # yellow
            self.comp_plays_as = "red"
            self.whoever_plays_1 = self.red
            self.human_plays_as = "yellow"
            self.whoever_plays_2 = self.yellow
        else: # if red player is not bot (it is yellow)
            self.comp = 2 # yellow
            self.human = 1 # red
            self.comp_plays_as = "yellow"
            self.whoever_plays_2 = self.yellow
            self.human_plays_as = "red"
            self.whoever_plays_1 = self.red


        # if self.comp == 1: # comp is red

        # else: # comp is yellow

        # if self.human == 1:
        #     self.human_plays_as = "red"
        # else:
        #     self.human_plays_as = "yellow"

        self.current_player = self.red
        self.winner = None
        self.match_is_draw = False

        self.content = textwrap.dedent(f"""\n
            {ctx.author} vs {member}
            {self.red} will play as {self.RED_EMOJI}
            {self.yellow} will play as {self.YELLOW_EMOJI}
            """)
        self.embed = discord.Embed(
            title = textwrap.dedent(f"""\n
            It is {self.current_player}'s turn.
            """))
        
        self.embed.description = self.convert_board_to_str()
        self.embed.colour = self.update_embed_colour()
        for i in range(self.WIDTH):
            self.add_item(COMP_connect_4_buttons(label = str(i+1)))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (interaction.user.id == self.current_player.id) and (self.processing is False):
            return True
        else:
            return False

    async def on_timeout(self):
        self.stop()
        self.disable_buttons()
        if self.current_player == self.red:
            self.embed.title = f"{self.red} didn't make any move since 1 minute.\n{self.yellow} won!"
            self.winner = self.yellow
        elif self.current_player == self.yellow:
            self.embed.title = f"{self.yellow} didn't make any move since 1 minute.\n{self.red} won!"
            self.winner = self.red
        

        self.embed.description = self.convert_board_to_str()
        self.embed.colour = self.update_embed_colour()
        return await self.message.edit(embed=self.embed, view=self)

    def update_embed_colour(self):
        if self.match_is_draw is True:
            return self.TIE_COLOUR

        elif self.winner == self.red:
            return self.RED_COLOUR

        elif self.winner == self.yellow:
            return self.YELLOW_COLOUR

        elif self.current_player == self.red:
            return self.RED_COLOUR

        elif self.current_player == self.yellow:
            return self.YELLOW_COLOUR

    def convert_board_to_str(self) -> str:
        string = ""
        for rows in self.board:
            for elem in rows:
                string += f"{elem} "
            string += "\n"

        string = string.replace("0", f"{self.BLUE_EMOJI}")
        string = string.replace("2", f"{self.YELLOW_EMOJI}")
        string = string.replace("1", f"{self.RED_EMOJI}")
        string += " ".join([str(self.numbers_emojis[i]) for i in range(self.WIDTH)])
        return string

    def disable_buttons(self):
        for btn in self.children:
            btn.disabled = True

    def enable_buttons(self):
        for column in range(self.WIDTH):
            check = self.check_if_valid(column)
            if check is True:
                button = self.children[column]
                button.disabled = False # enables

    def check_if_valid(self, column) -> bool:
        # we only check the first row
        if self.board[0][column] == 0:
            return True
        else:
            return False

    def isMovesLeft(self, state=None):
        """
        Checks if there are empty squares available\n
        It can take an optional state.
        Defaults to the board
        """
        if state is None:
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

    def get_next_row(self, column, state=None) -> int: # only called if there is atleast 1 space left in column
        if state is None:
            row_index = (len(self.board) -1) # if len is 7, max index will be 6
            for row in reversed(self.board):
                # print(f"row is {row_index} and column is {column}") # board.index breaks this
                if row[column] == 0:
                    return row_index
                row_index -= 1
        else:
            row_index = (len(state) -1) # if len is 7, max index will be 6
            for row in reversed(state):
                # print(f"row is {row_index} and column is {column}") # board.index breaks this
                if row[column] == 0:
                    return row_index
                row_index -= 1

    def insert_to(self, row: int, column: int, colour: str):
        if colour == "red":
            self.board[row][column] = 1
            self.current_player = self.yellow
        if colour == "yellow":
            self.board[row][column] = 2
            self.current_player = self.red
        self.total_moves_played += 1

    def check_for_winning(self):
        """checks if there is a winner. if winner found, edits self.winner and stops the view. returns nothing"""

        state = self.board

        players = (1,2)
        # check horizontal
        for column in range(self.WIDTH -3): # col count
            for row in range(self.HEIGHT): # row count
                # print("================")
                # print(f'row {row}, column {column}')
                # print(state[row][column])
                # print(state[row][column+1])
                # print(state[row][column+2])
                # print(state[row][column+3])
                # print("=====================")
                to_be_added = [state[row][column], state[row][column +1], state[row][column +2], state[row][column +3]]
                
                if sum(to_be_added) == 8: # 8 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == 4: #4 is for red
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        self.winner = self.red
                        self.disable_buttons()
                        self.stop()
                        return


        # check vertical
        for column in range(self.WIDTH):
            for row in range(self.HEIGHT -3): # row is int here
                to_be_added = [state[row][column], state[row+1][column], state[row+2][column], state[row+3][column]]
                
                if sum(to_be_added) == 8: # 8 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == 4: #4 is for red
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        self.winner = self.red
                        self.disable_buttons()
                        self.stop()
                        return

        # check diagonals \\\
        for column in range(self.WIDTH -3):
            for row in range(self.HEIGHT -3):
                to_be_added = [state[row][column], state[row+1][column+1], state[row+2][column+2], state[row+3][column+3]]
                
                if sum(to_be_added) == 8: # 8 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == 4: #4 is for red
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        self.winner = self.red
                        self.disable_buttons()
                        self.stop()
                        return

        # check diagonals ///
        for column in range(self.WIDTH - 3):
            for row in range(3, self.HEIGHT):
                to_be_added = [state[row][column], state[row-1][column+1], state[row-2][column+2], state[row-3][column+3]]

                if sum(to_be_added) == 8: # 8 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == 4: #4 is for red
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        self.winner = self.red
                        self.disable_buttons()
                        self.stop()
                        return

        # we need to see if its a draw and all columns are filled
        if all(i != 0 for row in self.board for i in row):
            self.match_is_draw = True
            self.disable_buttons()
            self.stop()
            return

    def prepare_edit(self):
        if self.match_is_draw is True:
            self.embed.title = "It is a tie!"

        elif self.winner is None:
            self.embed.title = f"It is {self.current_player}'s turn."
        elif self.winner is not None: # we have a winner
            self.embed.title = f"*{self.winner}* won!"
            self.disable_buttons()

        self.embed.colour = self.update_embed_colour()
        self.embed.description = self.convert_board_to_str()

        for column in range(self.WIDTH):
            check = self.check_if_valid(column)
            if check is False:
                button = self.children[column]
                button.disabled = True
        
        if self.current_player.id == self.ctx.bot.user.id:
            self.disable_buttons() # disable all
        elif (self.current_player.id == self.ctx.author.id) and (self.winner is None):
            self.enable_buttons() # same as above for loop but it enables buttons if their column is not full

        return [self.embed, self]

    #------------ getting moves----------------

    def get_possible_columns(self, state: List[List[int]] =None) -> List[int]:
        """returns all the possible columns which are empty"""
        if state is None:
            state = self.board

        empty_columns = []
        current_col_index = 0
        for col in state[0]:
            if col == 0:
                empty_columns.append(current_col_index)
            current_col_index += 1
        return empty_columns

    def get_sorted_columns(self, state) -> List[int]:
        """Returns a list of columns in a sorted manner from best to worst (center first, edges last)"""
        if state is None:
            state = self.board

        # indexes of columns
        sorted_columns: List[int] = [] # 3,2,4,0,1,5,6

        center_col = 3 if state[0][3] == 0 else None
        left_center_col = 2 if state[0][2] == 0 else None
        right_center_col = 4 if state[0][4] == 0 else None

        for col in (center_col, left_center_col, right_center_col):
            if col is not None:
                sorted_columns.append(col)

        unsorted_columns = self.get_possible_columns() # 0,1,2,3,4,5,6
        for col in unsorted_columns:
            if col not in sorted_columns:
                sorted_columns.append(col)
        return sorted_columns

    def get_possible_moves(self, state=None) -> List[Tuple[int, int]]:
        """Returns a list containing tuple(row, column) of all possible moves"""
        if state is None:
            state = self.board

        moves: List[Tuple[int, int]] = []
        for col in self.get_sorted_columns(state):
            row = self.get_next_row(col, state)
            moves.append((row, col))
        return moves

    #------------ minimax----------------

    def is_winning_move(self, state, player: int):
        """checks if there is a winner in the state. Return true if found. False if not found"""
        piece = (4 * player)
        # check horizontal ---
        for column in range(self.WIDTH -3): # col count
            for row in range(self.HEIGHT): # row count # if len= 7, range will be 0-3
                to_be_added = [state[row][column], state[row][column +1], state[row][column +2], state[row][column +3]]
                if sum(to_be_added) == piece:
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        return True

        # check vertical |||
        for column in range(self.WIDTH):
            for row in range(self.HEIGHT -3): # row is int here
                to_be_added = [state[row][column], state[row+1][column], state[row+2][column], state[row+3][column]]
                if sum(to_be_added) == piece:
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        return True

        # check diagonals \\\
        for column in range(self.WIDTH -3):
            for row in range(self.HEIGHT -3):
                to_be_added = [state[row][column], state[row+1][column+1], state[row+2][column+2], state[row+3][column+3]]
                if sum(to_be_added) == piece:
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        return True

        # check diagonals ///
        for column in range(self.WIDTH - 3):
            for row in range(3, self.HEIGHT):
                if sum(to_be_added) == piece:
                    if to_be_added[0] == to_be_added[1] == to_be_added[2] == to_be_added[3]:
                        return True
        return False

    def evaluate(self, line: List, piece: int):
        """Evaluates only a given line of 4 cells. Line will be list of cells from board with their value"""
        EMPTY = 0
        score = 0
        opp_piece = self.human
        if piece == self.human:
            opp_piece = self.comp

        if line.count(piece) == 4:
            score += 10000
        elif line.count(piece) == 3 and line.count(EMPTY) == 1:
            score += 5
        elif line.count(piece) == 2 and line.count(EMPTY) == 2:
            score += 2

        elif line.count(opp_piece) == 3 and line.count(EMPTY) == 1:
            score -= 4

        return score

    def score_position(self, state: List[List[int]], piece: int):
        """returns static evaluation of a given state"""
        score = 0

        # center column
        center_col = [row[3] for row in state]
        # for row in state:
        #     center_col.append(row[3])
        center_count = center_col.count(piece)
        score += center_count * 3


        # check horizontal
        for column in range(self.WIDTH -3): # col count
            for row in range(self.HEIGHT): # row count
                to_be_added = [state[row][column], state[row][column +1], state[row][column +2], state[row][column +3]]
                score += self.evaluate(to_be_added, piece)


        # check vertical
        for column in range(self.WIDTH):
            for row in range(self.HEIGHT -3): # row is int here
                to_be_added = [state[row][column], state[row+1][column], state[row+2][column], state[row+3][column]]
                score += self.evaluate(to_be_added, piece)

        # check diagonals \\\
        for column in range(self.WIDTH -3):
            for row in range(self.HEIGHT -3):
                to_be_added = [self.board[row][column], self.board[row+1][column+1], self.board[row+2][column+2], self.board[row+3][column+3]]
                score += self.evaluate(to_be_added, piece)

        # check diagonals ///
        for column in range(self.WIDTH - 3):
            for row in range(3, self.HEIGHT):
                to_be_added = [self.board[row][column], self.board[row-1][column+1], self.board[row-2][column+2], self.board[row-3][column+3]]
                score += self.evaluate(to_be_added, piece)

        return score

    def findBestMove(self) -> Tuple[int, int]:
        """Return a list[row, column] of best move"""
        bestMove = (-1, -1)

        # maximizer's turn (always comp)
        bestScore = -infinity
        # self.depth_ = 0
        if self.total_moves_played > 30:
            self.depth_ = 13 # calculate all possible moves
        elif self.total_moves_played > 25:
            self.depth_ = 10
        elif self.total_moves_played > 20:
            self.depth_ = 8
        elif self.total_moves_played > 15:
            self.depth_ = 7
        elif self.total_moves_played > 6:
            self.depth_ = 6
        else:
            self.depth_ = 5

        print(f"depth = {self.depth_}, moves = {self.total_moves_played}")
        for cell_coords in self.get_possible_moves():
            r,c = cell_coords
            self.total_games_searched += 1

            self.board[r][c] = self.comp
            if self.is_winning_move(self.board, self.comp) or self.is_winning_move(self.board, self.human): # check one move wins
                # if a move is winning for us or our opponent, that is our best move
                return cell_coords

            score = self.minimax(self.board, self.depth_, False, -infinity, infinity) # calling for minimizer's turn
            # undo move
            self.board[r][c] = 0
            if score > bestScore: # maximizing
                bestScore = score
                bestMove = (r, c)
        
        return bestMove

    def is_terminal_node(self, state):
        """Tells if it is the last node. Either is someone has won or no moves are left"""
        return (self.is_winning_move(state, self.comp)) or (self.is_winning_move(state, self.human)) or (self.isMovesLeft(state) is False)

    def minimax(self, state: List[List[int]], depth: int, isMaximizing: bool, alpha, beta):
        # score = self.score_position(state, player)

        if self.is_terminal_node(state) or (depth == 0):
            if self.is_terminal_node(state):
                if self.is_winning_move(state, self.comp):
                    return (1000000000 + depth)
                elif self.is_winning_move(state, self.human):
                    return (-1000000000 - depth)

                else: # game over. no moves left
                    return 0
            else: # depth 0 reached
                score = self.score_position(state, self.comp)
                return score # player = piece

        # maximizer player's turn (always computer)
        if isMaximizing: # red
            bestScore = -infinity
            for cell_coords in self.get_possible_moves(state):
                row = cell_coords[0]
                col = cell_coords[1]
                assert row is not None
                assert col is not None
                self.total_games_searched += 1

                self.board[cell_coords[0]][cell_coords[1]] = self.comp

                score = self.minimax(state, depth-1, False, alpha, beta)
                self.board[cell_coords[0]][cell_coords[1]] = 0

                bestScore = max(bestScore, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return bestScore

        # minimizer player's turn (always human)
        if isMaximizing is False: # yellow
            bestScore = infinity
            for cell_coords in self.get_possible_moves(state):
                row = cell_coords[0]
                col = cell_coords[1]
                assert row is not None
                assert col is not None
                self.total_games_searched += 1

                self.board[cell_coords[0]][cell_coords[1]] = self.human

                score = self.minimax(state, depth-1, True, alpha, beta)
                # undo the move
                self.board[cell_coords[0]][cell_coords[1]] = 0

                bestScore = min(bestScore, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return bestScore

    async def ai_turn(self):
        loop: asyncio.AbstractEventLoop = self.ctx.bot.loop
        # raw_move = await self.findBestMove(self.comp)
        raw_move = await loop.run_in_executor(None, self.findBestMove)
        row = raw_move[0]
        column = raw_move[1]
        self.insert_to(row, column, self.comp_plays_as) # also updating the current player
        self.check_for_winning()
        raw_response = self.prepare_edit()
        # self.enable_buttons()
        await self.message.edit(embed=raw_response[0], view=self)
        # await self.ctx.send(f"computer searched {self.total_games_searched} games")
        self.total_games_searched = 0
        self.processing = False
#==================================
