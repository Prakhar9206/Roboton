import discord
from discord.ext import commands

# confirms
class confirm(discord.ui.View):
    def __init__(self, ctx, member):
        super().__init__()
        self.value = None
        self.timeout = 45
        self.ctx = ctx
        self.member = member

 
    async def interaction_check(self, interaction: discord.Interaction):
        return self.member.id == interaction.user.id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content= f"{self.member} did not react. Timeout", view=self)

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.edit(content="Starting the game", view=self.clear_items())
        self.value = True
        self.stop()

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.red)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.edit(content=f"{self.member} has declined.", view=self.clear_items())
        self.value = False
        self.stop()
#==================================

class just_confirm(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.value = None
        self.timeout = 45
        self.ctx = ctx

 
    async def interaction_check(self, interaction: discord.Interaction):
        return (self.ctx.author.id == interaction.user.id)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content= f"{self.ctx.author} did not react. Timeout", view=self)

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        
        await interaction.message.edit(content="Starting the game", view=self.clear_items())
        self.value = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):

        await interaction.message.edit(content=f"{self.ctx.author} Ok! Go read the rules by typing `{self.ctx.clean_prefix}help {self.ctx.command}` and play this game.", view=self.clear_items())
        self.value = False
        self.stop()
#==================================

class yes_no(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.value = None
        self.timeout = 45
        self.ctx = ctx


    async def interaction_check(self, interaction: discord.Interaction):
        return (self.ctx.author.id == interaction.user.id)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(content= f"{self.ctx.author} did not react. Timeout", view=self)

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        
        await interaction.message.edit(content="Starting the game", view=self.clear_items())
        self.value = True
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):

        await interaction.message.edit(content=f"OK! You can play with someone else by typing {self.ctx.clean_prefix}{self.ctx.command} [member]", view=self.clear_items())
        self.value = False
        self.stop()
#==================================

class end_poll_confirm(discord.ui.View):
    """This is for creator of poll only"""
    def __init__(self, creator: int):
        super().__init__()
        self.value = None
        self.timeout = 60
        self.creator = creator # ctx.author.id

 
    async def interaction_check(self, interaction: discord.Interaction):
        return self.creator == interaction.user.id


    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Poll ended", view=self.clear_items())
        self.value = True
        self.stop()

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.red)
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"Ok. You can end the poll whenever you wish.", view=self.clear_items())
        self.value = False
        self.stop()