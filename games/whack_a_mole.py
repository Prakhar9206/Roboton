import discord
from discord.ext import commands, tasks
import random
import asyncio


# whack a mole
class whack_a_mole_buttons(discord.ui.Button):
    dirt_emoji = "<:dirt:876833736610705469>"
    mole_emoji = "<:mole:876833644080144414>"
    def __init__(self, x, y, ctx: commands.Context, message):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", emoji=self.dirt_emoji, row=x)
        self.x = x
        self.y = y
        self.ctx = ctx
        self.message = message
        # self.view: whack_a_mole_view = self.view
        self.old_mole_position = None
        self.current_mole_position = int
        self.number_of_clicks = 0
        self.current_edit_loop = 0
        

    async def interaction_check(self, interaction: discord.Interaction):
        return (interaction.user.id == self.ctx.author.id)



    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: whack_a_mole_view = self.view
        clicked_button_position = view.children.index(self)
        
        if interaction.user == self.ctx.author:
            # self.number_of_clicks += 1
            returned_list = view.other_callback(clicked_button_position, view, button=self, number_of_clicks=self.number_of_clicks)
            new_view = returned_list[0]
            em = returned_list[1]
            await interaction.response.edit_message(embed=em, view=new_view)


class whack_a_mole_view(discord.ui.View):
    lose_colour = 0xfc0335 # red
    win_colour = 0x03fc62 # green 
    timeout_colour = 0xfcfc03 # yellow

    def __init__(self, ctx: commands.Context, message):
        super().__init__(timeout=15)
        # self.timeout = 15
        self.ctx = ctx
        self.message = message
        self.maximum_points = 20
        self.minimum_points = 15
        self.points = 0
        # board will be in this format = [
        #    row 0 [0, 1, 2, 3, 4],
        #    row 1 [5, 6, 7, 8, 9],
        #    row 2 [10, 11, 12, 13, 14],
        #    row 3 [15, 16, 17, 18, 19],
        #    row 4 [20, 21, 22, 23, 24],
        # ]
        for x in range(5):
            for y in range(5):
                self.wamb_inst = whack_a_mole_buttons(x, y, self.ctx, self.message)
                self.add_item(self.wamb_inst)
    
        self.edit_every_five_second.start()

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user == self.ctx.author

    async def on_timeout(self): # this never gets called
        # print("In timeout")
        for child in self.children:
            child.disabled = True
        
        self.stop()
        self.edit_every_five_second.cancel()
        em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
        em.description = f"**POINTS** : {self.points}/20\nTimeout"
        await self.message.edit(embed=em, view=self)
        # print("edited the message for timeout")
        return

    # new mole after every 5 seconds
    @tasks.loop(seconds=5, count=20) # automatically stops after given count
    async def edit_every_five_second(self, message=None):
        message = self.message

        # making a new mole
        
        if self.wamb_inst.old_mole_position is not None:
            # getting the button where the mole was earlier from children and changing old mole button
            self.wamb_inst.old_mole_button = self.children[self.wamb_inst.old_mole_position]
            self.wamb_inst.old_mole_button.emoji = self.wamb_inst.dirt_emoji
            self.wamb_inst.old_mole_button.style = discord.ButtonStyle.grey

                
        # making sure current_mole_position and old_mole_position are not same
        self.wamb_inst.current_mole_position = random.randint(0, 24)
        while self.wamb_inst.current_mole_position == self.wamb_inst.old_mole_position:
            self.wamb_inst.current_mole_position = random.randint(0, 24)
        
        self.wamb_inst.current_mole_button = self.children[self.wamb_inst.current_mole_position]
        self.wamb_inst.current_mole_button.emoji = self.wamb_inst.mole_emoji

        em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
        em.description = f"**POINTS** : {self.points}/20"

        # enabling our buttons and making them grey if they had a different colour
        for button in self.children:
            button.style = discord.ButtonStyle.grey
            button.disabled = False

        await message.edit(embed=em, view=self)
        self.wamb_inst.old_mole_position = self.wamb_inst.current_mole_position

        # disabling the buttons after 2.75 seconds. this means the mole will stay on screen for 1.75 seconds and then hide again
        await asyncio.sleep(2.5)
        for button in self.children:
            # button.disabled = True
            button.emoji = self.wamb_inst.dirt_emoji
        em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
        em.description = f"**POINTS** : {self.points}/20"
        await message.edit(embed=em, view=self)

        self.wamb_inst.current_edit_loop += 1
        if (self.wamb_inst.current_edit_loop == 5 and self.wamb_inst.number_of_clicks == 0) or (self.wamb_inst.current_edit_loop == 10 and self.wamb_inst.number_of_clicks <= 4):
            # print(self.wamb_inst.number_of_clicks)
            em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
            em.description = f"**POINTS** : {self.points}/20"
            em.colour = self.lose_colour
            await message.edit(content="Woops! You didn't click on any button. Timeout. Try to be quicker next time.",embed=em, view=self)
            self.edit_every_five_second.stop()
            self.stop()


    @edit_every_five_second.after_loop
    async def check_for_win(self):
        if self.points < 15:
            em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
            em.description = f"**POINTS** : {self.points}/{self.maximum_points}\nYou lost {self.ctx.author}\n"
            em.color = self.lose_colour
            if self.points < 6:
                em.description += f"You got {self.points}/20 points. Shame on you."
            elif self.points >= 6 and self.points <= 10:
                em.description += f"You got {self.points}/20 points. Try harder."
            elif self.points > 10 and self.points < 15:
                em.description += f"You got {self.points}/20 points. You were so close to winning. Try a little harder."
            
        elif self.points >= 15:
            em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
            em.description = f"**POINTS** : {self.points}/{self.maximum_points}\nYou won! {self.ctx.author}\n"
            em.color = self.win_colour
            if self.points == 15:
                em.description += "You just won with exactly 15 points. Maybe you can do better!"
            elif self.points == 16:
                em.description += "You just won with 1 extra point. Maybe you can do better!"
            elif self.points == 17:
                em.description += "Nice win. But you can still do better!"
            elif self.points == 18:
                em.description += "You got 18 points. Congrats! but you should aim for 20 points!"
            elif self.points == 19:
                em.description += "You were so close to getting 20/20. I am sure you can do it!"
            elif self.points == 20:
                em.description += "You got 20/20 ....?. What the heck! Was the game that easy?"

        for child in self.children:
            child.disabled = True
            self.stop()

        await self.message.edit(embed=em, view=self)
        
    
    def other_callback(self, clicked_button_position, view, button, number_of_clicks) -> discord.ui.View:
        for btn in self.children:
            btn.disabled = True
        # print(f"current mole position- {self.wamb_inst.current_mole_position} and click button position {clicked_button_position}")
        if self.wamb_inst.current_mole_position == clicked_button_position:
            # print("You clicked correct button")
            button.style = discord.ButtonStyle.green
            self.points += 1
            self.wamb_inst.number_of_clicks += 1
            if self.points == 20:
                em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
                em.description = f"**POINTS** : {self.points}/20"

            else:
                em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
                em.description = f"**POINTS** : {self.points}/20"

        else:
            button.style = discord.ButtonStyle.red
            em = discord.Embed(title=f"{self.ctx.author}'s game of whack-a-mole.")
            em.description = f"**POINTS** : {self.points}/20"
        return [self, em]
#==================================