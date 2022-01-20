import discord
import random
import textwrap



# 2 player connect 4
class connect_4_buttons(discord.ui.Button):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.green, label=label)

    async def callback(self, interaction: discord.Interaction):
        view: connect_4_view = self.view
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
            embed = embedAndView[0]
            embed.colour = view.update_embed_colour()
            _view = embedAndView[1]
            
            await interaction.response.edit_message(embed=embed, view=_view)
        else:
            await interaction.response.send_message("That column is full! Select some other column.", ephemeral=True)
            self.disabled = True


class connect_4_view(discord.ui.View):

    HEIGHT = 7
    WIDTH = 7
    RED_EMOJI = '🔴'
    YELLOW_EMOJI = '🟡'
    BLUE_EMOJI = '⏺️'
    RED_COLOUR = 0xfc0335 # red
    YELLOW_COLOUR = 0xfcfc03 # yellow
    TIE_COLOUR = 0xff9a1f

    # yellow will be -1 and red will be 1

    def __init__(self, ctx, member, message):
        super().__init__()
        self.ctx = ctx
        self.timeout = 60
        self.member = member
        self.message = message
        # self.board = numpy.zeros((self.HEIGHT, self.WIDTH))
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
        # self.alphabets = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
        
        self.red = random.choice([ctx.author, member])
        self.yellow = random.choice([ctx.author, member])
        while self.red == self.yellow:
            self.yellow = random.choice([ctx.author, member])

        self.current_player = random.choice([self.red, self.yellow])
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
            self.add_item(connect_4_buttons(label = str(i+1)))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.current_player.id

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
        string = string.replace("-1", f"{self.YELLOW_EMOJI}")
        string = string.replace("1", f"{self.RED_EMOJI}")
        string += " ".join([str(self.numbers_emojis[i]) for i in range(self.WIDTH)])
        return string

    def disable_buttons(self):
        for btn in self.children:
            btn.disabled = True

    def check_if_valid(self, column) -> bool:
        # we only check the first row
        if self.board[0][column] == 0:
            return True
        else:
            return False

    def get_next_row(self, column) -> int:
        row_index = (len(self.board) -1) # if len is 7, max index will be 6
        for row in reversed(self.board):
            # print(f"row is {row_index} and column is {column}") # board.index breaks this
            if row[column] == 0:
                return row_index
            row_index -= 1

    def insert_to(self, row: int, column: int, colour: str):
        if colour == "red":
            self.board[row][column] = 1
            self.current_player = self.yellow
        if colour == "yellow":
            self.board[row][column] = -1
            self.current_player = self.red

    def check_for_winning(self):
        # check horizontal
        for row in range(self.WIDTH):
            for column in range(self.HEIGHT -3): # if len= 7, range will be 0-3
                to_be_added = [self.board[row][column], self.board[row][column +1], self.board[row][column +2], self.board[row][column +3]]
                if sum(to_be_added) == 4: #4 is for red
                    self.winner = self.red
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == -4: #-4 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return

        # check vertical
        for row in range(self.WIDTH -3):
            for column in range(self.HEIGHT): # row is int here
                to_be_added = [self.board[row][column], self.board[row+1][column], self.board[row+2][column], self.board[row+3][column]]
                
                if sum(to_be_added) == 4: #4 is for red
                    self.winner = self.red
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == -4: #-4 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return

        # check diagonals \\\
        for column in range(self.HEIGHT -3):
            for row in range(self.WIDTH -3):
                to_be_added = [self.board[row][column], self.board[row+1][column+1], self.board[row+2][column+2], self.board[row+3][column+3]]
                
                if sum(to_be_added) == 4: #4 is for red
                    self.winner = self.red
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == -4: #-4 is for yellow
                    self.winner = self.yellow
                    self.disable_buttons()
                    self.stop()
                    return

        # check diagonals ///
        for column in range(self.WIDTH - 3):
            for row in range(3, self.HEIGHT):
                to_be_added = [self.board[row][column], self.board[row-1][column+1], self.board[row-2][column+2], self.board[row-3][column+3]]
                if sum(to_be_added) == 4: #4 is for red
                    self.winner = self.red
                    self.disable_buttons()
                    self.stop()
                    return
                elif sum(to_be_added) == -4: #-4 is for yellow
                    self.winner = self.yellow
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
        elif self.winner is not None:
            self.embed.title = f"*{self.winner}* won!"

        self.embed.colour = self.update_embed_colour()
        self.embed.description = self.convert_board_to_str()

        for column in range(self.WIDTH):
            check = self.check_if_valid(column)
            if check is False:
                button = self.children[column]
                button.disabled = True
        return [self.embed, self]
#==================================