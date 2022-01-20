import random
from typing import Dict, List, Tuple
from mazelib import Maze
from mazelib.generate.Prims import Prims
from mazelib.generate.BacktrackingGenerator import BacktrackingGenerator
from mazelib.generate.HuntAndKill import HuntAndKill
import discord
from discord.ext import commands
from PIL import Image
import asyncio
from io import BytesIO
from cogs.Economy import Database_Manager


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


# buttons
class BlankButton(discord.ui.Button):
    def __init__(self, row: int):
        super().__init__(emoji="<:blank:885545215065206856>", disabled=True, row=row, style=discord.ButtonStyle.grey)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class DirectionButton(discord.ui.Button):
    """The button which just changes your direction.
    It does NOT changes your position.
    """

    def __init__(self, label: str = None, row: int = None, direction: str = None):
        super().__init__(label=label, row=row, style=discord.ButtonStyle.green)
        self.direction = direction

    async def callback(self, interaction: discord.Interaction):
        view: _3dmazeView = self.view

        view.processing = True
        view.change_direction(self.direction)

        sprites = view.get_sprites(view.current_position)
        key = await view.generate_key(sprites)
        url = view.colour_theme_urls.get(key)

        if url:
            # print("using cache")
            view.update_buttons()
            await view.update_embed(url=url)
            await interaction.response.edit_message(content=None, embed=view.embed, view=view)
            view.processing = False

        else:
            await interaction.response.defer()
            # print("NOT using cache")
            loop: asyncio.AbstractEventLoop = view.ctx.bot.loop
            await loop.run_in_executor(None, view.merge, sprites)
            view.update_buttons()
            await view.update_embed(key=key)
            await interaction.followup.edit_message(view.message.id, content=None, embed=view.embed, view=view)
            view.processing = False


class MovementButton(discord.ui.Button):
    """The button which controls movements"""
    def __init__(self, emoji, row: int, relative_direction: str):
        super().__init__(emoji=emoji, row=row, style=discord.ButtonStyle.green)
        self.relative_direction = relative_direction

    async def callback(self, interaction: discord.Interaction):
        view: _3dmazeView = self.view

        view.processing = True
        if (self.relative_direction != "front") and (self.relative_direction != "forward"):
            view.change_direction(self.relative_direction)
        view.move_forward()

        sprites = view.get_sprites(view.current_position)
        key = await view.generate_key(sprites)
        url = view.colour_theme_urls.get(key)

        if url:
            # print("using cache")
            view.update_buttons()
            await view.update_embed(url=url)
            await interaction.response.edit_message(content=None, embed=view.embed, view=view)
            view.processing = False

        else:
            await interaction.response.defer()
            # print("NOT using cache")
            loop: asyncio.AbstractEventLoop = view.ctx.bot.loop
            await loop.run_in_executor(None, view.merge, sprites)
            view.update_buttons()
            await view.update_embed(key=key)
            await interaction.followup.edit_message(view.message.id, content=None, embed=view.embed, view=view)
            view.processing = False

