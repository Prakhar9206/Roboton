from typing import List, Tuple
from mazelib import Maze
from mazelib.generate.Prims import Prims
from mazelib.generate.Ellers import Ellers
import discord
from discord.ext import commands
import time
from mazelib.solve.BacktrackingSolver import BacktrackingSolver
import random





class myMaze(Maze): # just overrides the default to_string function to return player as well
    def __init__(self, seed=None):
        super().__init__(seed=seed)

    def tostring(self, entrances=False, solutions=False, player=False, player_position: Tuple[int, int]=None):
        """ Return a string representation of the maze.
        This can also display the maze entrances/solutions IF they already exist.

        Args:
            entrances (bool): Do you want to show the entrances of the maze?
            solutions (bool): Do you want to show the solution to the maze?
        Returns:
            str: string representation of the maze
        """
        if self.grid is None:
            return ''

        # build the walls of the grid
        txt = []
        for row in self.grid:
            txt.append(''.join(['#' if cell else ' ' for cell in row]))

        # insert the start and end points
        if entrances and self.start and self.end:
            r, c = self.start
            txt[r] = txt[r][:c] + 'S' + txt[r][c + 1:]
            r, c = self.end
            txt[r] = txt[r][:c] + 'E' + txt[r][c + 1:]

        # if extant, insert the solution path
        if solutions and self.solutions:
            for r, c in self.solutions[0]:
                txt[r] = txt[r][:c] + '+' + txt[r][c + 1:]
        
        # show player based on the given player_position
        if player:
            r, c = player_position
            txt[r] = txt[r][:c] + '@' + txt[r][c + 1:]

        return '\n'.join(txt)


class ViewManager():
    def __init__(self, ctx: commands.Context, killer: discord.Member, member1: discord.Member=None, member2: discord.Member=None) -> None:

        self.member2 = member2
        self.stats_message: discord.Message

        self.seed = int(time.time())
        self.maze = myMaze(seed=self.seed)
        self.rows = 10 if member2 else 8
        self.cols = 10 if member2 else 8
        self.maze.generator = Ellers(self.rows, self.cols) # works nicely
        self.maze.generate()
        self.maze.generate_entrances()
        self.keys = []
        self.spawn_position = self.get_spawn_position(self.maze.start, self.maze.grid)
        self.spawn_keys()
        self.killer_emoji = "<:impostor:927976226025508925>"
        
        self.survivors__ = {ctx.author, member1}
        if member2:
            self.survivors__.add(member2)
        self.survivors__.remove(killer)
        # self.survivors_.remove(None)
        self.survivors = list(self.survivors__)
        # print(self.survivors)

        self.door_locked = True
        self.alive_people_left = 2 if member2 else 1
        self.total_survivors = 2 if member2 else 1
        self.escaped_survivors = 0
        self.dead_survivors = 0

        self.p1_emoji = self.killer_emoji if ctx.author == killer else "<:AmongusBlue:927937423227359263>"

        if member1 == killer: # p2
            self.p2_emoji = self.killer_emoji
        elif self.p1_emoji == "<:AmongusBlue:927937423227359263>": # p1 is not killer, we are not killer too
            self.p2_emoji = "<:AmongusLime:927937583676268647>"
        elif ctx.author == killer:
            self.p2_emoji = "<:AmongusBlue:927937423227359263>"

        self.p3_emoji = self.killer_emoji if member2 == killer else "<:AmongusLime:927937583676268647>"


        self.player1_view = _2dmazeView(ctx, killer, self, ctx.author, self.p1_emoji, member1, member2)
        self.player2_view = _2dmazeView(ctx, killer, self, member1, self.p2_emoji, member1, member2)


        if member2:
            self.player3_view = _2dmazeView(ctx, killer, self, member2, self.p3_emoji, member1, member2)

        # player1
        self.player1_view.p1_view = self.player1_view

        self.player1_view.p2_view = self.player2_view
        if member2:
            self.player1_view.p3_view = self.player3_view
        # self.player1_view.update_buttons()

        # player2
        self.player2_view.p2_view = self.player2_view

        self.player2_view.p1_view = self.player1_view
        if member2:
            self.player2_view.p3_view = self.player3_view
        # self.player2_view.update_buttons()

        # player3
        if member2:
            self.player3_view.p3_view = self.player3_view

            self.player3_view.p1_view = self.player1_view
            self.player3_view.p2_view = self.player2_view
            # self.player3_view.update_buttons()

    def get_spawn_position(self, start: Tuple[int, int], grid: List[List[int]]):
        """Returns a Tuple(int, int) of the coordinates where the player should be spawned"""
        # some of them can be invalid based on mazes
        neighbours = (
            (start[0]-1, start[1]), # up
            (start[0]+1, start[1]), # down
            (start[0], start[1]+1), # right
            (start[0], start[1]-1), # left
        )

        for neighbour in neighbours: # one of them has to be 0
            try:
                if grid[neighbour[0]][neighbour[1]] == 0:
                    return neighbour
                
            except Exception:
                continue


    def spawn_keys(self):
        rows = self.rows * 2
        cols = self.cols * 2

        total_keys = 2 if self.member2 else 1
        possible_spots = []

        for r in range(1, rows, 2):
            for c in range(1, cols, 2):
                if (r,c) != self.spawn_position:
                    possible_spots.append((r,c))

        self.keys = random.choices(possible_spots, k=total_keys)




