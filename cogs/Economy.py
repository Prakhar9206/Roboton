import discord
from discord.ext import commands

class Database_Manager():
    """The class which handles all database operations."""
    def __init__(self, bot) -> None:
        self.bot = bot
        self.col = self.bot.mongo_client.economy.coins

    async def get_balance(self, user_id: int) -> int:
        """Gets the balance of a user.
        AWAIT THIS.
        """
        doc = await self.col.find_one(
            {"user_id": user_id}
        )
        if doc is None:
            return 0
        else:
            return doc["amount"]

    async def insert_coins(self, user_id: int, amount: int):
        """Inserts coins into database.
        AWAIT THIS.
        """
        doc = await self.col.find_one(
            {"user_id": user_id}
        )

        if doc is None: # new user
            doc = await self.col.insert_one(
                {
                    "user_id": user_id,
                    "amount": amount
                }
            )
            return
        
        else:
            self.col.update_one(doc, {"$inc": {"amount" : amount}})

    async def remove_coins(self, user_id: int, amount: int):
        """Removes coins from database.
        AWAIT THIS.
        """
        doc = await self.col.find_one(
            {"user_id": user_id}
        )

        if doc is None: # new user
            doc = await self.col.insert_one(
                {
                    "user_id": user_id,
                    "amount": -amount
                }
            )
            return
        
        else:
            self.col.update_one(doc, {"$inc": {"amount" : -amount}}) # subtract
        

class Economy(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = Database_Manager(self.bot)

        self.dogecoin_emoji = "<a:DOGECOIN:920338187400925275>"

    @commands.command(aliases=["bal"])
    async def balance(self, ctx: commands.Context, user: discord.User = None):
        """Shows the balance of a person"""
        user = user or ctx.author
        balance = await self.db.get_balance(user.id)
        em = discord.Embed(title=f"{user.name}'s balance", description=f"{self.dogecoin_emoji} **{balance}**")
        await ctx.send(embed=em)

    @commands.is_owner()
    @commands.command(aliases=["ac"], hidden=True)
    async def add_coins(self, ctx, user: discord.User, amount: int):
        await self.db.insert_coins(user.id, amount)
        await ctx.send(f"Added {amount} coins to {user.name}#{user.discriminator}")

    @commands.is_owner()
    @commands.command(aliases=["rc"], hidden=True)
    async def remove_coins(self, ctx, user: discord.User, amount: int):
        await self.db.remove_coins(user.id, amount)
        await ctx.send(f"Removed {amount} coins from {user.name}#{user.discriminator}")


def setup(bot):
    bot.add_cog(Economy(bot))
    print("Economy cog is loaded")