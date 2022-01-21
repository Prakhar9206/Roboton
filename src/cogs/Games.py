import discord
from discord.ext import commands
import random
import asyncio
from akinator.async_aki import Akinator
from typing import Optional
from discord.ext.commands.cooldowns import BucketType
import asyncio

# importing confirms
from games.confirm_views import *


# importing games 
from games.rps import RockPaperScissorsWithMember
from games.rps_ai import RockPaperScissorsWithComputer
from games.akinator_ import aki_view
from games.snail_race import snailrace
from games.tictactoe import tictactoe
from games.tictactoe_ai import COMP_tictactoe
from games.whack_a_mole import whack_a_mole_view
from games.connect_4 import connect_4_view
from games.connect_4_ai.connect4cheat import COMP_connect_4_view
from games.match_tile import match_tile_view
from games.maze import _3dmazeView
from games.nim import NimView
from games.multiplayer_maze import ViewManager, _2dmazeView
import time

class Games(commands.Cog, name="Games"):
    """All the games commands."""
    def __init__(self,bot):
        self.bot = bot


    @commands.command(aliases=["rps", "rock_paper_scissor", "rock-paper-scissor"])
    async def rock_paper_scissors(self, ctx: commands.Context, member: discord.Member = None):
        """Play rock, paper, scissors with someone. Or if no one wants to play with you, you can also play with me :D"""

        # if no member is provided
        if member is None:
            member = "comp"
        if member == "comp" or member.id == self.bot.user.id:
            em = discord.Embed(title=f"{ctx.author.name}'s game of rock paper and scissors")
            em.description = "Click on your choice."
            em.color = ctx.author.colour
            comp_move = random.choice(["rock", "paper", "scissors"])
            rps_instance = RockPaperScissorsWithComputer(ctx=ctx, bot_move=comp_move)
            rps_instance.message = await ctx.send(embed=em, view=rps_instance)

            # if a member is provided

        else:
            if member.bot:
                return await ctx.send(f"Well bots can't play rock paper scissors cuz you will never hear back from them. But if you really want to play with bots, you can play with me by using `{ctx.clean_prefix}rps` or `{ctx.clean_prefix}rps @{self.bot.user}`")

            em = discord.Embed(title=f"Rock, Paper, Scissors\n{ctx.author.name} vs {member.name}")
            em.description = "Click on your choice."
            em.color = ctx.author.colour
            rps_instance = RockPaperScissorsWithMember(ctx, member)
            rps_instance.message = await ctx.send(embed=em, view=rps_instance)
            await rps_instance.wait()
            em = discord.Embed(title=f"Rock, Paper, Scissors\n{ctx.author.name} vs {member.name}")
            em.description = rps_instance.content
            em.color = ctx.author.colour
            await rps_instance.message.edit(embed=em, view=None)


    @commands.command()
    async def race(self, ctx, member : discord.Member = None):
        """Starts a snail race between two people."""
        
        if member is None:
            return await ctx.send("You didn't tell me which member to play with!")
        if member == ctx.author:
            return await ctx.send("You can't play with yourself")
        if member.bot:
            return await ctx.send("Dude.. bots can't play")

        confirm_view_obj = confirm(ctx=ctx, member=member)
        confirm_view_obj.message = await ctx.send(f"{member.mention}! {ctx.author.name} wants to have a race with you.", view=confirm_view_obj)
        await confirm_view_obj.wait()
        if confirm_view_obj.value:
            snail_view_obj = snailrace(ctx=ctx, member=member)
            
            snail_view_obj.message = await ctx.send(embed=snail_view_obj.game_embed, view=snail_view_obj)
            
    
    @commands.command(aliases=['ttt'])
    @commands.guild_only()
    async def tictactoe(self, ctx: commands.Context, member: Optional[discord.Member] = None, difficulty: str = "hard"):
        """Play a game of tic tac toe with someone.
        Type `<prefix>tictactoe [member]` to play with a member from the server.
        You can also type `<prefix>tictactoe [difficulty]` to play AI.
        Difficulty can be either `easy`, `medium` or `hard`.
        """
        if member is None or member == ctx.guild.me:
            if difficulty.lower() not in ("easy", "e", "medium", "m", "hard", "h"):
                return await ctx.send(f"No difficulty called {difficulty} was found. Difficulties can be either `easy`, `medium` or `hard`")
            view = yes_no(ctx)
            view.message = await ctx.send("Do you want to play with me?", view=view)
            await view.wait()
            if view.value:
                _difficulty = difficulty.lower()
                if _difficulty == "e":
                    difficulty = "easy"
                elif _difficulty == "m":
                    difficulty = "medium"
                elif _difficulty == "h":
                    difficulty = "hard"
                    
                comp_ttt = COMP_tictactoe(ctx, ctx.guild.me, view.message, difficulty.lower())
                await view.message.edit(embed=comp_ttt.game_embed, view=comp_ttt)
                
                if comp_ttt.current_player == ctx.guild.me:
                    await comp_ttt.ai_turn()
            

        elif member == ctx.author:
            return await ctx.send("You can't play with yourself")
        elif member.bot:
            return await ctx.send("Dude.. bots can't play")
        else:
            confirm_view_obj_1 = confirm(ctx=ctx, member=member)
            confirm_view_obj_1.message = await ctx.send(f"{member.mention}! {ctx.author.name} wants to play tic tac toe with you.", view=confirm_view_obj_1)
            await confirm_view_obj_1.wait()
            if confirm_view_obj_1.value:
                ttt_view_obj = tictactoe(ctx=ctx, member=member)
                ttt_view_obj.message = await ctx.send(embed=ttt_view_obj.game_embed, view=ttt_view_obj)
    

    @commands.command(name="akinator")
    @commands.max_concurrency(number=1, per=BucketType.default, wait=False)
    async def aki_start(self, ctx):
        """Starts a game of akinator!"""

        aki = Akinator()
        question = await aki.start_game(client_session=self.bot.aiohttp_session, child_mode=True)
        em = discord.Embed(title="Akinator", description=question)
        aki_view_inst = aki_view(ctx=ctx, aki=aki)
        aki_view.message = await ctx.send(embed=em, view=aki_view_inst)
        await aki_view_inst.wait()


    @commands.command(aliases=["wam"])
    async def whack_a_mole(self, ctx: commands.Context):
        """Play whack a mole. You win if you reach 15 points."""

        message = await ctx.send("Starting the game...")
        wam_inst = whack_a_mole_view(ctx=ctx, message=message)
        em = discord.Embed(title=f"{ctx.author}'s game of whack-a-mole.")
        em.description = f"**POINTS** : {wam_inst.points}/{wam_inst.maximum_points}"
        await asyncio.sleep(2)
        await message.edit(content=None, embed=em, view=wam_inst)


    @commands.command(aliases=["c4"])
    async def connect_4(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Play connect 4 with someone. You can also play with the AI by just typing `+c4`.
        You can learn how to play connect 4 from here https://www.wikihow.com/Play-Connect-4
        """

        if member is None or member == ctx.guild.me:
            # if difficulty.lower() not in ("easy", "e", "medium", "m", "hard", "h"):
            #     return await ctx.send(f"No difficulty called {difficulty} was found. Difficulties can be either `easy`, `medium` or `hard`")
            view = yes_no(ctx)
            view.message = await ctx.send("Do you want to play with me?", view=view)
            await view.wait()
            if view.value:
                # _difficulty = difficulty.lower()
                # if _difficulty == "e":
                #     difficulty = "easy"
                # elif _difficulty == "m":
                #     difficulty = "medium"
                # elif _difficulty == "h":
                #     difficulty = "hard"

                comp_c4 = COMP_connect_4_view(ctx, ctx.guild.me, view.message) #, difficulty.lower())
                if comp_c4.current_player == ctx.guild.me:
                    comp_c4.disable_buttons()

                await view.message.edit(embed=comp_c4.embed, view=comp_c4)
                
                if comp_c4.current_player == ctx.guild.me:
                    comp_c4.processing = True

                    await comp_c4.ai_turn()

        elif member is None:
            return await ctx.send("You didn't tell me which member to play with!")
        elif member == ctx.author:
            return await ctx.send("You can't play with yourself")
        elif member.bot:
            return await ctx.send("Dude.. bots can't play")

        else:
            confirm_view_obj_1 = confirm(ctx=ctx, member=member)
            confirm_view_obj_1.message = await ctx.send(f"{member.mention}! {ctx.author.name} wants to play connect 4 with you.", view=confirm_view_obj_1)
            await confirm_view_obj_1.wait()

            if confirm_view_obj_1.value:

                c4_view_obj = connect_4_view(ctx=ctx, member=member, message=confirm_view_obj_1.message)
                
                c4_view_obj.message = await ctx.send(c4_view_obj.content, embed=c4_view_obj.embed ,view=c4_view_obj)


    @commands.command(aliases=["mt", "match-tile", "matchtile"], brief="Play a game of match the correct tile.")
    async def match_tile(self, ctx: commands.Context):
        """Play a game of match the correct tile.
        **__RULES__**:
        You to have click on 2 tiles having same emoji.
        You can only have 2 open tiles at once.
        If you click on 2 matching tiles, they turn green and you get +1 point.
        Your aim is to repeat the same process for all the remaining tiles and get 12/12 points.
        If the two opened tiles don't match, they are closed.
        __But__ there is a clown <:pepeclown:884455754533310545> hiding among the emojis. If you click on the clown, it is game over.
        """
        confirm_view = just_confirm(ctx=ctx)
        confirm_view.message = await ctx.send(f"Have you read the rules of this game? You can read the rules by typing `{ctx.clean_prefix}help {ctx.command}`", view=confirm_view)
        await confirm_view.wait()

        if confirm_view.value:
            message = confirm_view.message
            mt_view = match_tile_view(ctx, message)
            await asyncio.sleep(2)
            mt_view.message = await ctx.send(embed=mt_view.embed, view=mt_view)


    @commands.command(name="3dmaze", aliases=["maze"])
    async def _3dmaze(self, ctx, row=5, column=5):
        """Starts a game of 3d maze runner."""

        if (row > 15) or (column > 15):
            return await ctx.send("row or column cannot be greater than 15")
        if (row < 5) or (column < 5):
            return await ctx.send("row or column cannot be less than 5")
        view = _3dmazeView(ctx, row, column)
        
        view.message = await ctx.send("pls wait...")
        await view.make_image()
        await view.message.edit(content=None, embed=view.embed, view=view)

    @commands.command()
    async def nim(self, ctx: commands.Context, member: discord.Member=None):
        """You can take any number of 🔴 from a row.
        Click on a 🔴 to take the 🔴 and all the 🔴 left to it.\nThe person to take the last 🔴 wins.
        """
        if member is None:
            return await ctx.reply("No member given")
        elif member.id == ctx.author.id:
            return await ctx.reply("You can't play with yourself")
        elif member.bot:
            return await ctx.reply("Bots can't play.")
            
        
        view = NimView(ctx, member=member)
        view.message = await ctx.reply(f"__**Nim game**__\n{ctx.author.name} vs {member.name}\n\nYou can take any number of 🔴 from a row.\nClick on a 🔴 to take the 🔴 and all the 🔴 left to it.\nThe person to take the last 🔴 wins.", embed=view.embed, view=view, mention_author=False)

    @commands.command()
    async def mm(self, ctx: commands.Context, member1: discord.Member=None, member2: discord.Member=None):
        if member1 is None:
            return await ctx.send("`member1` must be given.")

        if (member1 == member2) or (member1 == ctx.author) or (member2 == ctx.author):
            return await ctx.send("Every member must be unique.")
        
        if member1.bot:
            return await ctx.send("Bots can't play.")
        if member2 and member2.bot:
            return await ctx.send("Bots can't play.")

        choices = [ctx.author, member1]
        if member2:
            choices.append(member2)

        killer = random.choice(choices)

        vm = ViewManager(ctx, killer, member1, member2)
        details = f"__**{killer.name}**__ : <:impostor:927976226025508925>\n"

        choices.remove(killer)
        emojis = ("<:AmongusBlue:927937423227359263>", "<:AmongusLime:927937583676268647>")

        for index, member in enumerate(choices):
            details += f"{member.name} : {emojis[index]}\n"

        vm.stats_message = await ctx.send(f"{details}\n{len(vm.keys)} <:goldKey:929034929571000370> remaining")
        vm.player1_view.message = await ctx.author.send(embed=vm.player1_view.embed, view=vm.player1_view)
        vm.player2_view.message = await member1.send(embed=vm.player2_view.embed, view=vm.player2_view)
        
        if member2:
            vm.player3_view.message = await member2.send(embed=vm.player3_view.embed, view=vm.player3_view)
        await asyncio.sleep(25)

        if vm.player1_view.is_killer:
            vm.player1_view.update_buttons()
            await vm.player1_view.message.edit(view=vm.player1_view)

        elif vm.player2_view.is_killer:
            vm.player2_view.update_buttons()
            await vm.player2_view.message.edit(view=vm.player2_view)

        elif vm.player3_view.is_killer:
            vm.player3_view.update_buttons()
            await vm.player3_view.message.edit(view=vm.player3_view)


def setup(bot):
    bot.add_cog(Games(bot))
    print("Games cog is loaded")