class MovementButton(discord.ui.Button):
    def __init__(self, emoji: str, row: int, direction: str):
        super().__init__(style=discord.ButtonStyle.green, emoji=emoji, row=row)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        view: _2dmazeView = self.view

        if self.direction == "up":
            view.current_position = (view.current_position[0]-1, view.current_position[1])
        elif self.direction == "left":
            view.current_position = (view.current_position[0], view.current_position[1]-1)
        elif self.direction == "right":
            view.current_position = (view.current_position[0], view.current_position[1]+1)
        elif self.direction == "down":
            view.current_position = (view.current_position[0]+1, view.current_position[1])

        view.update_embed()
        
        if view.end_reached():
            view.disable_buttons()
        else:
            view.update_buttons()
        await interaction.response.edit_message(embed=view.embed, view=view)
        view.processing = False

        if (view.current_position in view.vm.keys) and (view.is_killer is False): # only survivors can pick up keys
            view.vm.keys.remove(view.current_position)
         
            # open the door when all keys are picked up
            if len(view.vm.keys) == 0:
                view.vm.door_locked = False

            msg = self.create_stats_message()
            await view.vm.stats_message.edit(content=msg)

        # check if survivors won
        # print(f"escaped survivors = {view.vm.escaped_survivors}, total survivors = {view.vm.total_survivors}")
        if view.vm.escaped_survivors == view.vm.total_survivors:
            view.vm.stats_message = view.ctx.bot.get_message(view.vm.stats_message.id)
            content = view.vm.stats_message.content

            if view.vm.total_survivors == 1:
                content += f"\n__**{view.vm.survivors[0].name}**__ has escaped the maze!"
            if view.vm.total_survivors == 2:
                content += f"\n__**{view.vm.survivors[0].name}**__ and __**{view.vm.survivors[1].name}**__ have escaped the maze!"
            await view.vm.stats_message.edit(content=content)

            if view.p1_view.is_killer:
                view.p1_view.disable_buttons()
                view.p1_view.stop()
                await view.p1_view.message.edit(content="The survivors have escaped. You lost!", view=view.p1_view)

            elif view.p2_view.is_killer:
                view.p2_view.disable_buttons()
                view.p2_view.stop()
                await view.p2_view.message.edit(content="The survivors have escaped. You lost!", view=view.p2_view)

            elif view.p3_view.is_killer:
                view.p3_view.disable_buttons()
                view.p3_view.stop()
                await view.p3_view.message.edit(content="The survivors have escaped. You lost!", view=view.p3_view)

        elif view.is_killer: # killer

            # kill people
            if (view.player.id != view.p1_view.player.id) and (view.current_position == view.p1_view.current_position):
                view.p1_view.disable_buttons()
                view.p1_view.stop()
                view.p1_view.is_alive = False
                view.p1_view.receive_edits = False
                view.p1_view.player_emoji = "<:blank:885545215065206856>" 

                view.vm.alive_people_left -= 1
                view.vm.dead_survivors += 1
                await view.p1_view.message.edit(content="You died!", view=view.p1_view)
                content = self.create_stats_message()
                await view.vm.stats_message.edit(content=content)
            
            elif (view.player.id != view.p2_view.player.id) and (view.current_position == view.p2_view.current_position):
                view.p2_view.disable_buttons()
                view.p2_view.stop()
                view.p2_view.is_alive = False
                view.p2_view.receive_edits = False
                view.p2_view.player_emoji = "<:blank:885545215065206856>" 

                view.vm.alive_people_left -= 1
                view.vm.dead_survivors += 1
                await view.p2_view.message.edit(content="You died!", view=view.p2_view)
                content = self.create_stats_message()
                await view.vm.stats_message.edit(content=content)

            elif (view.player.id != view.p3_view.player.id) and (view.current_position == view.p3_view.current_position):
                view.p3_view.disable_buttons()
                view.p3_view.stop()
                view.p3_view.is_alive = False
                view.p3_view.receive_edits = False
                view.p3_view.player_emoji = "<:blank:885545215065206856>" 

                view.vm.alive_people_left -= 1
                view.vm.dead_survivors += 1
                await view.p3_view.message.edit(content="You died!", view=view.p3_view)
                content = self.create_stats_message()
                await view.vm.stats_message.edit(content=content)

            # check if killer won
            if view.vm.alive_people_left == 0: # all survivors dead
                view.disable_buttons()
                await view.message.edit(content=f"You won!", view=view)
                content = view.vm.stats_message.content
                content += f"\n__**{view.killer}**__ has won as the killer!"
                await view.vm.stats_message.edit(content=content)

        # one survivor escaped but the other survivor died
        if (view.vm.escaped_survivors == 1) and (view.vm.dead_survivors == 1):

            # editing killers message
            if view.p1_view.is_killer:
                view.p1_view.disable_buttons()
                view.p1_view.stop()
                await view.p1_view.message.edit(content="You won but you could had done better.", view=view.p1_view)

            elif view.p2_view.is_killer:
                view.p2_view.disable_buttons()
                view.p2_view.stop()
                await view.p2_view.message.edit(content="You won but you could had done better.", view=view.p2_view)

            elif view.p3_view.is_killer:
                view.p3_view.disable_buttons()
                view.p3_view.stop()
                await view.p3_view.message.edit(content="You won but you could had done better.", view=view.p3_view)

            # stats message
            msg = self.create_stats_message()
            msg += f"\n__**{view.vm.survivors[0].name}**__ has escaped the maze."
            await view.vm.stats_message.edit(content=msg)

        # if we move in the range of some other user
        if view.player.id == view.p1_view.player.id:
            view.p2_view.embed.description = view.p2_view.create_map()
            view.p3_view.embed.description = view.p3_view.create_map()

        elif view.player.id == view.p2_view.player.id:
            view.p1_view.embed.description = view.p1_view.create_map()
            view.p3_view.embed.description = view.p3_view.create_map()

        elif view.player.id == view.p3_view.player.id:
            view.p1_view.embed.description = view.p1_view.create_map()
            view.p2_view.embed.description = view.p2_view.create_map()

        view.p1_view.message = view.ctx.bot.get_message(view.p1_view.message.id)
        view.p2_view.message = view.ctx.bot.get_message(view.p2_view.message.id)
        view.p3_view.message = view.ctx.bot.get_message(view.p3_view.message.id)

        if (view.p1_view.player.id != view.player.id) and (view.p1_view.receive_edits is True) and (view.p1_view.embed.description != view.p1_view.message.embeds[0].description) and (view.p1_view.processing is False):
            await view.p1_view.message.edit(embed=view.p1_view.embed)
            view.p1_view.processing = False

        if (view.p2_view.player.id != view.player.id) and (view.p2_view.receive_edits is True) and (view.p2_view.embed.description != view.p2_view.message.embeds[0].description) and (view.p2_view.processing is False):
            await view.p2_view.message.edit(embed=view.p2_view.embed)
            view.p2_view.processing = False

        if (view.p3_view.player.id != view.player.id) and (view.p3_view.receive_edits is True) and (view.p3_view.embed.description != view.p3_view.message.embeds[0].description) and (view.p3_view.processing is False):
            await view.p3_view.message.edit(embed=view.p3_view.embed)
            view.p3_view.processing = False

        # print(f"alive ppl - {view.vm.alive_people_left}")

    def create_stats_message(self) -> str:
        view: _2dmazeView = self.view
        string = f"__**{view.killer.name}**__ : <:impostor:927976226025508925>\n"

        choices = {view.player1, view.player2}
        if view.player3:
            choices.add(view.player3)
        choices.remove(view.killer)

        for member in choices:
            if view.p1_view.player.id == member.id:
                string += f"{member.name} : {view.p1_view.stats_emoji}"
                if view.p1_view.is_alive is False:
                    string += "- DEAD"
                elif view.p1_view.has_escaped is True:
                    string += "- ESCAPED"
                string += "\n"

            elif view.p2_view.player.id == member.id:
                string += f"{member.name} : {view.p2_view.stats_emoji}"
                if view.p2_view.is_alive is False:
                    string += "- DEAD"
                elif view.p2_view.has_escaped is True:
                    string += "- ESCAPED"
                string += "\n"

            elif view.p3_view.player.id == member.id:
                string += f"{member.name} : {view.p3_view.stats_emoji}"
                if view.p3_view.is_alive is False:
                    string += "- DEAD"
                elif view.p3_view.has_escaped is True:
                    string += "- ESCAPED"
                string += "\n"

        string = f"{string}\n{len(view.vm.keys)} <:goldKey:929034929571000370> remaining\n{'The exit is now open!' if len(view.vm.keys) == 0 else ''}"

        return string

