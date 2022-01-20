import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from typing import List
from discord.ext.commands.errors import CheckFailure
import motor
from discord.ext import tasks
import random

troll_guild_and_members = {} # "guild_id" : [member1_id, member2_id...]
white_check_mark_emoji = '✅'



very_special_people = [842950909159145493, 451125295848751104]
pingsock_emoji = "<:AngryPingSock:862345990191054858>"
spam = ['fuck you','fuck u','u suck','you are idiot','u r idiot','you are trash','u r trash','you are dumb','u r dumb','you are stupid','u r stupid','fuck off','you are gay','u r gay','pls die']



class FreeMoney(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.timeout = 60

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        

    @discord.ui.button(emoji=white_check_mark_emoji, label="Click4money")
    async def free_money_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("virus activated", ephemeral=True)



class Fun(commands.Cog, name="Fun", description="All fun commands."):
    
    def __init__(self,bot):
        self.bot: commands.Bot = bot
    

    @commands.command(name="asciify")   #font, optional arguement, probably will come with dpy v2
    async def asciify(self, ctx, *, text = None):
        """Converts the text into an ascii form."""
        font = 'doom'
        if text is None:
            return await ctx.send("You did not specify what text to ASCIIfy")
        
        
        async with self.bot.aiohttp_session.get(f"https://artii.herokuapp.com/make?text={text}&font={font}") as resp:
            reply = (await resp.text())
            await ctx.send(f"```\n{reply}\n```")
                    

    @commands.command()
    async def gender(self, ctx, name = None):
        """Tries to guess the gender of the name provided."""
        if name is None:
            return await ctx.send("You did not provide a name")
        async with self.bot.aiohttp_session.get(f"https://api.genderize.io/?name={name}") as resp:
            reply = await resp.json()
            gender = reply['gender']
            if gender:
                await ctx.send(f"{name} is a {gender}.")
            else:
                await ctx.send(f"I cannot figure out {name}'s gender by the name.")


    @commands.command(name='Troll_start', aliases=['trollstart'])
    @commands.has_permissions(manage_messages=True)
    async def Troll_start(self,ctx: commands.Context, member: discord.Member = None,):
        """Always delete the messages of the person getting trolled. The `manage_messages` permission is required in order to use this command."""
        if member == None:
            return await ctx.send("Please mention a person who you want to troll.")

        if member.id in self.bot.owner_ids:
            return await ctx.send("I cannot troll my owner")
        if int(member.id) == self.bot.user.id:
            return await ctx.send("I cannot troll myself")
        if member.id == 451125295848751104:
            return await ctx.send("Lab would ban me if I troll him.")
        member_ids = troll_guild_and_members.get(f"{ctx.guild.id}")
        if member_ids is not None: # check if we are already trolling them
            if member.id in member_ids:
                return await ctx.send(f"{member} is already being trolled")

        else:
            if member.id == ctx.author.id:
                await ctx.send("Such an idiot. You are trolling yourself. I am not gonna stop you.")

            # member_ids = troll_guild_and_members.get(f"{ctx.guild.id}")
            if member_ids is None: # creating new key if no key exists
                troll_guild_and_members[f"{ctx.guild.id}"] = [member.id]
            elif member_ids: # if key exists, we append to the list of ids
                troll_guild_and_members[f"{ctx.guild.id}"].append(member.id)
            await ctx.send(f"Started trolling {member}")


    @commands.command(name='Troll_stop', aliases=['trollstop'])
    @commands.has_permissions(manage_messages=True)
    async def Troll_stop(self, ctx: commands.Context, member: discord.Member = None):
        """Stops trolling a person who is getting trolled. The `manage_messages` permission is required in order to use this command."""
        if member is None:
            return await ctx.send("Please mention a person who you want to stop trolling.")

        member_ids: List = troll_guild_and_members.get(f"{ctx.guild.id}")
        if member_ids is None:
            return await ctx.send(f"{member} is not being trolled.")
        if member.id not in member_ids:
            return await ctx.send(f"{member} is not being trolled.")
        else:
            member_ids.remove(member.id)
            if len(member_ids) == 0:
                troll_guild_and_members.pop(f"{ctx.guild.id}")
            await ctx.send(f"Stopped trolling {member}")


    @commands.command(name='Free_money', aliases=['Freemoney'])
    async def Free_money(self,ctx):
        """Gives you some free money."""
        view = FreeMoney()
        em = discord.Embed(title= "FREE ROBUX WOOHOO !!!!", description= "react with ✅ to get free robux !!", color= ctx.author.color)
        msg = await ctx.send(embed=em, view=view)

    @commands.command()        
    async def joke(self, ctx: commands.Context):
        """Gives a random joke."""
        async with self.bot.reddit_session.get(f'https://www.reddit.com/r/Jokes/hot.json') as r:
            print(r)
            res = await r.json()
            random_joke = random.randint(1,25)
            title = res['data']['children'] [random_joke]['data']['title']
            jokeLink = res['data']['children'] [random_joke]['data']['permalink']
            completeLink = f"https://www.reddit.com{jokeLink}"
            em = discord.Embed(title=title, url=completeLink)
            description = res['data']['children'] [random_joke]['data']['selftext']
            em.description = description
            await ctx.send(embed=em)

    @commands.command(name="meme",aliases=["memes"]) 
    async def meme(self, ctx):
        """Shows some fresh and good memes from reddit!"""
        random_meme_sub = random.choice(["memes", "dankmemes", "meme"])
        
        async with self.bot.reddit_session.get(f'https://www.reddit.com/r/{random_meme_sub}/hot.json') as r:
            res = await r.json()
            random_meme = random.randint(0,25)
            meme_is_nsfw = res['data']['children'] [random_meme]['data']['over_18']
            if meme_is_nsfw:
                await self.meme(ctx)
            else:
                memeLink = res['data']['children'] [random_meme]['data']['permalink']
                completeLink = f"https://www.reddit.com{memeLink}"
                memeTitle = res['data']['children'] [random_meme]['data']['title']
                memeUpvotes = res['data']['children'] [random_meme]['data']['ups']
                memeComments = res['data']['children'] [random_meme]['data']['num_comments']
                embed = discord.Embed(title=f"{memeTitle}", description=f"Other info:\nUpvotes: {memeUpvotes}\nComments: {memeComments}\n[Link]({completeLink})")
                embed.color=ctx.author.color
                embed.set_image(url=res['data']['children'] [random_meme]['data']['url'])
                embed.set_footer(text=f"Fetched from r/{random_meme_sub}")

                await ctx.send(embed=embed)

    @commands.command(name="ping_react", aliases=["pingreact"])
    async def ping_react(self, ctx):
        """Bot will react with <:pingsock:796686890539417632> whenever you are pinged."""
        col = self.bot.mongo_client.discord.ping_react_ids
        # checking if they already exist in our database
        check_if_already_exists = await col.find_one({"user_id" : f"{ctx.author.id}"})
        if check_if_already_exists:
            return await ctx.send(f"I am already reacting with {pingsock_emoji} whenever you are pinged.")
        
        await col.insert_one({"user_id" : f"{ctx.author.id}"})
        self.bot.ping_react_list.append(ctx.author.id)
        await ctx.send(f"OK, I will react with {pingsock_emoji} whenever you are pinged.")

    @commands.command(name="stop-ping-react")
    async def stop_ping_react(self, ctx):
        """Bot will stop reacting with <:pingsock:796686890539417632> whenever you are pinged."""
        col = self.bot.mongo_client.discord.ping_react_ids
        query = {"user_id" : f"{ctx.author.id}"}
        # finding if they are in our database
        finding_user = await col.find_one({"user_id" : f"{ctx.author.id}"})

        # if they are found, we delete them
        if finding_user:
            await col.delete_one(query)
            self.bot.ping_react_list.remove(ctx.author.id) # also removing them locally
            await ctx.send(f"OK. I will stop reacting with {pingsock_emoji} whenever you are pinged.")

        else:
            await ctx.send(f"I am not even reacting {pingsock_emoji} whenever you are pinged!")

    @commands.command(name="did_you_mean", aliases=["dym", "didyoumean"])
    async def dym(self, ctx, *, text = "No text entered| pls enter text"):
        """Make a google did you mean meme. Remember to separate the two texts by a '|'"""
        splitted_text = text.split('|')
        upperText = splitted_text[0]
        bottomText = splitted_text[1]

        img = Image.open("dym.png")
        draw = ImageDraw.Draw(img)
        font_type = ImageFont.truetype("arial.ttf", 24)
        font_type2 = ImageFont.truetype("arialbi.ttf", 24)

        draw.text((200,90), upperText, (20,20,20), font=font_type)
        draw.text((320,240), bottomText, (33,21,145), font=font_type2)
        img.save("text.png")

        await ctx.send(file = discord.File("text.png"))
    

    @commands.command(aliases=["anti-ghost-ping", "antighostping", "agp"])
    async def anti_ghost_ping(self, ctx: commands.Context):
        """Bot will notify (DM) you whenever you are ghost pinged."""
        col = self.bot.mongo_client.discord.anti_ghost_ping_users
        # checking if they already exist in our database
        check_if_already_exists = await col.find_one({"user_id" : f"{ctx.author.id}"})
        if check_if_already_exists:
            return await ctx.send(f"I am already notifying you whenever you are ghost pinged.")
        
        await col.insert_one({"user_id" : f"{ctx.author.id}"})
        # user = self.bot.get_user(ctx.author.id)
        self.bot.anti_ghost_ping_users.append(ctx.author.id)
        # self.bot.anti_ghost_ping_users.append(user)
        await ctx.send(f"OK, I will notify (DM) you whenever you get ghost pinged.")

    @commands.command(aliases=["stop-anti-ghost-ping", "stopantighostping", "sagp"])
    async def stop_anti_ghost_ping(self, ctx: commands.Context):
        """Bot will stop notifying you whenever you are ghost pinged."""
        col = self.bot.mongo_client.discord.anti_ghost_ping_users
        query = {"user_id" : f"{ctx.author.id}"}
        # finding if they are in our database
        finding_user = await col.find_one({"user_id" : f"{ctx.author.id}"})

        # if they are found, we delete them
        if finding_user:
            await col.delete_one(query)
            # user = self.bot.get_user(ctx.author.id)
            self.bot.anti_ghost_ping_users.remove(ctx.author.id) # also removing them locally
            await ctx.send(f"OK, I will stop notifying you whenever you are ghost pinged.")

        else:
            await ctx.send(f"I am not even notifying you whenever you are ghost pinged!")


    #--------- Listeners ---------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        if message.author.id == self.bot.user.id:
            return

        if (message.mention_everyone is False) and (pingsock_emoji not in message.reactions) and (message.guild is not None):

            member_ids_set = set(self.bot.ping_react_list)
            message_mentions = set([member.id for member in message.mentions])
            result = member_ids_set.intersection(message_mentions)
            if result:
                await message.add_reaction(pingsock_emoji)

        if message.guild is not None:
            trolled_member_ids = troll_guild_and_members.get(f"{message.guild.id}")
            if trolled_member_ids is not None:
                if message.author.id in trolled_member_ids:
                    try:
                        await message.delete()
                        return
                    except Exception:
                        pass

        for abusiveWords in spam:
            if (self.bot.user.mentioned_in(message)) and (message.mention_everyone is False) and (abusiveWords in message.content.lower()):
                await message.reply("NO U")


    def get_all_members(self, guild: discord.Guild) -> List[discord.Member]:
        """Returns a list of all members (discord.Member) in a guild which are using anti ghost ping."""
        members = []
        for userid in self.bot.anti_ghost_ping_users:
            member = guild.get_member(userid)
            if member is not None:
                members.append(member)
        return members

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if message.guild is not None:
            if message.mentions or message.role_mentions:
                members = self.get_all_members(message.guild)
                for member in members:
                    if member.mentioned_in(message) and (message.author.id != member.id): # to prevent checking self ghost pings
                        em = discord.Embed(title="You have been ghost pinged!")
                        em.description = f"__**The message contained the following text**__\n\n{message.clean_content}"
                        em.add_field(name="The message was sent by", value=f"{message.author}", inline=False)
                        em.add_field(name="server", value=f"{message.guild.name}", inline=False)
                        em.add_field(name="Channel", value=f"{message.channel.name}", inline=False)
                        em.set_thumbnail(url=message.author.avatar.url)
                        em.color = 0xfc0339

                        try:
                            await member.send(embed=em)
                        except Exception:
                            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.id == self.bot.user.id:
            return

        if after.guild is not None:
            if (before.mentions or before.role_mentions):
                if (before.mentions != after.mentions) or (before.role_mentions != after.role_mentions):

                    members = self.get_all_members(after.guild)
                    for member in members:
                        if member.mentioned_in(before) and (before.author.id != member.id) and (member.mentioned_in(after) is False): # to prevent checking self ghost pings
                            em = discord.Embed(title="You have been ghost pinged by editing a message!")
                            em.description = f"__**The message contained the following text**__"
                            em.add_field(name="Before", value=f"{before.clean_content}")
                            em.add_field(name="After", value=f"{after.clean_content}")

                            em.add_field(name="The message was sent by", value=f"{after.author}", inline=False)
                            em.add_field(name="server", value=f"{after.guild.name}", inline=False)
                            em.add_field(name="Channel", value=f"{after.channel.name}", inline=False)
                            em.set_thumbnail(url=after.author.avatar.url)
                            em.color = 0xfc0339

                            try:
                                await member.send(embed=em)
                            except Exception:
                                pass

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Message]):
        reported_to: List[discord.Member] = []
        for message in messages:
            if message.author.id == self.bot.user.id:
                return

            if message.guild is not None:
                if message.mentions or message.role_mentions:
                    members = self.get_all_members(message.guild)
                    for member in members:
                        if member.mentioned_in(message) and (message.author.id != member.id) and (member.id not in reported_to): # to prevent checking self ghost pings and reporting many times
                        # if member.mentioned_in(message):
                        #     if message.author.id != member.id:
                        #         if member.id not in reported_to:
                            em = discord.Embed(title="You have been ghost pinged in a bulk delete of messages. I am __only reporting one of those messages__ to not spam your DM. There might have been more ghost pings for you")
                            em.description = f"__**The message contained the following text**__\n\n{message.clean_content}"
                            em.add_field(name="The message was sent by", value=f"{message.author}", inline=False)
                            em.add_field(name="server", value=f"{message.guild.name}", inline=False)
                            em.add_field(name="Channel", value=f"{message.channel.name}", inline=False)
                            em.set_thumbnail(url=message.author.avatar.url)
                            em.color = 0xfc0339

                            reported_to.append(member.id)
                            try:
                                await member.send(embed=em)
                            except Exception:
                                pass


def setup(bot):
    bot.add_cog(Fun(bot))
    print("Fun cog is loaded")
