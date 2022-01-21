from typing import List
import discord
import traceback
import sys
from discord.ext import commands
from utils.custom_errors import Suspended
import warnings
warnings.filterwarnings("ignore", message='Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')
from thefuzz.process import extract

from cogs.Help import ErrorHandlingView, CommandButton, QuitButton

class Error_handler(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
    
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        # ignored = (commands.CommandNotFound)
        ignored = ()
        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandNotFound):

            if (ctx.prefix == f"<@{self.bot.user.id}> ") or (ctx.prefix == f"<@!{self.bot.user.id}> "):
                return
            # print(ctx.invoked_with)
            ignored_cogs = ("Admin")
            raw_commands: List[commands.Command] = []
            for cmd in ctx.bot.commands:
                cog = cmd.cog
                if cog:
                    if cog.qualified_name not in ignored_cogs:
                        raw_commands.append(cmd)
                else: # if a command is not in any cog, we will pass
                    pass
            # aliases = [a for a in cmd.aliases for cmd in raw_commands if cmd.aliases]
            aliases = []
            command_names = [cmd.name for cmd in raw_commands]

            for cmd in raw_commands:
                raw_aliases = cmd.aliases
                if raw_aliases:
                    for alias in raw_aliases:
                        aliases.append(alias)

            to_search = command_names + aliases
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore")
            raw_new_cmds = extract(ctx.invoked_with, to_search, limit=3)

            new_cmds = [cmd[0] for cmd in raw_new_cmds]
            # print(new_cmds)
            view = ErrorHandlingView(ctx)
            for cmd in new_cmds:
                view.add_item(CommandButton(ctx, cmd))
            view.add_item(QuitButton(ctx))
            view.message = await ctx.reply(f"No command called {ctx.invoked_with} was found. Did you mean?", view=view)


        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} cannot be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.CommandOnCooldown):
            em = discord.Embed(title="Spam is not cool lol", description = "Try again in {:.2f} seconds".format(error.retry_after))
            em.colour = ctx.author.colour
            await ctx.send(embed=em)
        
        elif isinstance(error, commands.BadArgument):
            em = discord.Embed(title="You made a typing mistake while writing this command", description=f"The correct usage is\n{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}")
            em.color = ctx.author.color
            await ctx.send(embed=em)
        
        elif isinstance(error, commands.MissingPermissions):

            em = discord.Embed(title="You are missing the following permissions to use this command", description=f"{', '.join(error.missing_permissions)}")
            em.color = ctx.author.color
            await ctx.send(embed=em)

        elif isinstance(error, commands.MaxConcurrencyReached):
            em = discord.Embed(title="This command is already being used by someone. Please wait before using this command again")
            em.color = ctx.author.color
            await ctx.send(embed=em)

        elif isinstance(error, Suspended):

            # em = discord.Embed(title="You have been blocked from using this bot for the following reason")
            # em.description = error
            # em.color = 0xfc0335
            # await ctx.send(embed=em)
            pass
            

        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            em = discord.Embed(title="Error", description=f"{error}", colour=0xeb0808)
            await ctx.send(embed=em)

        error_logs = self.bot.get_channel(891165131449446400)
        em = discord.Embed(title=f"An error in command {ctx.command}")
        em.description = f"{error}"
        em.add_field(name=f"Message", value=f"{ctx.message.content}", inline=False)
        em.add_field(name= "Command used by", value=f"{ctx.author}", inline=False)
        em.add_field(name="Channel", value=f"{ctx.channel}\n{ctx.channel.id}", inline=False)
        em.add_field(name="Server", value=f"{ctx.guild.name}\n{ctx.guild.id}", inline=False)
        em.add_field(name= "Message URL", value=ctx.message.jump_url, inline=False)
        em.color = 0xd60b0b
        await error_logs.send(embed=em)

def setup(bot):
    bot.add_cog(Error_handler(bot))
    print("Error handling cog is loaded")