class BlankButton(discord.ui.Button):
    def __init__(self, row: int):
        super().__init__(emoji="<:blank:885545215065206856>", disabled=True, row=row, style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()



class _2dmazeView(discord.ui.View):

    def __init__(self, ctx: commands.Context, killer: discord.Member, View_Manager, player: discord.Member, player_emoji: str, member1: discord.Member=None, member2: discord.Member=None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.player = player
        self.killer = killer
        self.is_killer = True if self.player.id == self.killer.id else False
        self.vm: ViewManager = View_Manager
        self.is_alive = True
        self.has_escaped = False
        self.receive_edits = True
        self.stats_emoji = player_emoji

        self.player1 = ctx.author
        self.player2 = member1
        self.player3 = member2

        # two of these will be changed by manager class
        self.p1_view: _2dmazeView = self
        self.p2_view: _2dmazeView = self
        self.p3_view: _2dmazeView = self

        self.current_position: Tuple[int, int]
        self.message: discord.Message
        self.embed = discord.Embed()


        self.red_emoji = "<:AmongusRed:927937251890057246>" # player1
        self.blue_emoji = "<:AmongusBlue:927937423227359263>" # player2
        self.lime_emoji = "<:AmongusLime:927937583676268647>" # player3
        self.player_emoji = "<:impostor:927976226025508925>" if self.is_killer else player_emoji

        self.spawn_position = self.vm.spawn_position
        self.current_position = self.spawn_position

        self.embed.title = f"{self.player.name}"
        self.embed.description = self.create_map()

        self.add_buttons()
        self.update_buttons()

        # for the cooldown at beginning
        if self.is_killer:
            self.disable_buttons()

        # spam protection
        self.processing = False

        # print(self.vm.maze.tostring(True, True, True, (self.current_position)))


    def add_buttons(self):
        # row 0
        self.add_item(BlankButton(0))
        self.add_item(MovementButton("\N{UPWARDS BLACK ARROW}", 0, "up"))
        self.add_item(BlankButton(0))

        # row 1
        self.add_item(MovementButton("\N{LEFTWARDS BLACK ARROW}", 1, "left"))
        self.add_item(BlankButton(1))
        self.add_item(MovementButton("\N{BLACK RIGHTWARDS ARROW}", 1, "right"))

        # row 2
        self.add_item(BlankButton(2))
        self.add_item(MovementButton("\N{DOWNWARDS BLACK ARROW}", 2, "down"))
        self.add_item(BlankButton(2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # if (interaction.user.id == self.ctx.author.id) or (interaction.user.id == self.player.id):
        if interaction.user.id == self.player.id:
            return True
        else:
            return await interaction.response.send_message("You cannot control this character.", ephemeral=True)

    def create_map(self) -> str:
        """generates a 7x7 view of given index.
        `ignored_users` is a list of `discord.Member.id` to prevent infinite loops of editing messages.
        """

        # self.processing = True

        max_rows = self.vm.rows * 2 # index
        max_cols = self.vm.cols * 2 # index
        side = 5 if self.is_killer else 7
        offset = side//2
        # T - top
        # B - bottom
        # R - right
        # L - left


        row: int = self.current_position[0]
        col: int = self.current_position[1]
        tl = [row - offset, col - offset]
        br = [row + offset, col + offset]

        TL_row, TL_col = tl
        BR_row, BR_col = br

        if TL_row < 0: # row of TL
            tl[0] = 0
            br[0] = side - 1

        if TL_col < 0: # col of TL
            tl[1] = 0
            br[1] = side - 1

        if BR_row > max_rows: # row of BR 
            br[0] = max_rows # -1
            tl[0] = max_rows - side + 1

        if BR_col > max_cols: # col of BR 
            br[1] = max_cols # -1
            tl[1] = max_cols - side + 1

        string = ""

        for row in range(tl[0], br[0]+1):
            # print(maze[row])
            for col in range(tl[1], br[1]+1):
                try:
                    cell = self.vm.maze.grid[row][col]

                    if (row,col) == (self.current_position):
                        string += self.player_emoji

                    elif ((row,col) == self.vm.maze.end) and (self.vm.door_locked is False):
                        string += "\N{DOOR}"

                    # killer
                    elif ((row,col) == self.p1_view.current_position) and (self.p1_view.player.id != self.player.id) and (self.p1_view.is_killer): 
                        string += self.p1_view.player_emoji

                    elif ((row,col) == self.p2_view.current_position) and (self.p2_view.player.id != self.player.id) and (self.p2_view.is_killer): 
                        string += self.p2_view.player_emoji

                    elif ((row,col) == self.p3_view.current_position) and (self.p3_view.player.id != self.player.id) and (self.p3_view.is_killer): 
                        string += self.p3_view.player_emoji

                    # remaining players
                    elif ((row,col) == self.p1_view.current_position) and (self.p1_view.player.id != self.player.id): 
                        string += self.p1_view.player_emoji

                    elif ((row,col) == self.p2_view.current_position) and (self.p2_view.player.id != self.player.id): 
                        string += self.p2_view.player_emoji

                    elif ((row,col) == self.p3_view.current_position) and (self.p3_view.player.id != self.player.id): 
                        string += self.p3_view.player_emoji

                    elif (row, col) in self.vm.keys:
                        string += "<:goldKey:929034929571000370>"

                    elif (row,col) == self.vm.maze.start: # red square emoji
                        string += "\N{LARGE RED SQUARE}"
                    elif ((row,col) == self.vm.maze.end) and (self.vm.door_locked is True):
                        string += "\N{LOCK}"
                    elif cell == 1: # wall
                        string += "\N{LARGE YELLOW SQUARE}"
                    elif cell == 0: # open
                        string += "<:blank:885545215065206856>"
                    

                except IndexError:
                    print(f"row = {row}, col = {col}, TL = {tl}, BR = {br}")
            string += "\n"

        # self.processing = False
        return string[:-1] # remove last \n as it causes bugs when comparing with embed

    def update_embed(self):
        self.processing = True
        self.embed.description = self.create_map()

        if self.end_reached():
            self.embed.title = f"{self.player.name} has escaped the maze!"
            self.receive_edits = False
            self.disable_buttons()
            self.stop()
            self.vm.escaped_survivors += 1
            self.has_escaped = True

    def update_buttons(self):

        neighbours = (
            (self.current_position[0], self.current_position[1]-1), # left
            (self.current_position[0], self.current_position[1]+1), # right
            (self.current_position[0]+1, self.current_position[1]), # down
            (self.current_position[0]-1, self.current_position[1]), # up
        )

        buttons = {
            "0" : 3,
            "1" : 5,
            "2" : 7,
            "3" : 1,
        }

        for index, neighbour in enumerate(neighbours): # one of them has to be 0

            try:
                r,c = neighbour
                # enabling paths
                btn_index = buttons[str(index)]
                button: discord.ui.Button = self.children[btn_index]

                if (self.vm.maze.grid[r][c] == 0):
                    button.disabled = False

                # disable walls
                if ((self.vm.maze.grid[r][c] == 1) or (self.vm.maze.grid[r][c] == self.vm.maze.start)) or (self.vm.maze.grid[r][c] != self.vm.maze.end):
                    button.disabled = True

                # disabling end if keys are remaining 
                if (neighbour == self.vm.maze.end) and (len(self.vm.keys) > 0):
                    button.disabled = True

                # enabling end if all keys are found
                if (neighbour == self.vm.maze.end) and (len(self.vm.keys) == 0):
                    button.disabled = False

                # disabling end if all keys are found and we are killer
                if (self.is_killer) and (neighbour == self.vm.maze.end) and (len(self.vm.keys) == 0):
                    button.disabled = True

            except Exception:
                pass
    
    def end_reached(self):
        if self.current_position == self.vm.maze.end:
            return True
        return False

    def disable_buttons(self):
        for button in self.children:
            button.disabled = True