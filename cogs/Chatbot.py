import discord
from discord.ext import commands
from discord.ext.commands.errors import CheckFailure
# import randomstuff
import json
import aiohttp

with open('config.json', 'r') as f:
    key = json.load(f)
    api_key = key['RS_API_KEY']
    rapidapi_key = key['RAPIDAPI_KEY']
# rs_client = randomstuff.AsyncClient(api_key=api_key)


# this is needed if we don't use a wrapper

# api_key = os.environ['RS_API_KEY']
# pgamerx_header = {"x-api-key": api_key}
# session = aiohttp.ClientSession(headers=pgamerx_header)

headers = {
    "authorization": f"{api_key}",
    'x-rapidapi-host': "random-stuff-api.p.rapidapi.com",
    'x-rapidapi-key': f"{rapidapi_key}"
    }

bot_owner = "Sans The Skeleton"
bot_name = "Roboton"

class Chatbot(commands.Cog, name="Chatbot"):
    """All chatbot related commands."""
    
    def __init__(self,bot):
        self.bot = bot

    # alternative way to make this in a command without any wrappers

    async def get_reply(self, clean_message, author_id):
        pgamerx_params = {
            'bot_master' : "Sans The Skeleton#5153",
            'bot_name' : "Roboton",
            'msg': clean_message,
            "id": author_id
            }
        try:
            async with aiohttp.ClientSession(headers = headers) as session:
                async with session.get(url="https://random-stuff-api.p.rapidapi.com/ai", params = pgamerx_params) as resp:
                    text = await resp.json()
                    # print(text)
                    aichatresponse = text['AIResponse']
                    return aichatresponse
                    
        except Exception as error:
            print(error)
            
            return "Some error occured with API"

    @commands.guild_only()
    @commands.command(name='Enable_chatbot', aliases=['ecb', 'enablechatbot'])
    @commands.has_permissions(manage_channels=True)
    async def Enable_chatbot(self, ctx):
        """Enables the chatbot in the channel in which this command is used. You need `manage_channels` permission to use this command."""
        if ctx.channel.id in self.bot.channels_ID_list:
            await ctx.send("Chatbot is already enabled in this channel.")
        else: 
            self.bot.channels_ID_list.append(ctx.channel.id)
            await self.bot.mongo_client.discord.chatbot_channels.insert_one({"channel_id" : f"{ctx.channel.id}"})
            await ctx.send("Successfully enabled chatbot in this channel.")

    @Enable_chatbot.error
    async def Enable_chatbot_error(self,ctx,error):
        if isinstance(error, CheckFailure):
            await ctx.send("You need to have `manage_channels` permission before using this command bruh.")

    @commands.guild_only()
    @commands.command(name='Disable_chatbot', aliases=['dcb', 'disablechatbot'])
    @commands.has_permissions(manage_channels=True)
    async def Disable_chatbot(self, ctx):
        """Disable the chatbot in this channel. You need `manage_channels` permission to use this command."""
        if ctx.channel.id in self.bot.channels_ID_list:

            self.bot.channels_ID_list.remove(ctx.channel.id)
            await self.bot.mongo_client.discord.chatbot_channels.delete_one({"channel_id" : f"{ctx.channel.id}"})

            await ctx.send("Successfully disabled chatbot in this channel.")

    @Enable_chatbot.error
    async def Disable_chatbot_error(self,ctx,error):
        if isinstance(error, CheckFailure):
            await ctx.send("You need to have `manage_channels` permission before using this command bruh.")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.bot.user.id == message.author.id:
            return
        if message.guild is None:
            return
        if message.author.bot:
            return

        elif (self.bot.user.mentioned_in(message) and message.mention_everyone is False) and (message.content.lower() == f'<@!{self.bot.user.id}>' or message.content.lower() == f'<@{self.bot.user.id}>'):
            
            # no custom prefix in dms
            default_prefix = self.bot.prefixes.get("DEFAULT_PREFIX")
            
            if message.guild is None:
                return await message.reply(f"My prefix is `{default_prefix}`", mention_author=False)

            current_prefix = self.bot.prefixes.get(str(message.guild.id))
            if current_prefix is None:
                current_prefix = default_prefix

            return await message.reply(f"{message.author.mention} thanks for pinging me. My prefix is `{current_prefix}`. Have a great day", mention_author=False)

        elif (message.channel.id) in self.bot.channels_ID_list:
            
            clean_message = message.clean_content
            try:
                # response = await rs_client.get_ai_response(message=clean_message, master=bot_owner, name=bot_name, uid=str(message.author.id), age="69")                
                # await message.reply(response.message, mention_author=False)
                
                # if we don't want a wrapper
                
                authorid = str(message.author.id)
                reply = await self.get_reply(clean_message, authorid)
                await message.reply(reply, mention_author = False)
            except Exception as e:
                print(e)



def setup(bot):
    bot.add_cog(Chatbot(bot))
    print("Chatbot cog is loaded")
