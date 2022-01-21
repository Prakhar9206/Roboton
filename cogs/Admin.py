import aiohttp
import discord
from discord.ext import commands
from discord.ext import buttons
import datetime
import copy
from typing import Union, Optional


target_channel = [] 
starting_channel = [891165515551240213] # control hq channel

target_user_list = []
user_control_channel_list = [891165558056304673]

DM_log_channel_list = [891165191537053756]


class MyPaginator(buttons.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class GlobalChannel(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            # Not found... so fall back to ID + global lookup
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f'Could not find a channel by ID {argument!r}.')
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is None:
                    raise commands.BadArgument(f'Could not find a channel by ID {argument!r}.')
                return channel

class Admin(commands.Cog, name="Admin", command_attrs=dict(hidden=True)):
    """Commands for the owner of the bot."""
    
    def __init__(self,bot):
        self.bot: commands.Bot = bot
    
# ------------------- blacklist group commands ---------------------------
    @commands.is_owner()
    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def blacklist(self, ctx):

        if len(self.bot.blacklisted_users) != 0:
            user_list = []
            em = discord.Embed(title="Blacklist")
            for user_id in self.bot.blacklisted_users:
                user = self.bot.get_user(user_id)
                user_list.append(f"{user} ---> ID = {user.id}")
            page = MyPaginator(colour=0xff1493, embed=True, entries=user_list, length=10, title='All the blacklisted users', timeout=90, use_defaults=True)
            await page.start(ctx)
        else:
            await ctx.send("Blacklist is empty.")

    @blacklist.command()
    async def add(self, ctx, user: discord.User, *, reason="No reason provided"):
        await self.bot.mongo_client.discord.blacklist.insert_one({
            "user" : f"{user.id}",
            "reason" : f"{reason}"
        })
        self.bot.blacklisted_users.append(user.id)
        await ctx.send(F"Blacklisted {user}, with ID -> {user.id}. For reason : \n{reason}")

    @blacklist.command()
    async def remove(self, ctx, user: discord.User):
        if user.id in self.bot.blacklisted_users:
            doc = await self.bot.mongo_client.discord.blacklist.find_one({
            "user" : f"{user.id}",
        })
        if doc:
            await self.bot.mongo_client.discord.blacklist.delete_one(doc)
            self.bot.blacklisted_users.remove(user.id)
            await ctx.send(f"Removed {user} from blacklist.")
        else:
            await ctx.send(f"{user} is not blacklisted.")

    @blacklist.command()
    async def info(self, ctx, user: discord.User):
        if user.id in self.bot.blacklisted_users:
            doc = await self.bot.mongo_client.discord.blacklist.find_one({
            "user" : f"{user.id}",
        })
        if doc:
            reason = doc["reason"]
            _user = self.bot.get_user(user)
            em = discord.Embed(title=_user.name)
            em.description = f"Blacklist for the following reason:\n{reason}"
            await ctx.send(f"Removed {user} from blacklist.")
        else:
            await ctx.send(f"{user} is not blacklisted.")
    
# ---------------------------admin commands----------------------------------------------------
    @commands.is_owner()
    @commands.command(hidden=True)
    async def status(self, ctx, activitytype, *, text = None):
        """Changes the activity status of the bot."""
        mycol = self.bot.mongo_client.discord.custom_status
        old_query = {'_id': '69'}
        
        # default status
        if str(activitytype).lower() == "default":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.bot.guilds)} servers | type +help for more info"))
            new_query = {"$set" :{
                "activity_type" : "watching",
                "status_text" : "default"
            }}
            await mycol.update_one(old_query, new_query)
            await ctx.send("Status updated")

        # playing status
        elif str(activitytype).lower() == "playing":
            await self.bot.change_presence(activity=discord.Game(name=f"{text}"))
            new_query = {"$set" :{
                "activity_type" : "playing",
                "status_text" : f"{text}"
            }}
            await mycol.update_one(old_query, new_query)
            await ctx.send("Status updated")

        # listening status
        elif str(activitytype).lower() == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{text}"))
            new_query = {"$set" :{
                "activity_type" : "listening",
                "status_text" : f"{text}"
            }}
            await mycol.update_one(old_query, new_query)            
            await ctx.send("Status updated")
    
        # competing status
        elif str(activitytype).lower() == "competing":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=f"{text}"))
            new_query = {"$set" :{
                "activity_type" : "competing",
                "status_text" : f"{text}"
            }}
            await mycol.update_one(old_query, new_query)
            await ctx.send("Status updated")
        
        # watching status
        elif str(activitytype).lower() == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{text}"))
            new_query = {"$set" :{
                "activity_type" : "watching",
                "status_text" : f"{text}"
            }}
            await mycol.update_one(old_query, new_query)
            await ctx.send("Status updated")

        # streaming status
        elif str(activitytype).lower() == "streaming":
            await self.bot.change_presence(activity=discord.Streaming(name=f"{text}", url="https://www.twitch.tv/hidden_black_"))
            new_query = {"$set" :{
                "activity_type" : "streaming",
                "status_text" : f"{text}"
            }}
            await mycol.update_one(old_query, new_query)            
            await ctx.send("Status updated")

    @commands.command(hidden=True)
    async def d_sudo(self, ctx, channel: Optional[GlobalChannel], who: Union[discord.Member, discord.User], *, command: str):
        """Run a command as another user optionally in another channel."""
        msg = copy.copy(ctx.message)
        channel = channel or ctx.channel
        msg.channel = channel
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        
        await self.bot.invoke(new_ctx)
    


    @commands.command()
    @commands.is_owner()
    async def disable(self, ctx, cmd):
        """Disables a command"""
        command = self.bot.get_command(cmd)
        if not command.enabled:
            return await ctx.send("This command is already disabled.")
        command.enabled = False
        await ctx.send(f"Disabled {command.name} command.")

    @commands.command()
    @commands.is_owner()
    async def enable(self, ctx, cmd):
        """Enables a command"""
        command = self.bot.get_command(cmd)
        if command.enabled:
            return await ctx.send("This command is already enabled.")
        command.enabled = True
        await ctx.send(f"Enabled {command.name} command.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def servers(self, ctx):
        """Lists all servers the bot is in with their IDs"""
        servers_list = []
        if ctx.author.id in self.bot.owner_ids:
            for server in self.bot.guilds:
                
                # await ctx.send(f"{server} ---> ID = {server.id}")
                servers_list.append(f"{server} ---> ID = {server.id}")
            page = MyPaginator(colour=0xff1493, embed=True, entries=servers_list, length=10, title='All the servers of this bot', timeout=90, use_defaults=True)
            await page.start(ctx)
            
        
        else:
            await ctx.send("You are not the owner of this bot!")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def channels(self, ctx, server: discord.Guild):
        """Lists all channels of a server"""
        channels_list = []
        if ctx.author.id in self.bot.owner_ids:
            try:                
                for channels in server.text_channels:
                    
                    channels_list.append(f"{channels}, ID -> {channels.id}")
                page = MyPaginator(colour=0xff1493, embed=True, entries=channels_list, length=10, title=f'All the channels of {server.name}', timeout=90, use_defaults=True)
                await page.start(ctx)

            except Exception as e:
                await ctx.send("Invalid server ID.")
        else:
            await ctx.send("You are not the owner of this bot!")


    @commands.command(name="make_invite", aliases=["mi"], hidden=True)
    @commands.is_owner()
    async def make_invite(self, ctx, channel: Optional[GlobalChannel] = None, guild: discord.Guild = None):
        """Creates an invite for a server with a given channel"""
        if channel:
            try:
                link = await channel.create_invite(max_age = 300)
                await ctx.send(link)

            except discord.Forbidden: # we dont have perms
                await ctx.send("I do not have perms")
        
        elif guild:
            channel = guild.text_channels[0]
            try:
                link = await channel.create_invite(max_age = 300)
                await ctx.send(link)
            except discord.Forbidden: # we dont have perms
                await ctx.send("I do not have perms")

    @commands.command(name="members")
    @commands.is_owner()    
    async def members(self, ctx, server: discord.Guild):
        """Lists the members of a server"""
        member_list = []
        for member in server.members:
            member_list.append(f"{member.name}, ID -> {member.id}")
        page = MyPaginator(colour=0xff1493, embed=True, entries=member_list, length=10, title=f'All the members of {server.name}', timeout=90, use_defaults=True)
        await page.start(ctx)            


#===================================================================================================
# channels stuff
    @commands.command(name="start_channel", aliases=["starting_channel", "sc"], hidden=True)
    @commands.is_owner()
    async def start_channel(self, ctx):
        """Marks the channel to be used as the starting channel to send messages via bot."""
        if ctx.author.id in self.bot.owner_ids:
            starting_channel.clear()
            starting_channel.append(int(ctx.channel.id))
            await ctx.message.add_reaction('✅')

        else:
            await ctx.send("You do not own this bot!")

    @commands.command(name="target_channel", aliases=["tc"], hidden=True)
    @commands.is_owner()
    async def target_channel(self, ctx, channel_id):
        """Targets a channel where the messages from start_channel will go"""
        if ctx.author.id in self.bot.owner_ids:
            target_channel.clear()
            target_channel.append(int(channel_id))
            chan = self.bot.get_channel(int(channel_id))
            
            em = discord.Embed(title="Target successful", description=f"Targetting channel: {chan} in server: {chan.guild}", color=0x2fef12)
            await ctx.send(embed=em)
            await ctx.message.add_reaction('✅')

        else:
            await ctx.send("You do not own this bot!")


    @commands.command(name="clear_all_channels", aliases=["cac", "clearallchannels"], hidden=True)
    @commands.is_owner()
    async def clear_all_channels(self, ctx):
        """Resets start_channel and target_channel"""
        if ctx.author.id in self.bot.owner_ids:
            target_channel.clear()
            starting_channel.clear()
            await ctx.message.add_reaction('✅')

        else:
            await ctx.send("You do not own this bot!")

# ----------------------------------------------------------------------------------------------------------------------------------------
# user and DM stuff
    @commands.command(name="target_user", aliases=["tu"], hidden=True)
    @commands.is_owner()
    async def target_user(self, ctx, user_id):
        """Targets a user to send messages"""
        if ctx.author.id in self.bot.owner_ids:
            try:
                target_user_list.clear()
                target_user_list.append(int(user_id))
                user = self.bot.get_user(int(user_id))
                await ctx.send(f"Targetting {user}")
                await ctx.message.add_reaction('✅')
            except Exception as e:
                await ctx.send("Enter a valid ID")
        else:
            await ctx.send("You do not own this bot!")


    @commands.command(name="user_starting_channel", aliases=["user_control_channel", "user_start_channel", "usc", "ucc"], hidden=True)
    @commands.is_owner()
    async def user_starting_channel(self, ctx):
        """Marks the current channel to send messages to a targetted user"""
        if ctx.author.id in self.bot.owner_ids:
            user_control_channel_list.clear()
            user_control_channel_list.append(int(ctx.channel.id))
            await ctx.message.add_reaction('✅')

        else:
            await ctx.send("You do not own this bot!")

    @commands.command(name="clear_all_users", aliases=["cau"], hidden=True)
    @commands.is_owner()
    async def clear_all_users(self, ctx):
        """Resets user_starting_channel and target_user"""
        if ctx.author.id in self.bot.owner_ids:
            target_user_list.clear()
            user_control_channel_list.clear()
            await ctx.message.add_reaction('✅')

        else:
            await ctx.send("You do not own this bot!")

#----------------------------------- Listeners ------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is ready!!")
        print(f"Logged in as {self.bot.user}")
        print(f"ID ---> {self.bot.user.id}")
        if self.bot.aiohttp_session is None:
            self.bot.aiohttp_session = aiohttp.ClientSession()
        if self.bot.reddit_session is None:
            headers = {"User-Agent" : "Discord bot by u/sans-the-skeleton"}
            self.bot.reddit_session = aiohttp.ClientSession(headers=headers)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        
        # DM logs
        if message.guild == None:
            if message.author.id == self.bot.user.id:
                return
            else:
                DM_logs_channel = self.bot.get_channel(DM_log_channel_list[0])

                if message.content == "":
                    try:
                        
                        message_attachments = message.attachments[0]
                        image_url = message_attachments.url
                        em = discord.Embed(title=f"{message.author}", description="Image received", color=message.author.color)
                        em.set_image(url=image_url)                        
                        em.set_thumbnail(url=message.author.avatar.url)
                        # em.add_field(name="Channel :" ,value=f"{message.channel}")
                        em.set_footer(text=f"{message.author}")                        
                        await DM_logs_channel.send(embed=em)
                        return

                    except Exception as e:
                        await DM_logs_channel.send("Could not read that message")

                em = discord.Embed(title=f"{message.author}", description=f"{message.content}", color=message.author.color)
                em.add_field(name="User ID :" ,value=f"{message.author.id}")
                em.set_thumbnail(url=message.author.avatar.url)
                em.timestamp = datetime.datetime.utcnow()
                await DM_logs_channel.send(embed=em)


        if message.author.id == self.bot.user.id:
            pass
        
        # send from target channel to starting channel
        elif message.channel.id in target_channel:
            schannel = self.bot.get_channel(starting_channel[0])
            content = message.content
            if content == "":
                try:
                    message_attachments = message.attachments[0]
                    content = message_attachments.url
                    em = discord.Embed(title=f"{message.guild}", description="Image received", color=message.author.color)
                    em.set_image(url=content)
                    em.set_thumbnail(url=message.author.avatar.url)
                    # em.add_field(name="Channel :" ,value=f"{message.channel}")
                    em.set_footer(text=f"{message.author}")
                    await schannel.send(embed=em)
                    return

                except Exception as e:
                    await schannel.send("Could not read that message")

            em = discord.Embed(title=f"{message.guild}", description=f"{content}", color=message.author.color)
            em.set_thumbnail(url=message.author.avatar.url)
            em.add_field(name="Channel :" ,value=f"{message.channel}")
            em.set_footer(text=f"{message.author}")
            await schannel.send(embed=em)

        # send from starting channel to target channel
        elif message.channel.id in starting_channel:
            content = message.content
            if content.startswith("+"):
                return
            if content == "":
                try:
                    message_attachments = message.attachments[0]
                    content = message_attachments.url
                except Exception as e:
                    await message.channel.send("Could not read that message")

            
            else:
                try:
                    target = self.bot.get_channel(target_channel[0])
                    await target.send(content)
                except Exception as e:
                    pass

        # DM stuff
        # send from to DM to control channel
        elif message.author.id in target_user_list:
            if message.guild == None:
                channel = self.bot.get_channel(user_control_channel_list[0])
                
                if message.content == "":
                    try:
                        
                        message_attachments = message.attachments[0]
                        image_url = message_attachments.url
                        em = discord.Embed(title=f"{message.author}", description="Image received", color=message.author.color)
                        em.set_image(url=image_url)                        
                        em.set_thumbnail(url=message.author.avatar.url)
                        em.set_footer(text=f"{message.author}")                        
                        await channel.send(embed=em)
                        return

                    except Exception as e:
                        await channel.send("Could not read that message")

                em = discord.Embed(title=f"{message.author}", description=f"{message.content}", color=message.author.color)
                em.add_field(name="User ID :" ,value=f"{message.author.id}")
                em.set_thumbnail(url=message.author.avatar.url)
                em.timestamp = datetime.datetime.utcnow()
                await channel.send(embed=em)

        # from control channel to DM
        elif message.channel.id in user_control_channel_list:
            content = message.content
            
            if content.startswith("+"):
                return
            if content == "":
                try:
                    message_attachments = message.attachments[0]
                    content = message_attachments.url
                except Exception as e:
                    await message.channel.send("Could not read that message")
            else:
                try:
                    target = self.bot.get_user(target_user_list[0])
                    await target.send(content)
                except Exception as e:
                    pass
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        channel = self.bot.get_channel(891165635789332510)
        em = discord.Embed(title= f"Bot added in '{guild.name}'")
        em.description = "\n".join((f"ID: {guild.id}", f"Total Members: {guild.member_count}", f"Guild Owner: {guild.owner}"))
        em.color = 0x33f72d
        await channel.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        channel = self.bot.get_channel(891165635789332510)
        em = discord.Embed(title= f"Bot removed in '{guild.name}'")
        em.description = "\n".join((f"ID: {guild.id}", f"Total Members: {guild.member_count}", f"Guild Owner: {guild.owner}"))
        em.color = 0xf72d2d
        await channel.send(embed=em)


def setup(bot):
    bot.add_cog(Admin(bot))
    print("Admin cog is loaded")
