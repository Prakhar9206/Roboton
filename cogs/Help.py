import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import textwrap
from typing import List, Tuple, Optional
import warnings
warnings.filterwarnings("ignore", message='Using slow pure-python SequenceMatcher. Install python-Levenshtein to remove this warning')
from thefuzz.process import extract


class CogSelect(discord.ui.Select):
    def __init__(self, ctx, cogs_list) -> None:
        super().__init__(placeholder="Select a category...", options=cogs_list)
        self.ctx: commands.Context = ctx
        self.cogs_list = cogs_list

    async def callback(self, interaction: discord.Interaction):
        values = self.values
        view: HelpView = self.view


        if values[0] == "Index": # sending index page
            # for item in view.children: # removing buttons and not the select menu
            #     if isinstance(item, discord.ui.Button):
            #         view.remove_item(item) 
            # idk why the above code doesnt work so i had to do this
            view.clear_items()
            view.add_item(self)

            return await interaction.response.edit_message(embed=view.index_embed, view=view)
            
        # sending cog help
        cog: commands.Cog = self.ctx.bot.get_cog(values[0])
        em = discord.Embed(title= f"{cog.qualified_name}\n{self.get_cog_help(cog)}\n\nClick on the button with the name of a command for more help on the command")

        cog_and_cmds = [f"**{self.get_command_signature(command)}**\n{self.get_command_help(command)}\n" for command in self.sorted_commands(cog)]
        em.description = "\n".join(cog_and_cmds)
        em.color = self.ctx.author.color

        view.clear_items()
        view.add_item(self)

        for command in self.sorted_commands(cog): # adding new buttons of selected cog
            view.add_item(CommandButton(self.ctx, command.name))
        view.add_item(QuitButton(self.ctx))
        await interaction.response.edit_message(embed=em, view=view)

    def get_command_help(self, command: commands.Command):
        if command.brief:
            return command.brief
        elif command.help:
            shortdoc = command.help.split("\n")[0]
            return f"{shortdoc}"
        else:
            return "No help found for this command..."
    
    def get_command_signature(self, command):
        return f"{self.ctx.clean_prefix}{command.qualified_name} {command.signature}"

    def get_cog_help(self, cog: commands.Cog) -> str:
        if cog.description:
            return cog.description
        return "No help found for this category..."

    def sorted_commands(self, cog: commands.Cog):
        key = lambda c: c.name
        _sorted_commands = sorted(cog.get_commands(), key=key)
        return _sorted_commands


class QuitButton(discord.ui.Button):
    def __init__(self, ctx: commands.Context):
        super().__init__(style=discord.ButtonStyle.red, label="Quit")
        self.ctx = ctx
    
    async def callback(self, interaction: discord.Interaction):
        self.view.stop()
        await self.view.message.delete()

class CommandButton(discord.ui.Button):
    """The button which will be added to a view.
    Its label will be the command name.
    Its callback will send an ephemeral message of the help of the command"""

    def __init__(self, ctx: commands.Context, label: str = None):
        super().__init__(label=label, style=discord.ButtonStyle.green)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        command: commands.Command = self.ctx.bot.get_command(self.label)
        em = discord.Embed(title=f"{self.get_command_signature(command)}", colour=self.ctx.author.colour)
        em.description = command.help or "No help found for this command..."

        alias = (command.aliases if (command.aliases) else "No aliases found for this command...")
        if alias != "No aliases found for this command...":
            em.add_field(name="Aliases", value=", ".join(alias), inline=False)

        elif alias == "No aliases found for this command...":
            em.add_field(name="Aliases", value=alias, inline=False)


        await interaction.response.send_message(embed=em, ephemeral=True)

    def get_command_signature(self, command: commands.Command):
        return f"{self.ctx.clean_prefix}{command.qualified_name} {command.signature}"



