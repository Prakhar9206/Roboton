import discord
import akinator

# akinator
class aki_view(discord.ui.View):
    def __init__(self, ctx, aki):
        super().__init__()
        self.ctx = ctx
        self.timeout = 60
        self.aki = aki


    async def interaction_check(self, interaction: discord.Interaction):
        return (interaction.user.id == self.ctx.author.id)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        return await self.message.edit("You did not respond in time! Timeout reached.", view=self)

    async def update(self, question, interaction):
        embed = discord.Embed(title="Akinator")
        embed.description = question

        await interaction.response.edit_message(embed=embed)

    async def disable_buttons(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    @discord.ui.button(label="yes", style=discord.ButtonStyle.green)
    async def yes_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = await self.aki.answer("yes")
        if self.aki.progression >= 80:
            await self.aki.win()
            em = discord.Embed(title=f"{self.aki.first_guess['name']}")
            em.description = f"{self.aki.first_guess['description']}?"
            em.set_image(url=self.aki.first_guess['absolute_picture_path'])
            await interaction.response.edit_message(embed=em)
            await self.disable_buttons()
            self.stop()
            return
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="no", style=discord.ButtonStyle.red)
    async def no_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = await self.aki.answer("no")
        if self.aki.progression >= 80:
            await self.aki.win()
            em = discord.Embed(title=f"{self.aki.first_guess['name']}")
            em.description = f"{self.aki.first_guess['description']}"
            em.set_image(url=self.aki.first_guess['absolute_picture_path'])
            await interaction.response.edit_message(embed=em)
            await self.disable_buttons()
            self.stop()
            return
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="idk", style=discord.ButtonStyle.blurple)
    async def idk_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = await self.aki.answer("idk")
        if self.aki.progression >= 80:
            await self.aki.win()
            em = discord.Embed(title=f"{self.aki.first_guess['name']}")
            em.description = f"{self.aki.first_guess['description']}"
            em.set_image(url=self.aki.first_guess['absolute_picture_path'])
            await interaction.response.edit_message(embed=em)
            await self.disable_buttons()
            self.stop()
            return
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="probably", style=discord.ButtonStyle.grey)
    async def probably_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = await self.aki.answer("p")
        if self.aki.progression >= 80:
            await self.aki.win()
            em = discord.Embed(title=f"{self.aki.first_guess['name']}")
            em.description = f"{self.aki.first_guess['description']}"
            em.set_image(url=self.aki.first_guess['absolute_picture_path'])
            await interaction.response.edit_message(embed=em)
            await self.disable_buttons()
            self.stop()
            return
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="probably not", style=discord.ButtonStyle.grey)
    async def probablyNot_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = await self.aki.answer("pn")
        if self.aki.progression >= 80:
            await self.aki.win()
            em = discord.Embed(title=f"{self.aki.first_guess['name']}")
            em.description = f"{self.aki.first_guess['description']}"
            em.set_image(url=self.aki.first_guess['absolute_picture_path'])
            await interaction.response.edit_message(embed=em)
            await self.disable_buttons()
            self.stop()
            return
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="back", style=discord.ButtonStyle.red)
    async def back_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        try:
            question = await self.aki.back()
        except akinator.CantGoBackAnyFurther:
            question = "Can't go back!"
            
        await self.update(question=question, interaction=interaction)

    @discord.ui.button(label="End game", style=discord.ButtonStyle.red)
    async def end_callback(self, button : discord.ui.Button, interaction : discord.Interaction):
        question = "The game is ended"
            
        await self.update(question=question, interaction=interaction)
        await self.disable_buttons()
        self.stop()
#==================================