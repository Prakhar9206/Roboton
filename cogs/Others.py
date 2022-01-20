from typing import Dict
import discord
from discord.ext import commands
import googletrans
import textwrap
import unicodedata
from games.confirm_views import end_poll_confirm

class EndPollButton(discord.ui.Button):
    def __init__(self, creator: int, label: str, custom_id: str):
        super().__init__(style=discord.ButtonStyle.red, label=label, custom_id=custom_id)
        self.creator = creator # ctx.author.id

    def get_key(self, val, dictionary):
        for key, value in dictionary.items():
            if val == value:
                return key

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.creator:
            confirm_view = end_poll_confirm(self.creator)
            await interaction.response.send_message(f"Do you want to end the poll? This will automatically show the results.", ephemeral=True, view=confirm_view)
            await confirm_view.wait()

            if confirm_view.value:
                # print("poll ended")
                view: PollView = self.view
                bot: commands.Bot = view.bot
                channel = bot.get_channel(view.channel_id)
                message = await channel.fetch_message(view.message_id)
                user = bot.get_user(self.creator)
                col = bot.mongo_client.discord.polls
                doc: Dict = await col.find_one({"message_id" : view.message_id})

                em = message.embeds[0]

                results = {}
                em.title += "\n**This poll has ended.**"

                for k, v in doc.items(): # looping through options
                    if (k != "options") and (isinstance(v, list)): # unique options
                        results[k] = str(len(v))


                val = max(list(results.values()))
                winner = self.get_key(val, results)
                content = f"The winner of the poll is:\n__**{winner}**__\n\n"

                count = 1 # i hate myself for not using enumerate
                for k,v in results.items():
                    content += f"{count}. {k} : {v}\n"
                    count += 1

                for btn in view.children:
                    btn.disabled = True
                await message.edit(content=content, embed=em, view=view)
                await col.delete_one({"message_id" : view.message_id})
        else:
            await interaction.response.send_message(f"You cannot end this poll.", ephemeral=True)


