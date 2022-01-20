import discord


class RockPaperScissorsWithComputer(discord.ui.View):
    lose_colour = 0xfc0335 # red
    win_colour = 0x03fc62 # green 
    Tie_colour = 0xfcfc03 # yellow

    def __init__(self, ctx, bot_move):
        super().__init__()
        self.timeout = 30
        self.ctx = ctx
        self.bot_move = bot_move
        self.embed_colour = None
        # print(self.bot_move)


    async def interaction_check(self, interaction: discord.Interaction):
        return (interaction.user.id == self.ctx.author.id)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        self.stop()
        return await self.message.edit(f"{self.ctx.author.name} didn't reply in time.", view=self)

    def check_for_win(self, user_move, comp_move):
        win_content = f"You won! Bot chose {comp_move}. You chose {user_move}."
        lose_content = f"You lost! Bot chose {comp_move}. You chose {user_move}."

        if user_move == comp_move:
            return f"Its a tie. Bot chose {comp_move}. You  chose {user_move}.", self.Tie_colour

        if user_move == "rock":
            if comp_move == "paper":
                return lose_content, self.lose_colour
            if comp_move == "scissors":
                return win_content, self.win_colour

        if user_move == "paper":
            if comp_move == "rock":
                return win_content, self.win_colour
            if comp_move == "scissors":
                return lose_content, self.lose_colour

        if user_move == "scissors":
            if comp_move == "rock":
                return lose_content, self.lose_colour
            if comp_move == "paper":
                return win_content, self.win_colour

    @discord.ui.button(label="rock", style=discord.ButtonStyle.grey, emoji="\U0000270a")
    async def comp_rock_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        content, colour = self.check_for_win("rock", self.bot_move)
        await interaction.response.edit_message(content=None, embed=discord.Embed(title=f"{self.ctx.author.name}'s game of rock paper and scissors", description=content, colour=colour))
        self.stop()

    @discord.ui.button(label="paper", style=discord.ButtonStyle.green, emoji="\U0000270b")
    async def comp_paper_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        content, colour = self.check_for_win("paper", self.bot_move)
        await interaction.response.edit_message(content=None, embed=discord.Embed(title=f"{self.ctx.author.name}'s game of rock paper and scissors", description=content, colour=colour))
        self.stop()

    @discord.ui.button(label="scissors", style=discord.ButtonStyle.red, emoji="\U0000270c")
    async def comp_scissors_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        content, colour = self.check_for_win("scissors", self.bot_move)
        await interaction.response.edit_message(content=None, embed=discord.Embed(title=f"{self.ctx.author.name}'s game of rock paper and scissors", description=content, colour=colour))
        self.stop()

