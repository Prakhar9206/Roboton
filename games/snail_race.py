import discord
from discord.ext import commands
import random
import textwrap

# snailrace
class snailrace(discord.ui.View):
    def __init__(self, ctx: commands.Context, member: discord.Member):
        super().__init__()
        self.timeout = 30
        self.ctx = ctx
        self.member = member
        self.message: discord.Message

        self.green_snail_emoji = "<:green_snail:868487030424883241>"
        self.yellow_snail_emoji = "<:yellow_snail:868487066982424646>"
        self.finishline_emoji = "<:finishline:868517091756630056>"
        self.blueline_emoji = "<:BlueLine:868520474127249468>"
        self.green_position = 0
        self.yellow_position = 0 # 0                 1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17
        self.green_track = [self.green_snail_emoji, "=","=","=","=","=","=","=","=","=","=","=","=","=","=","=","=",self.finishline_emoji]
        self.yellow_track = [self.yellow_snail_emoji, "=","=","=","=","=","=","=","=","=","=","=","=","=","=","=","=",self.finishline_emoji]
        self.winner = None

        
        self.green_member = random.choice([ctx.author , member])
        self.yellow_member = random.choice([ctx.author , member])

        while self.green_member == self.yellow_member:
            self.yellow_member = random.choice([ctx.author , member])

        self.game_embed = discord.Embed()
        self.update_embed()

    async def interaction_check(self, interaction: discord.Interaction):
        return ((interaction.user.id == self.ctx.author.id) or (interaction.user.id == self.member.id)) and (self.winner is None)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        self.message.edit("No one reacted. Timeout", view=self)
        return await self.ctx.reply("No one reacted. Timeout")

    def update_embed(self):
        self.game_embed = discord.Embed(title=f"Race between {self.ctx.author.name} and {self.member.name}")
        self.game_embed.description = textwrap.dedent(f"""\n
        {self.green_member} will play as {self.green_snail_emoji}
        {self.yellow_member} will play as {self.yellow_snail_emoji}


        {"".join(self.green_track)}
        {self.blueline_emoji * 9}
        {"".join(self.yellow_track)}
        """)

    async def edit_list(self, position, member_colour):
        """edits the track lists. requires a position and the green_member or yellow_member"""
        if member_colour == self.green_member:
            self.green_track[position] = self.green_snail_emoji
            self.green_track[position - 1] = "="
            self.update_embed()
            
            
        elif member_colour == self.yellow_member:
            self.yellow_track[position] = self.yellow_snail_emoji
            self.yellow_track[position - 1] = "="
            self.update_embed()
            


    @discord.ui.button(label="Move", style=discord.ButtonStyle.green)
    async def move_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id == self.green_member.id:
            self.green_position += 1
            # 17 is finish line
            if self.green_position == 17:
                await self.edit_list(self.green_position, self.green_member)
                self.game_embed.title = f"{self.green_member} won!"

                button.disabled = True
                self.stop()
                await interaction.response.edit_message(content=None, embed=self.game_embed, view=self)
                
                self.winner = self.green_member
                

            else:
                await self.edit_list(self.green_position, self.green_member)
                await interaction.response.edit_message(content=None, embed=self.game_embed, view=self)

        elif interaction.user.id == self.yellow_member.id:
            self.yellow_position += 1
            if self.yellow_position == 17:
                await self.edit_list(self.yellow_position, self.yellow_member)
                self.game_embed.title = f"{self.yellow_member} won!"
                await interaction.response.edit_message(content=None, embed=self.game_embed, view=self)

                button.disabled = True
                self.stop()
                self.winner = self.yellow_member
                
            else:
                await self.edit_list(self.yellow_position, self.yellow_member)
                await interaction.response.edit_message(content=None, embed=self.game_embed)      
#==================================