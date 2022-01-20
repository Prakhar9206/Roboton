import discord
from discord.ext import commands


class RockPaperScissorsWithMember(discord.ui.View):

    lose_colour = 0xfc0335 # red
    win_colour = 0x03fc62 # green 
    Tie_colour = 0xfcfc03 # yellow

    def __init__(self, ctx: commands.Context, member: discord.Member):
        super().__init__()
        self.timeout = 30
        self.ctx = ctx
        self.member = member
        self.embed_colour = None
        self.user_move = None
        self.member_move = None
        self.winner = None
        self.content = None

    async def interaction_check(self, interaction: discord.Interaction):
        return (interaction.user.id == self.ctx.author.id) or (interaction.user.id == self.member.id)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        self.stop()
        memberWhoDidntClick = self.ctx.author if self.user_move is None else self.member
        return await self.message.edit(f"{memberWhoDidntClick} didn't press any button. Timeout", view=self)

    def check_for_win(self, user_move, member_move):
        
        if user_move == member_move:
            self.content =  f"Its a tie.\n{self.ctx.author} chose {user_move}.\n{self.member} chose {member_move}."
            self.stop()

        elif user_move == "rock":
            if member_move == "scissors":
                self.winner = self.ctx.author
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()
            if member_move == "paper":
                self.winner = self.member
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()

        elif user_move == "paper":
            if member_move == "rock":
                self.winner = self.ctx.author
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()
            if member_move == "scissors":
                self.winner = self.member
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()

        elif user_move == "scissors":
            if member_move == "rock":
                self.winner = self.member
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()
            if member_move == "paper":
                self.winner = self.ctx.author
                self.content = f"{self.winner} won.\n{self.ctx.author} chose {self.user_move}.\n{self.member} chose {self.member_move}."
                self.stop()


    @discord.ui.button(label="rock", style=discord.ButtonStyle.grey, emoji="\U0000270a")
    async def member_rock_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            self.user_move = "rock"
        elif interaction.user.id == self.member.id:
            self.member_move = "rock"
        
        await interaction.response.send_message("You selected rock", ephemeral=True)
        self.check_for_win(self.user_move, self.member_move)

    @discord.ui.button(label="paper", style=discord.ButtonStyle.green, emoji="\U0000270b")
    async def member_paper_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            self.user_move = "paper"
        elif interaction.user.id == self.member.id:
            self.member_move = "paper"
        
        await interaction.response.send_message("You selected paper", ephemeral=True)
        self.check_for_win(self.user_move, self.member_move)

    @discord.ui.button(label="scissors", style=discord.ButtonStyle.red, emoji="\U0000270c")
    async def member_scissors_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            self.user_move = "scissors"
        elif interaction.user.id == self.member.id:
            self.member_move = "scissors"
        
        await interaction.response.send_message("You selected scissors", ephemeral=True)
        self.check_for_win(self.user_move, self.member_move)