import discord
from utils import custom_errors
from discord.ext import commands
import os
import sys
import traceback
import motor.motor_asyncio
from ssl import CERT_NONE
import json
from cogs.Others import PollView


intents = discord.Intents.all()
with open('config.json', 'r') as f:
    config = json.load(f)
    token = config["TOKEN"]
    mongo_connection_url = config["MONGO_URI"]
    DEFAULT_PREFIX = config["PREFIX"]


def get_prefix(bot, message):
    # only allowing in servers
    if message.guild is not None:
        prefix = bot.prefixes.get(str(message.guild.id))
        # if prefix is not found, we return default prefix
        if prefix is None:
            prefix = (bot.prefixes.get("DEFAULT_PREFIX")) or DEFAULT_PREFIX

    # in dms we return default prefix
    else:
        prefix = bot.prefixes.get("DEFAULT_PREFIX")
    
    return commands.when_mentioned_or(prefix)(bot, message)

class Roboton(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

        self.prefixes = {}
        self.troll_ids = {}
        self.blacklisted_users = []
        self.anti_ghost_ping_users = []
        self.maze_cache_yellow_purple = {}
        self.maze_cache_green_pink = {}
        self._BotBase__cogs = commands.core._CaseInsensitiveDict() # case insensitive cogs
        self.aiohttp_session = None
        self.reddit_session = None
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_connection_url, ssl_cert_reqs=CERT_NONE)
        self.ping_react_list = []
        self.channels_ID_list = []

    def get_message(self, message_id: int) -> discord.Message:
        """Gets the message from cache"""
        return self._connection._get_message(message_id)

    async def on_ready(self):
        docs = self.mongo_client.discord.polls.find()
        if docs is not None:
            async for doc in docs:
                channel_id = doc["channel_id"]
                creator = doc["creator"]
                message_id = doc["message_id"]
                option1 = doc["option1"]
                option2 = doc["option2"]
                options = doc["options"]
                self.add_view(PollView(self, channel_id, creator, message_id, option1, option2, options), message_id=message_id)


bot = Roboton(command_prefix=get_prefix, intents=intents, case_insensitive=True, owner_ids=[842950909159145493, 846033217685684224])

@bot.check
async def blacklist_check(ctx):
    if ctx.author.id in bot.blacklisted_users:
        await custom_errors.blacklist_reason(ctx=ctx, bot=bot)
        raise custom_errors.Suspended()
        # return False will work too but its yells in terminal
    else:
        return True

_cd = commands.CooldownMapping.from_cooldown(2, 10, commands.BucketType.member)

@bot.check
async def cooldown_check(ctx):
    bucket = _cd.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.member)
    return True


os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
os.environ['JISHAKU_FORCE_PAGINATOR'] = 'True'
os.environ["JISHAKU_HIDE"] = 'True'


extensions=[
            'jishaku',
            'cogs.Background_tasks',
            'cogs.Admin',
            'cogs.Games',
            'cogs.Fun',
            'cogs.Chatbot',
            'cogs.Eval',
            'cogs.Tags',
            'cogs.Logging',
            'cogs.Error_handling',
            'cogs.Others',
            'cogs.Image',
            'cogs.Help',
            'cogs.Economy'

]

if __name__ == "__main__":
    for extension in extensions:
        try:
            bot.load_extension(extension)
            
        except Exception as e:
            print(f"Error loading {extension}", file=sys.stderr)
            traceback.print_exc()
        
bot.run(token)