class PollButton(discord.ui.Button):
    def __init__(self, label: str, custom_id: str):
        super().__init__(style=discord.ButtonStyle.grey, label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        bot: commands.Bot = view.bot
        col = bot.mongo_client.discord.polls
        doc: Dict = await col.find_one({"message_id" : view.message_id})

        array = doc[self.label]

        if interaction.user.id in array: # check if they have voted for the same option
            return await interaction.response.send_message(f"You have already voted for: {self.label}", ephemeral=True)

        for k, v in doc.items(): # previously voted for different option
            if (k != "options") and (isinstance(v, list)): # unique options
                if interaction.user.id in v:
                    v.remove(interaction.user.id)
                    array.append(interaction.user.id)

                    new_query = {"$set" : {
                        self.label : array,
                        k : v
                    }}
                    await col.update_one({"message_id" : view.message_id}, new_query)
                    return await interaction.response.send_message(f"You have changed your vote from: {k} to: {self.label}", ephemeral=True)

        if interaction.user.id not in array: # adding new user
            array.append(interaction.user.id)
            new_query = {"$set" : {self.label : array}}
            await col.update_one({"message_id" : view.message_id}, new_query)

            return await interaction.response.send_message(f"You have voted for: {self.label}", ephemeral=True)
        


class PollView(discord.ui.View):
    def __init__(self, bot, channel_id, creator: int, message_id: int, option1: str, option2: str, options):
    # def __init__(self):
        super().__init__(timeout=None)
        self.option1 = option1
        self.option2 = option2
        self.options = options
        self.bot = bot
        self.channel_id = channel_id
        self.creator = creator # ctx.author.id
        # print(self.options)
        self.message_id = message_id

        self.row_count = 0
        self.button_count = 2 # per row
        self.total_button_count = 2 # per row

        self.add_item(PollButton(self.option1, f"{message_id}-1"))
        self.add_item(PollButton(self.option2, f"{message_id}-2"))

        if self.options:
            if isinstance(self.options, list):
                for option in self.options:
                    self.total_button_count += 1
                    self.add_item(PollButton(option, f"{message_id}-{self.total_button_count}"))

            elif isinstance(self.options, str):
                self.total_button_count += 1
                self.add_item(PollButton(self.options, f"{message_id}-{self.total_button_count}"))

        self.total_button_count += 1
        self.add_item(EndPollButton(self.creator, "Show results", f"{self.message_id}-{self.total_button_count}"))




class Others(commands.Cog, name="Others"):
    """Commands that don't fit anywhere else come in this category"""
    
    def __init__(self,bot):
        self.bot = bot
        self.trans = googletrans.Translator()

    @commands.command()
    async def ping(self, ctx):
        """Shows the bot's ping"""
        await ctx.send(f"p0ng! {round(self.bot.latency * 1000)} ms")

    @commands.command(name="pfp", aliases=["av", "avatar"])
    async def pfp(self, ctx, member : discord.Member = None):
        """Shows pfp of a member."""
        if member == None:
            em = discord.Embed(title="Profile Picture of", description=f"{ctx.author}", color=ctx.author.color)
            em.set_image(url=ctx.author.avatar.url)
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title="Profile Picture of", description=f"{member}", color=member.color)
            em.set_image(url=member.avatar.url)
            await ctx.send(embed=em)

    @commands.command(name="nickname", aliases=["nick"])
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member : discord.Member = None, *, name=""):
        """Changes the nickname of a member."""
        if member is None:
            member = ctx.author
        # mod changing someone's nick
        
        if ctx.author.guild_permissions.manage_nicknames:
            try:
                await member.edit(nick=name)
                if name == "":
                    return await ctx.send(f"Successfully cleared nickname of {member}")
                return await ctx.send(f"Successfully changed nickname of {member} to {name}")
            except discord.HTTPException:
                pass
            # normal person changing own nick
        else:
            if ctx.author == member:
                try:
                    await member.edit(nick=name)
                    if name == "":
                        return await ctx.send(f"Successfully cleared nickname of {member}")
                    return await ctx.send(f"Successfully changed nickname of {member} to {name}")
                except discord.HTTPException:
                    await ctx.send("some error occured!")
            else:
                await ctx.send("You do not have enough permissions to use that!")

    @commands.command(name="invite")
    async def invite(self, ctx):
        """Invite me to your server using this link!"""
        invite_embed = discord.Embed(title="Want to add me to your server? Use the link below!")
        invite_embed.description=discord.Embed.Empty
        invite_embed.color=ctx.author.color
        invite_embed.add_field(name="Invite Bot", value=f"[Click Here](https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=67497024&scope=bot%20applications.commands)", inline=False)
        invite_embed.add_field(name="Join Server", value="[Click Here](https://discord.gg/kqMXRmduuU)", inline=False)
        await ctx.send(embed=invite_embed)

    @commands.command(aliases=["about"])
    async def info(self, ctx: commands.Context):
        """Gives the information about the bot"""
        
        await ctx.send(textwrap.dedent(f"""
        Hello. I am Roboton. I am a discord bot made by Sans The Skeleton#5153.
        Use `{ctx.clean_prefix}help` to see all of my commands.
        You can use `{ctx.clean_prefix}help [command]` for more help on a command.
        You can also type `{ctx.clean_prefix}help [category]` for more help on a category.
        """))

    @commands.command(name="prefix")
    async def prefix(self, ctx: commands.Context, new_prefix=None):
        """Shows the bots the prefix. You can also set a new prefix with this commands."""
        
        # no custom prefix in dms
        default_prefix = self.bot.prefixes.get("DEFAULT_PREFIX")
        

        if ctx.guild is None:
            if new_prefix is None:
                
                return await ctx.send(f"My prefix is `{default_prefix}`")
                
            if new_prefix:
                return await ctx.send("You can't change prefix in dms")

        current_prefix = self.bot.prefixes.get(str(ctx.guild.id))
        if current_prefix is None:
            current_prefix = default_prefix

        # show current prefix
        if new_prefix is None:
            # server_prefix = self.bot.prefixes.get(str(ctx.guild.id))
            if current_prefix is None:
                current_prefix = default_prefix
            return await ctx.send(f"My prefix for this server is `{current_prefix}`")

        # changing the prefix to a custom one
        if ctx.author.guild_permissions.manage_guild:
            if new_prefix is not None:
                col = self.bot.mongo_client.discord.prefixes 

            # checking if new prefix is same as current prefix
                if current_prefix == new_prefix:
                    return await ctx.send(f"The prefix for this server is already `{new_prefix}`")

                if new_prefix != default_prefix:
                    old_query = {"_id" : f"{self.bot.user.id}"}
                    new_query = {"$set":{
                        f"{ctx.guild.id}" : f"{new_prefix}"
                        }}
                    await col.update_one(old_query, new_query)
                    self.bot.prefixes[f"{ctx.guild.id}"] = new_prefix

                elif new_prefix == default_prefix:
                    old_query = {"_id" : f"{self.bot.user.id}"}
                    new_query = {"$unset":{
                        f"{ctx.guild.id}" : ""
                        }}
                    await col.update_one(old_query, new_query)
                    self.bot.prefixes.pop(f"{ctx.guild.id}")
                    
                return await ctx.send(f"Prefix for this server is changed to `{new_prefix}`")
        else:
            return await ctx.send(f"You do not have the permission to change the prefix for this server.")

    @commands.command()
    async def translate(self, ctx: commands.Context, *, message: commands.clean_content = None):
        """Translates a message to English with the help of Google translate."""
        loop = self.bot.loop
        if message is None:
            ref = ctx.message.reference
            if ref and isinstance(ref.resolved, discord.Message):
                message = ref.resolved.content
            else:
                return await ctx.send('Missing a message to translate')

        try:
            ret = await loop.run_in_executor(None, self.trans.translate, message)
        except Exception as e:
            return await ctx.send(f'An error occurred')#: {e.__class__.__name__}: {e}')

        em = discord.Embed(title='Translated from Google', colour=ctx.author.colour)
        src = googletrans.LANGUAGES.get(ret.src, '(auto-detected)').title()
        dest = googletrans.LANGUAGES.get(ret.dest, 'Unknown').title()
        em.add_field(name=f'From {src}', value=ret.origin, inline=False)
        em.add_field(name=f'To {dest}', value=ret.text, inline=False)
        await ctx.send(embed=em)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def charinfo(self, ctx, *, characters: str):
        """Shows you information about a number of characters.
        Only up to 25 characters at a time.
        """

        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>'

        msg = '\n'.join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send('Output too long to display.')
        await ctx.send(msg)

    @commands.command(name="poll", aliases=["poll-create", "poll_create", "pollcreate", "pc"])
    async def poll(self, ctx: commands.Context, message: str, option1: str, option2: str, *options):
        """Creates an anonymous voting poll. The creator of the poll can choose when to show the results of the poll.
        Example usage: `+poll create "whats your favourite color?" "i like red" "i like blue" "i like green" "i like yellow"`
        """
        # print(options)
        # print(type(options))
        if len(message) > 4000:
            return await ctx.send("Message is too long.")
        if len(options) > 18:
            return await ctx.send("Too many options were given.")
        if (len(option1) > 25) or (len(option2) > 25): # character limit of buttons
            return await ctx.send("Options must be within 25 character limit.")
        for o in options:
            if (len(o) > 25): # character limit of buttons
                return await ctx.send("Length of an option cannot be more than 25 characters.")

        msg = await ctx.send("Creating poll...") # just to get the message's id

        em = discord.Embed(title=f"{ctx.author.name}'s poll", description=message, colour=0x3248a8)

        if options:
            options = [option for option in options]
        else:
            options = None

        view = PollView(ctx.bot, ctx.channel.id, ctx.author.id, msg.id, option1, option2, options)

        await msg.edit(content=None, embed=em, view=view)
        query = {
            "channel_id" : ctx.channel.id,
            "creator" : ctx.author.id,
            "message_id" : msg.id,
            "option1" : option1,
            "option2" : option2,
            "options" : options,   
            option1 : [],
            option2 : [],
        }
        if options:
            for o in options:
                query[o] = []

        await ctx.bot.mongo_client.discord.polls.insert_one(query)




def setup(bot):
    bot.add_cog(Others(bot))
    print("Others cog is loaded")
