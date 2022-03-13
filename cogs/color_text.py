import discord
from discord.ext import commands

class Colortext(commands.Cog, name="Colortext", description="All fun commands."):
    
    def __init__(self,bot):
        self.bot: commands.Bot = bot
        self.text_dict = {
            "grey" : "30",
            "red" : "31",
            "green" : "32",
            "yellow" : "33",
            "blue" : "34",
            "pink" : "35",
            "cyan" : "36",
            "white" : "37",
        }
        self.background_dict = {
            "blue" : "40",
            "orange" : "41",
            "grey" : "42",
            "light_grey" : "43",
            "very_light_grey" : "44",
            "indigo" : "45",
            "again_grey" : "46",
            "white" : "47",

            "lg" : "43", # shortcuts
            "vlg" : "44",
            "ag" : "46"
        }

    @commands.command()
    async def ct(self, ctx: commands.Context, *, text: str = ""):
        """Changes the provided text into colorful text.
        Format: `+ct [background_color text_color]type text here`
        NOTE - typing `[]` is necessary in this command.
        Available backgrounds colors - blue, orange, grey, light_grey or lg, very_light_grey or vlg, again_grey or ag, white.
        Available text colors - grey, red, green, yellow, blue, pink, cyan, white.
        """
        # `text` will be like "[bgcolor textcolor]text here"

        # editing the background part
        if text == "":
            return await ctx.send("No text provided.")
        for k,v in self.background_dict.items():
            text = text.replace(f"[{k} ", f"[{v};")
        # editing the text part
        for k,v in self.text_dict.items():
            text = text.replace(f";{k}]", f";{v}m")
        print(text)
        await ctx.send(f"```ansi\n{text}\n```\n\nCopy raw text\n\```ansi\n{text}\n```")

def setup(bot):
    bot.add_cog(Colortext(bot))
    print("Colortext cog is loaded")