# maze
class _3dmazeView(discord.ui.View):
    def __init__(self, ctx: commands.Context, row: int, cols: int):
        # view stuff
        super().__init__(timeout=180)
        self.ctx = ctx
        self.message: discord.Message
        self.embed = discord.Embed()
        self.starting_message_sent = False
        self.maze_channel: discord.TextChannel = ctx.bot.get_channel(900753157511061504)
        self.processing = False # set to true if we have depherred a response and we are making image. set to false if no image is being made

        self.colour_emoji_pairs = {
            "yellow_purple" : "🟨",
            "green_pink" : "🟩"
        }
        self.colour_theme, self.wall_emoji = random.choice(list(self.colour_emoji_pairs.items()))
        
        self.colour_theme_pairs: Dict[str, Dict[str, str]] = {
            "yellow_purple" : self.ctx.bot.maze_cache_yellow_purple,
            "green_pink" : self.ctx.bot.maze_cache_green_pink,
        }
        self.colour_theme_urls = self.colour_theme_pairs[self.colour_theme]
        self.add_buttons()

        # maze stuff
        self.maze = myMaze()
        self.rows = row
        self.cols = cols
        self.maze.generator = BacktrackingGenerator(self.rows, self.cols) # works nicely
        self.maze.generate()
        self.maze.generate_entrances()
        spawn_position = self.get_spawn_position(self.maze.start, self.maze.grid)
        self.current_position = spawn_position
        # self.maze.solver = BacktrackingSolver()
        # self.maze.solve()
        # self.update_buttons()
        # number of 90 degree rotations to be taken when switching directions
        self.all_directions = {
            "north": 0,
            "south": 2,
            "east": 3,
            "west": 1,
        }
        self.indexed_all_directions = {
            "0": "north",
            "2": "south",
            "3": "east",
            "1": "west",
        }
        self.direction = "north"
        self.compass_emoji = "<:Compass:920333076947681410>"
        self.directon_emojis = {
            "north": "\N{UPWARDS BLACK ARROW}",
            "south": "\N{DOWNWARDS BLACK ARROW}",
            "east": "\N{BLACK RIGHTWARDS ARROW}",
            "west": "\N{LEFTWARDS BLACK ARROW}",
        }
        # print(self.maze.tostring(True, True))
        # print(self.maze.grid)

        # image stuff
        self.buffer = BytesIO()
        self.background_path = "utils/maze_parts/transparent.png"
        self.complete_image = None

    def add_buttons(self):
        """Adds all the buttons required for the maze."""

        # row 0
        self.add_item(BlankButton(0))
        self.add_item(MovementButton("\N{UPWARDS BLACK ARROW}", 0, "forward"))
        self.add_item(BlankButton(0))

        # row 1
        self.add_item(MovementButton("\N{LEFTWARDS BLACK ARROW}", 1, "left"))
        self.add_item(BlankButton(1))
        self.add_item(MovementButton("\N{BLACK RIGHTWARDS ARROW}", 1, "right"))

        # row 2
        self.add_item(BlankButton(2))
        self.add_item(MovementButton("\N{DOWNWARDS BLACK ARROW}", 2, "back"))
        self.add_item(BlankButton(2))

        # row 3
        self.add_item(DirectionButton("look left", 3, "left"))
        self.add_item(BlankButton(3))
        self.add_item(DirectionButton("look right", 3, "right"))

        # row 4
        self.add_item(BlankButton(4))
        self.add_item(DirectionButton("look back", 4, "back"))
        self.add_item(BlankButton(4))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.ctx.author.id:
            if self.processing is False: # no image is being made
                return True
            else:
                await interaction.response.send_message("Spam bad.", ephemeral=True)
        else:
            await interaction.response.send_message(f"You cant control this maze. You can try this command by typing `{self.ctx.clean_prefix}3dmaze`", ephemeral=True)

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True
        await self.message.edit(content="Timeout reached", view=self)

    # maze image generation stuff
    def get_spawn_position(self, start: Tuple[int, int], grid: List[List[int]]):
        """Returns a Tuple(int, int) of the coordinates where the player should be spawned"""
        # some of them can be invalid based on mazes
        r,c = start
        neighbours = (
            (r-1, c), # up
            (r+1, c), # down
            (r, c+1), # right
            (r, c-1), # left
        )

        for neighbour in neighbours: # one of them has to be 0
            try:
                if grid[neighbour[0]][neighbour[1]] == 0:
                    return neighbour
                
            except Exception:
                continue

    def get_C_neighbours(self, current_position: Tuple[int, int]) -> Dict[str, Tuple[int, int]]:
        """Returns a dict of center neighbours"""
        r,c = current_position

        north_neighbours = {
            "1_" : (r, c), # floor/ wall/ door
            "2_" : (r-1, c), # floor/ wall/ door
            "3_" : (r-2, c), # floor/ wall/ door
            "4_" : (r-3, c), # floor/ wall/ door
            "5_" : (r-4, c), # floor/ wall/ door
            "6_" : (r-5, c), # wall/ door
        }

        south_neighbours = {
            "1_" : (r, c), # floor/ wall/ door
            "2_" : (r+1, c), # floor/ wall/ door
            "3_" : (r+2, c), # floor/ wall/ door
            "4_" : (r+3, c), # floor/ wall/ door
            "5_" : (r+4, c), # floor/ wall/ door
            "6_" : (r+5, c), # wall/ door
        }

        east_neighbours = {
            "1_" : (r, c), # floor/ wall/ door
            "2_" : (r, c+1), # floor/ wall/ door
            "3_" : (r, c+2), # floor/ wall/ door
            "4_" : (r, c+3), # floor/ wall/ door
            "5_" : (r, c+4), # floor/ wall/ door
            "6_" : (r, c+5), # wall/ door
        }

        west_neighbours = {
            "1_" : (r, c), # floor/ wall/ door
            "2_" : (r, c-1), # floor/ wall/ door
            "3_" : (r, c-2), # floor/ wall/ door
            "4_" : (r, c-3), # floor/ wall/ door
            "5_" : (r, c-4), # floor/ wall/ door
            "6_" : (r, c-5), # wall/ door
        }

        if self.direction == "north":
            return north_neighbours

        elif self.direction == "south":
            return south_neighbours

        elif self.direction == "east":
            return east_neighbours
            
        elif self.direction == "west":
            return west_neighbours

    def get_LR_neighbours(self, current_position: Tuple[int, int]) -> Dict[str, Tuple[int, int]]:
        """Returns a dict of left and right neighbours"""
        
        r,c = current_position

        north_neighbours = {
            "1_right_" : (r, c+1), # open/wall
            "1_left_": (r, c-1), # open/wall

            "2_right_" : (r-1, c+1), # open/wall
            "2_left_" : (r-1, c-1), # open/wall

            "3_right_" : (r-2, c+1), # open/wall
            "3_left_" : (r-2, c-1), # open/wall

            "4_right_" : (r-3, c+1), # open/wall
            "4_left_" : (r-3, c-1), # open/wall

            # 5 will be always wall and 5 right/left wall will be always added if 5 is visible
            "5_right_" : (r-4, c+1), # floor/wall
            "5_left_" : (r-4, c-1), # floor/wall
        }

        south_neighbours = {
            "1_right_" : (r, c-1), # open/wall
            "1_left_": (r, c+1), # open/wall

            "2_right_" : (r+1, c-1), # open/wall
            "2_left_" : (r+1, c+1), # open/wall

            "3_right_" : (r+2, c-1), # open/wall
            "3_left_" : (r+2, c+1), # open/wall

            "4_right_" : (r+3, c-1), # open/wall
            "4_left_" : (r+3, c+1), # open/wall

            # 5 will be always wall and 5 right/left wall will be always added if 5 is visible
            "5_right_" : (r+4, c-1), # floor/wall
            "5_left_" : (r+4, c+1), # floor/wall
        }

        east_neighbours = {
            "1_right_" : (r+1, c), # open/wall
            "1_left_": (r-1, c), # open/wall

            "2_right_" : (r+1, c+1), # open/wall
            "2_left_" : (r-1, c+1), # open/wall

            "3_right_" : (r+1, c+2), # open/wall
            "3_left_" : (r-1, c+2), # open/wall

            "4_right_" : (r+1, c+3), # open/wall
            "4_left_" : (r-1, c+3), # open/wall

            # 5 will be always wall and 5 right/left wall will be always added if 5 is visible
            "5_right_" : (r+1, c+4), # floor/wall
            "5_left_" : (r-1, c+4), # floor/wall
        }

        west_neighbours = {
            "1_right_" : (r-1, c), # open/wall
            "1_left_": (r+1, c), # open/wall

            "2_right_" : (r-1, c-1), # open/wall
            "2_left_" : (r+1, c-1), # open/wall

            "3_right_" : (r-1, c-2), # open/wall
            "3_left_" : (r+1, c-2), # open/wall

            "4_right_" : (r-1, c-3), # open/wall
            "4_left_" : (r+1, c-3), # open/wall

            # 5 will be always wall and 5 right/left wall will be always added if 5 is visible
            "5_right_" : (r-1, c-4), # floor/wall
            "5_left_" : (r+1, c-4), # floor/wall
        }

        if self.direction == "north":
            return north_neighbours

        elif self.direction == "south":
            return south_neighbours

        elif self.direction == "east":
            return east_neighbours
            
        elif self.direction == "west":
            return west_neighbours

    def get_sprites(self, current_position) -> List[str]:
        """Takes a `current_position` and returns a `List[str]` of paths of images to use."""

        maze = self.maze.grid
        end = self.maze.end

        complete_explore: List[str] = [] # floor and right and left walls
        partial_explore: List[str] = []
        final_paths: List[str] = []

        # center must be explored first to maximize speed and explored in ascending order (1-6)
        # 1 being biggest center wall and 6 being smallest
        C_neighbours: Dict[str, Tuple[int, int]] = self.get_C_neighbours(current_position)
        for prefix in C_neighbours.keys(): # center
            # 6 is special case
            if prefix[0] == "6":
                r,c = C_neighbours[prefix]
                if (r,c) == end:
                    suffix = "center_door" # change this
                else:
                    try:
                        if maze[r][c] == 0:
                            suffix = "open"
                        elif maze[r][c] == 1:
                            suffix = "wall"
                    except IndexError:
                        suffix = "wall"
            else:
                suffix = self.get_sprite_name(C_neighbours[prefix], True)

            complete_name = prefix + suffix
            final_paths.append(complete_name)


            # if we find a big wall that covers smaller the paths/wall behind it, we break the loop
            if complete_name.endswith("wall") or complete_name.endswith("door"):
                partial_explore.append(prefix[0])
                break
            else:
                # otherwise we will also visit right and left
                complete_explore.append(prefix[0])

        LR_neighbours: Dict[str, Tuple[int, int]] = self.get_LR_neighbours(current_position)
        for prefix in LR_neighbours.keys(): # left/right

            # only center wall
            if prefix[0] in partial_explore:
                pass


            # left and right walls too
            if prefix[0] in complete_explore:
                if prefix[0] == "5": # 5 always has walls
                    suffix = "wall"
                else:
                    suffix = self.get_sprite_name(LR_neighbours[prefix], False)
                complete_name = prefix + suffix
                final_paths.append(complete_name)

        # print(f"complete_explore: {complete_explore}")
        # print(f"final_paths: {final_paths}")
        return final_paths

    def get_sprite_name(self, position: Tuple[int, int], center: bool) -> str:
        """It is called by `get_sprites()` function to get the actual sprite name"""

        # if maze is None:
        maze = self.maze.grid
        end = self.maze.end

        r, c = position
        if position == end:
            if center:
                return "center_door"
            else:
                return "door"

        if not center: # left or right
            try:
                if maze[r][c] == 0:
                    return "open"
                if maze[r][c] == 1:
                    return "wall"
            except IndexError:
                return "wall"

        elif center:
            try:
                if maze[r][c] == 0:
                    return "floor"
                if maze[r][c] == 1:
                    return "center_wall"
            except IndexError:
                return "center_wall"

    def merge(self, sprites: List[str]):
        background = Image.open(f"utils/maze_parts/transparent.png")

        for sprite in sprites:
            img = Image.open(f"utils/maze_parts/{self.colour_theme}/{sprite}.png")
            img = img.convert("RGBA")
            background.paste(img, (0,0), img)

        self.buffer = BytesIO()
        background.save(self.buffer, "png")
        self.buffer.seek(0)
        self.complete_image = background

    async def make_image(self):
        """Creates the Image"""

        sprites = self.get_sprites(self.current_position)
        key = await self.generate_key(sprites)
        url = self.colour_theme_urls.get(key)

        if url:
            # print("using cache")
            await self.update_embed(url=url)

        else:
            # print("NOT using cache")
            loop: asyncio.AbstractEventLoop = self.ctx.bot.loop
            await loop.run_in_executor(None, self.merge, sprites)
            await self.update_embed(key=key)

        self.update_buttons()
        # self.embed.set_image(url="attachment://maze.png")
        
    #------------------------------------------------------

    # utility stuff
    def get_FBRL_cells(self) -> List[Tuple[int, int]]:
        """Returns a list of neighbouring cells sorted in following manner:
        1. front
        2. back
        3. right
        4. left
        """

        r,c = self.current_position

        if self.direction == "north":
            return [
                (r-1, c),
                (r+1, c),
                (r, c+1),
                (r, c-1)
            ]

        elif self.direction == "south":
            return [
                (r+1, c),
                (r-1, c),
                (r, c-1),
                (r, c+1)
            ]

        elif self.direction == "east":
            return [
                (r, c+1),
                (r, c-1),
                (r+1, c),
                (r-1, c)
            ]

        elif self.direction == "west":
            return [
                (r, c-1),
                (r, c+1),
                (r-1, c),
                (r+1, c)
            ]

    def update_buttons(self):
        neighbours = self.get_FBRL_cells() # front, back, right, left
        for index, neighbour in enumerate(neighbours): # one of them has to be 0
            try: # enabling paths
                
                if (self.maze.grid[neighbour[0]][neighbour[1]] == 0):
                    self.disable_button(index, False)

                # disable walls
                if (self.maze.grid[neighbour[0]][neighbour[1]] == 1):
                    self.disable_button(index, True)

                # enabling end
                if (neighbour == self.maze.end):
                    self.disable_button(index, False)

                # disabling start
                if (neighbour == self.maze.start):
                    self.disable_button(index, True)
            except Exception as e: # out of bounds/ IndexError
                pass

    def disable_button(self, direction_index: int, disabled: bool):
        """Disables a button based on index given by `update_buttons`"""
        if direction_index == 0: # front
            self.children[1].disabled = disabled

        elif direction_index == 1: # back
            self.children[7].disabled = disabled

        elif direction_index == 2: # right
            self.children[5].disabled = disabled

        elif direction_index == 3: # left
            self.children[3].disabled = disabled
        
    async def get_url(self):
        """sends a maze image in maze channel and returns the image's url"""
        msg = await self.maze_channel.send(file=discord.File(self.buffer, filename="maze.png"))
        return msg.attachments[0].url

    def create_map(self) -> str:
        """generates a 7x7 view of given index"""
        MAX_ROWS = self.rows * 2 # index
        MAX_COLS = self.cols * 2 # index
        side = 5
        offset = side//2
        # T - top
        # B - bottom
        # R - right
        # L - left

        row: int = self.current_position[0]
        col: int = self.current_position[1]
        TL = [row - offset, col - offset]
        BR = [row + offset, col + offset]

        TL_row, TL_col = TL
        BR_row, BR_col = BR

        if TL_row < 0: # row of TL
            TL[0] = 0
            BR[0] = side - 1

        if TL_col < 0: # col of TL
            TL[1] = 0
            BR[1] = side - 1

        if BR_row > MAX_ROWS: # row of BR 
            BR[0] = MAX_ROWS # -1
            TL[0] = MAX_ROWS - side + 1

        if BR_col > MAX_COLS: # col of BR 
            BR[1] = MAX_COLS # -1
            TL[1] = MAX_COLS - side + 1

        string = ""

        for row in range(TL[0], BR[0]+1):
            # print(maze[row])
            for col in range(TL[1], BR[1]+1):
                try:
                    cell = self.maze.grid[row][col]

                    if (row,col) == (self.current_position):
                        string += "\N{FLUSHED FACE}"
                    elif (row,col) == self.maze.start: # red
                        string += "🟥"
                    elif (row,col) == self.maze.end: # green
                        string += "\N{DOOR}"
                    elif cell == 1: # wall
                        string += self.wall_emoji
                    elif cell == 0: # wall
                        string += "⬛"
                    

                except IndexError:
                    print(f"row = {row}, col = {col}, TL = {TL}, BR = {BR}")
            string += "\n"
        return string

    async def update_embed(self, key: str = None, url: str = None):

        # random_maze = self.maze.tostring(True, False, True, (self.current_position))

        # random_maze = random_maze.replace(" ", "⬛") # floor - grey
        # random_maze = random_maze.replace("#", self.wall_emoji) # walls - depends on colour theme
        # random_maze = random_maze.replace("S", "🟥") # start - red
        # random_maze = random_maze.replace("E", "\N{DOOR}") # end - green
        # random_maze = random_maze.replace("@", "\N{FLUSHED FACE}") # player - ...
        # self.embed.description = random_maze
        self.embed.description = self.create_map()
        self.embed.title = f"{self.compass_emoji} - {self.directon_emojis[self.direction]}"

        if url is None:
            url = await self.get_url()
            await self.insert_url(key, url)
        self.embed.set_image(url=url)

        if self.current_position == self.maze.end:
            self.manager = Database_Manager(self.ctx.bot)
            amount = self.rows * self.cols
            await self.manager.insert_coins(self.ctx.author.id, amount)
            self.embed.title = f"You reached the end! Congrats.\nYou got {amount} coins."
            for button in self.children:
                button.disabled = True
            self.stop()
    #------------------------------------------------------
    # movement stuff

    # remind me to rewrite this shit
    def change_direction(self, new_relative_direction: str): # right/left/back
        """Changes `self.direction` to a new absolute direction given by `new_relative_direction`.
        `new_relative_direction` can be either 'left', 'right', 'back'.
        """
        old_direction = self.direction

        if new_relative_direction == "right":
            if old_direction == "north":
                self.direction = "east"

            elif old_direction == "south":
                self.direction = "west"

            elif old_direction == "east":
                self.direction = "south"

            elif old_direction == "west":
                self.direction = "north"

        elif new_relative_direction == "left":
            if old_direction == "north":
                self.direction = "west"

            elif old_direction == "south":
                self.direction = "east"

            elif old_direction == "east":
                self.direction = "north"

            elif old_direction == "west":
                self.direction = "south"

        elif new_relative_direction == "back":
            if old_direction == "north":
                self.direction = "south"

            elif old_direction == "south":
                self.direction = "north"

            elif old_direction == "east":
                self.direction = "west"

            elif old_direction == "west":
                self.direction = "east"

    def move_forward(self):
        if self.direction == "north":
            self.current_position = (self.current_position[0]-1, self.current_position[1])
        elif self.direction == "south":
            self.current_position = (self.current_position[0]+1, self.current_position[1])
        elif self.direction == "east":
            self.current_position = (self.current_position[0], self.current_position[1]+1)
        elif self.direction == "west":
            self.current_position = (self.current_position[0], self.current_position[1]-1)

    #-------------------------------------------------------
    # mongodb stuff for caching image URLs

    async def generate_key(self, final_paths: List[str]) -> str:
        """Generates a key from `final_paths` list.
        This can be used for cache lookup and database insertions.
        """
        key = f"{self.colour_theme}+"
        key += "+".join(final_paths)
        return key

    async def insert_url(self, key: str, url: str) -> None:
        """Inserts a key-url pair in the database for quick retrieval later.
        This also updates the local cache.
        """
        col = self.ctx.bot.mongo_client.discord.maze_URLs
        old_query = {"_id" : f"{self.colour_theme}"}
        new_query = {"$set" : {key : url}}
        await col.update_one(old_query, new_query)

        # self.ctx.bot.maze_cache[key] = url
        if self.colour_theme == "yellow_purple":
            self.ctx.bot.maze_cache_yellow_purple[key] = url
        elif self.colour_theme == "green_pink":
            self.ctx.bot.maze_cache_green_pink[key] = url