import discord
from discord.ext import commands
from discord.ext import tasks

class BackgroundTasks(commands.Cog, name="BackgroundTasks", command_attrs=dict(hidden=True)):
    """All the background tasks are handled here.
    This includes storing stuff from db into cache.
    """
    
    def __init__(self,bot: commands.Bot):
        self.bot = bot
        self.custom_status.start()
        self.get_blacklisted_users.start()
        self.get_pre.start()
        self.get_ping_react_ids.start()
        self.get_channels_from_db.start()
        self.anti_ghost_ping_ids.start()
        self.get_maze_urls.start()
    
    # custom status
    @tasks.loop(minutes=30)
    async def custom_status(self):
        mycol = self.bot.mongo_client.discord.custom_status

        query = await mycol.find_one({'_id': '69'})
        activity_type = query["activity_type"]
        status = query["status_text"]
        
        if str(status).lower() == "default":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.bot.guilds)} servers | type +help for more info"))
            
        elif str(activity_type).lower() == "playing":
            await self.bot.change_presence(activity=discord.Game(name=f"{status}"))
            
        elif str(activity_type).lower() == "listening":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{status}"))
            
        elif str(activity_type).lower() == "competing":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name=f"{status}"))
            
        elif str(activity_type).lower() == "watching":
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{status}"))

        elif str(activity_type).lower() == "streaming":
            await self.bot.change_presence(activity=discord.Streaming(name=f"{status}", url="https://www.twitch.tv/hidden_black_"))

        else:
            print("bruh invalid status")

    @custom_status.before_loop
    async def before_custom_status(self):
        await self.bot.wait_until_ready()

    # blacklist
    @tasks.loop(minutes=15)
    async def get_blacklisted_users(self):
        mycol = self.bot.mongo_client.discord.blacklist
        query = mycol.find()
        self.bot.blacklisted_users = [int(doc["user"]) async for doc in query]
        
    @get_blacklisted_users.before_loop
    async def before_blacklist(self):
        await self.bot.wait_until_ready()

    # prefixes
    @tasks.loop(minutes=15)
    async def get_pre(self):
        self.bot.prefixes = await self.bot.mongo_client.discord.prefixes.find_one({"_id" : f"{self.bot.user.id}"})

    @get_pre.before_loop
    async def before_get_pre(self):
        await self.bot.wait_until_ready()

    # ping react ids
    @tasks.loop(minutes=10)
    async def get_ping_react_ids(self):
        
        col = self.bot.mongo_client.discord.ping_react_ids

        query = col.find()
        self.bot.ping_react_list.clear()
        async for doc in query:
            raw_user_ids = doc["user_id"]
            user_id = int(raw_user_ids)
            self.bot.ping_react_list.append(user_id)

    @get_ping_react_ids.before_loop
    async def before_ping_react(self):
        await self.bot.wait_until_ready()

    # chatbot channels
    @tasks.loop(minutes=10)
    async def get_channels_from_db(self):
        mydb = self.bot.mongo_client["discord"]
        mycol = mydb["chatbot_channels"]

        query = mycol.find()
        self.bot.channels_ID_list.clear()
        async for doc in query:
            raw_channel = doc["channel_id"]
            channel = int(raw_channel)
            self.bot.channels_ID_list.append(channel)

    @get_channels_from_db.before_loop
    async def before_ping_react(self):
        await self.bot.wait_until_ready()

    # anti ghost ping ids
    @tasks.loop(minutes=10)
    async def anti_ghost_ping_ids(self):
        
        col = self.bot.mongo_client.discord.anti_ghost_ping_users

        query = col.find()
        self.bot.anti_ghost_ping_users.clear()
        async for doc in query:
            raw_user_ids = doc["user_id"]
            user_id = int(raw_user_ids)
            # user = self.bot.get_user(user_id)
            # if user is not None:
            self.bot.anti_ghost_ping_users.append(user_id)

    @anti_ghost_ping_ids.before_loop
    async def before_ping_react(self):
        await self.bot.wait_until_ready()

    # maze urls
    @tasks.loop(minutes=15)
    async def get_maze_urls(self):
        self.bot.maze_cache_yellow_purple = await self.bot.mongo_client.discord.maze_URLs.find_one({"_id" : "yellow_purple"})
        self.bot.maze_cache_green_pink = await self.bot.mongo_client.discord.maze_URLs.find_one({"_id" : "green_pink"})


    @get_maze_urls.before_loop
    async def before_get_maze_urls(self):
        await self.bot.wait_until_ready()




def setup(bot):
    bot.add_cog(BackgroundTasks(bot))
    print("BackgroundTasks cog is loaded")