import discord
from discord.ext import commands
from cogs.Economy import Database_Manager
from typing import List


class Item:
    def __init__(self, name: str, price: int, emoji: str = "<:blank:885545215065206856>", description: str = "No description provided.") -> None:
        self.name: str = name
        self.description: str = description
        self.price: int = price
        self.emoji: str = emoji

class Inventory_Manager:
    def __init__(self, bot, items) -> None:
        self.bot = bot
        self.col = self.bot.mongo_client.inventory.items
        self.items: List[Item] = items

    async def insert_item(self, user_id: int, item_name: str, number: int =1):
        """Inserts an item into database.
        AWAIT THIS.
        """
        item = self.getItemFromName(item_name)
        doc = await self.col.find_one(
            {"user_id": user_id}
        )

        if doc is None: # new user
            doc = await self.col.insert_one(
                {
                    "user_id": user_id,
                    f"{item.name}": number,
                }
            )
            return
        
        else:
            self.col.update_one(doc, {"$inc": {f"{item.name}" : number}})

    async def remove_item(self, user_id: int, item_name: str, number: int =1):
        """Removes an item from database.
        AWAIT THIS.
        """
        item = self.getItemFromName(item_name)
        doc = await self.col.find_one(
            {"user_id": user_id}
        )

        if doc is None: # new user
            doc = await self.col.insert_one(
                {
                    "user_id": user_id,
                    f"{item.name}": -number,
                }
            )
            return
        
        else:
            self.col.update_one(doc, {"$inc": {f"{item.name}" : -number}}) # subtract


    def get_price(self, item_name: str) -> int:
        """Returns the price of an item."""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item.price

    def getItemFromName(self, item_name: str) -> Item:
        """Returns an `Item` from its name."""
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item

    def get_all_items(self, user_id):
        pass

class Market(commands.Cog, name="Market"):
    """Market."""
    def __init__(self,bot):
        self.bot = bot
        self.eco_db = Database_Manager(self.bot)
        self.dogecoin_emoji = "<a:DOGECOIN:920338187400925275>"

        self.items = [
            Item("Laptop", 800, "<:Laptop:924301374383071282>",  "Just a laptop."),
        ]
        self.items_db = Inventory_Manager(self.bot, self.items)
        self.item_names = [item.name.lower() for item in self.items]




    @commands.command()
    async def shop(self, ctx: commands.Context):
        """Shows the items available in shop."""
        em = discord.Embed(title="Roboton Shop", color=0xf59042)
        em.description = ""
        for item in self.items:
            em.description += f"{item.emoji} **{item.name}** ─ {self.dogecoin_emoji}{item.price}\n{item.description}"
        
        await ctx.send(embed=em)

    @commands.command()
    async def buy(self, ctx: commands.Context, item: str, amount: int = 1):
        """Buys an item from the shop."""
        if item.lower() in self.item_names:
            bal = await self.eco_db.get_balance(ctx.author.id)
            price = self.items_db.get_price(item)
            if bal >= price:
                await self.eco_db.remove_coins(ctx.author.id, price)
                await self.items_db.insert_item(ctx.author.id, item, amount)
                await ctx.send(f"You purchased a {item}.")
            else:
                await ctx.send("You do not have enough money to buy this item.")
        else:
            await ctx.send("Invalid item!")

    
    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx: commands.Context):
        """Shows you your inventory."""
        pass




def setup(bot):
    bot.add_cog(Market(bot))
    print("Market cog is loaded")