class HelpView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.timeout = 60
        self.ctx = ctx
        self.message: discord.Message

        #---------- index embed ------------------------------------------------
        self.index_embed = discord.Embed(title="Roboton Help", color=self.ctx.author.color)
        self.index_embed.description = textwrap.dedent(f"""
        Hello! Welcome to the help page.

        Use "<prefix>help command" for more info on a command.
        Use "<prefix>help category" for more info on a category.
        Use the dropdown menu below to select a category.""")

        self.index_embed.add_field(name="How to read the help command signature?",
        value="Help command signatures are very easy to read.", inline=False)

        self.index_embed.add_field(name="[arguement]",
        value="This means that the arguement is **__optional__**", inline=False)

        self.index_embed.add_field(name="<arguement>",
        value="This means that the arguement is **__required__**", inline=False)

        self.index_embed.add_field(name="[A|B]",
        value="This means that the arguement can be **__either A or B__**", inline=False)

        self.index_embed.add_field(name="[arguement...]",
        value="This means you can pass multiple arguements.", inline=False)

        self.index_embed.add_field(name="Note", value="**__You do not need to type the brackets__**", inline=False)

        self.index_embed.add_field(name="Support Server", value="You can join the official server for more help. https://discord.gg/kqMXRmduuU",
        inline=False)


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        else:
            await interaction.response.send_message(f"You cannot use this select menu. Sorry!\nType `{self.ctx.clean_prefix}help` to use the help command", ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        self.stop()
        return await self.message.edit(view=self)


class ErrorHandlingView(discord.ui.View):
    def __init__(self, ctx: commands.Command):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.message : discord.Message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            return True
        else:
            await interaction.response.send_message(f"You cannot use these buttons", ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        self.stop()
        return await self.message.edit(view=self)


class MyHelp(commands.HelpCommand):

    def __init__(self):
        super().__init__(
            command_attrs={
                'cooldown' : commands.CooldownMapping(commands.Cooldown(2, 10,), type=BucketType.member)
            }
        )

    def get_command_signature(self, command):
        ctx = self.context
        return f"{ctx.clean_prefix}{command.qualified_name} {command.signature}"

    def get_command_name(self, command):
        return str(command.qualified_name)

    def get_visible_and_sorted_commands(self, commands):
        visible_commands = []
        for cmd in commands:
            if not cmd.hidden:
                visible_commands.append(cmd)

        key = lambda c: c.name
        sorted_commands = sorted(visible_commands, key=key)
        return sorted_commands

    def get_command_help(self, command: commands.Command):
        if command.help:
            return command.help
        else:
            return "No help found for this command..."

    def sort_cogs_SelectOptions(self, cogs: List[discord.SelectOption]):
        key = lambda options: options.label # SelectOption.label
        raw_sorted_cogs = sorted(cogs, key=key)
        sorted_cogs = [discord.SelectOption(label="Index", description="Shows the default help page of the bot")] + raw_sorted_cogs
        return sorted_cogs

    def get_cog_help(self, cog: commands.Cog) -> str:
        if cog.description:
            return cog.description
        return "No help found for this category..."

    # ------- bot help --------------
    async def send_bot_help(self, mapping):
        ctx = self.context
        # cogs_list = [discord.SelectOption(label="Index", description="Shows the default help page of the bot")]
        cogs_list = []
        ignored_cogs = ("error_handler", "no category", "logging", "evaluate")


        # --------------------- sending index page --------------------

        for cog, commands in mapping.items():
            visible_and_sorted_commands = self.get_visible_and_sorted_commands(commands)
            raw_command_names_list = [self.get_command_name(com) for com in visible_and_sorted_commands]

            if raw_command_names_list:
                cog_name = getattr(cog, "qualified_name", "No Category")
                if cog_name.lower() not in ignored_cogs:
                    cog_description = getattr(cog, "description", "No help found...")

                    cogs_list.append(discord.SelectOption(label=cog_name, description=cog_description))

        sorted_cogs_list = self.sort_cogs_SelectOptions(cogs_list)
        view = HelpView(ctx)
        view.add_item(CogSelect(ctx, sorted_cogs_list))
        view.message = await ctx.send(embed=view.index_embed, view=view)

    # --------- cog help ------------
    async def send_cog_help(self, cog: commands.Cog):
        ctx = self.context
        cog_commands = cog.get_commands()
        em = discord.Embed(title=f"{cog.qualified_name}\n{self.get_cog_help(cog)}\n\nClick on the button with the name of a command for more help on the command")
        em.color = ctx.author.color

        visible_and_sorted_commands = self.get_visible_and_sorted_commands(cog_commands)
        cog_and_cmds = [f"**{self.get_command_signature(command)}**\n{self.get_command_help(command)}\n" for command in visible_and_sorted_commands]

        em.description = "\n".join(cog_and_cmds)
        view = HelpView(ctx)
        for command in visible_and_sorted_commands:
            view.add_item(CommandButton(ctx, command.name))
        view.add_item(QuitButton(ctx))
        view.message = await ctx.send(embed=em, view=view)

    # --------- command help ------------------
    async def send_command_help(self, command: commands.Command):
        ctx = self.context
        if not command.hidden:
            embed = discord.Embed(title=self.get_command_signature(command))
            desc = command.help if (command.help) else "No help found for this command..."
            embed.add_field(name="Help", value=desc)
            embed.color=ctx.author.color

            alias = (command.aliases if (command.aliases) else "No aliases found for this command...")
            if alias != "No aliases found for this command...":
                embed.add_field(name="Aliases", value=", ".join(alias), inline=False)
                await ctx.send(embed=embed)
            elif alias == "No aliases found for this command...":
                embed.add_field(name="Aliases", value=alias, inline=False)
                await ctx.send(embed=embed)
        else: # hidden commands shall be hidden
            await ctx.send(f'No command called "{command}" found.')

    async def send_error_message(self, error: Tuple[str, str, Optional[commands.Group]]) -> None:
        await self.handle_error_message(*error)

    def command_not_found(self, string: str) -> Tuple[str, str]:
        return super().command_not_found(string), string

    async def handle_error_message(self, error: str, command: str, group: Optional[commands.Group] = None) -> None:
        ctx = self.context

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
        command_names = [cmd.name for cmd in ctx.bot.commands]

        for cmd in raw_commands:
            raw_aliases = cmd.aliases
            if raw_aliases:
                for alias in raw_aliases:
                    aliases.append(alias)


        to_search = command_names + aliases
        # with warnings.catch_warnings():
        #     warnings.simplefilter("ignore")
        raw_new_cmds = extract(command, to_search, limit=3)

        new_cmds = [cmd[0] for cmd in raw_new_cmds]
        view = ErrorHandlingView(ctx)
        for cmd in new_cmds:
            view.add_item(CommandButton(ctx, cmd))
        view.add_item(QuitButton(ctx))
        view.message = await ctx.reply(f"No command called {command} was found. Did you mean?", view=view)

def setup(bot: commands.Bot):
    bot.old_help_command = bot.help_command
    cog = bot.get_cog("cogs.Others")
    bot.help_command.cog = cog
    bot.help_command = MyHelp()
    print("Help cog is loaded")