import discord
from discord.ext import commands
import asyncio
import os
from discord.ext import buttons


class MyPaginator(buttons.Paginator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Tags(commands.Cog, name="Tags", description="All tag realated commands"):
    
    def __init__(self,bot):
        self.bot = bot


    @commands.command(name="tag")
    async def tag(self, ctx, *, tag = None):
        """Gets a tag with specified name"""
        if tag is None:
            await ctx.send("You need to specify a tag to search for!")
            return
        # searching by tag name
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        tag_lower = str(tag.lower().strip())
        
        query = {"tag_name" : tag_lower, "guild_id" : f"{ctx.guild.id}"}
        find_existing_tag = await mycol.find_one(query)
        
        # if tag name is not found, search by alias
        if find_existing_tag is None:
            alias_query = {"alias" : tag_lower, "guild_id" : f"{ctx.guild.id}"}
            find_existing_alias = await mycol.find_one(alias_query)
            # if alias is not found, we return
            if find_existing_alias is None:
                await ctx.send("Tag not found")
            else:
                # fetching original tag through alias
                # gets the name of original tag
                originaltag = find_existing_alias["original_tag"]
                # searches for original tag
                original_tag_doc = await mycol.find_one({"tag_name" : originaltag, "guild_id" : f"{ctx.guild.id}"})
                # check if tag exists or deleted
                if original_tag_doc is None:
                    await ctx.send("The tag for this alias is deleted")
                # finally we send
                else:
                    pingable_people = discord.AllowedMentions(everyone=False, users=False, roles=False)
                    await ctx.send(original_tag_doc["content"], allowed_mentions=pingable_people)
        else:
            pingable_people = discord.AllowedMentions(everyone=False, users=False, roles=False)
            await ctx.send(find_existing_tag["content"], allowed_mentions=pingable_people)
            
# ===============================================================================================================================
    @commands.command(name="tag_create", aliases=["tagcreate", "tag-create", "create_tag", "make_tag"])
    async def tag_create(self, ctx):
        """Creates a tag"""
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        def check(temp):
            return temp.author.id == ctx.author.id
    
        await ctx.send("Hello. What do you want to name the tag?\n**NOTE: You can abort the tag creation process at any time by typing `+abort`.**")

        tag_name_raw = await self.bot.wait_for("message", check=check, timeout=45)
        try:

            tag_name = str(tag_name_raw.content.lower().strip()) # tries to get text only

            if tag_name == "+abort":
                return await ctx.send("Process aborted")
            
            if tag_name == "":
                return await ctx.send("A tag's name can only be in text.")
                
            else:
                check_for_duplicates = await mycol.find_one({"tag_name" : f"{tag_name}", "guild_id" : f"{ctx.guild.id}"})


                # creating a new tag only if another tag does not exist with same name
                if check_for_duplicates is None:
                    check_for_duplicate_aliases = await mycol.find_one({"alias" : f"{tag_name}", "guild_id" : f"{ctx.guild.id}"})
                    if check_for_duplicate_aliases is None:
                        await ctx.send(f"Alright! So the tag's name is {tag_name}. Now, what should be the content for this tag?\n**NOTE: You can abort the tag creation process at any time by typing `+abort`.**")

                        tag_content_raw = await self.bot.wait_for("message", check=check, timeout=120)
                        try:
                            tag_content = str(tag_content_raw.content.strip())

                            # check for abort
                            if tag_content.lower() == "+abort":
                                return await ctx.send("Process aborted")
                            if tag_content == "":
                                tag_attachments = tag_content_raw.attachments[0] # if text is blank , tries to get url of attachment
                                tag_content = tag_attachments.url

                            # finally we create tag
                            await mycol.insert_one(
                                {
                                    "tag_name" : f"{tag_name}",
                                    "guild_id" : f"{ctx.guild.id}",
                                    "tag_owner_id" : f"{ctx.author.id}",
                                    "content" : f"{tag_content}"
                                    }
                                )
                            await ctx.send("Successfully created tag")
                        except Exception as e:
                            await ctx.send("Enter text/images only")
                    else:
                        await ctx.send(f"There is already an alias with the name {tag_name}")
                else:
                    await ctx.send("There is already a tag with that name!")
        except Exception as e:
            await ctx.send("Enter text/images only")



# ===============================================================================================================================
    @commands.command(name="tag_delete", aliases=["tag_remove", "tag-delete", "tag-remove"])
    async def tag_delete(self, ctx, *, tag_name = None):
        """Deletes a specified tag if you are the tag owner or you have `manage messages` permission."""
        if tag_name is None:
            return await ctx.send("You need to specify which tag I should delete.")
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        tag_name_lower = tag_name.lower().strip()
        query = await mycol.find_one({"tag_name" : tag_name, "guild_id" : f"{ctx.guild.id}"})

        if query is None:
            return await ctx.send("That tag doesn't exist.")

        # only tag owner can delete tag. mods can also delete tags
        elif (str(ctx.author.id) == (query['tag_owner_id'])) or (ctx.author.guild_permissions.manage_messages):
            await ctx.send(f"Are you sure you want to delete the tag called '{tag_name}'? Reply `Y` to continue and `N` to go back.")
            def check(m):
                return m.author.id == ctx.author.id

            try:
                confirmation = await self.bot.wait_for("message", check=check, timeout=25)
                if (confirmation.content.lower()) == "n":
                    await ctx.send("OK I won't delete this tag.")

                elif (confirmation.content.lower()) == "y":
                    await mycol.delete_one(query)
                    await ctx.send(f"{tag_name_lower} is successfully deleted.")

                else:
                    await ctx.send('''You need glasses. Can't you see I asked you to reply only "Y" or "N" ?''')

            except asyncio.TimeoutError:
                await ctx.send("Sorry, you didn't reply in time!")
        else:
            await ctx.send("You do not have the permission to delete this tag.")

# ===============================================================================================================================

    @commands.command(name="all_tags", description="", aliases=["all-tags", "alltags"])
    async def all_tags(self, ctx):
        """Gets all tags of this server."""
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        results_list = []
        query_results_cursor = mycol.find({"guild_id" : f"{ctx.guild.id}", "tag_name" :{"$exists" : True}})

        async for x in query_results_cursor:            
            results_list.append(x["tag_name"])
            

        new_results = []
        count = 1
        for i in results_list:
            new_results.append(f"{count}. {i}")
            count +=1
        
        # em1 = discord.Embed(title="Tags of this server", description="\n".join(new_results),color=ctx.author.color)
        # await ctx.send(embed=em1)
        page = MyPaginator(colour=0xff1493, embed=True, entries=new_results, length=10, title='All the tags of this server', timeout=90, use_defaults=True)
        await page.start(ctx)

# ===============================================================================================================================

    @commands.command(name="tag_alias", aliases=["tag-alias"])
    async def tag_alias(self, ctx):
        """Makes an alias of an existing tag"""
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        def check(temp):
            return temp.author.id == ctx.author.id

        await ctx.send("Enter the name of the tag you would like to make an alias for.")
        try:
            confirmation = await self.bot.wait_for("message", check=check, timeout=20)
            confirmation_lower = str(confirmation.content.lower().strip())
            query = mycol.find_one({"tag_name" : f"{confirmation_lower}"})
            

            if query is None:
                await ctx.send("Tag not found")
            else:
                await ctx.send(f"Nice. What should be the alias for {confirmation_lower} ?")
                try:
                    alias_name_raw = await self.bot.wait_for("message", check=check, timeout=20)
                    alias_name = str(alias_name_raw.content.lower().strip())
                    
                
                    check_for_existing_aliases = await mycol.find_one({"alias" : alias_name})
                    
                    if check_for_existing_aliases is None:
                        # creating a new alias
                        
                        mycol.insert_one(
                                    {
                                        "original_tag" : f"{confirmation_lower}",
                                        "alias" : f"{alias_name}",
                                        "guild_id" : f"{ctx.guild.id}",
                                        "alias_owner_id" : f"{ctx.author.id}"
                                        }
                                    )
                        await ctx.send(f"Successfully created alias with name `{alias_name}` that points to `{confirmation_lower}`.")
                    
                    else:
                        await ctx.send("There is already an existing with that name!")

                except asyncio.TimeoutError:
                    await ctx.send("Sorry, you didn't reply in time!")
        except asyncio.TimeoutError:
            await ctx.send("Sorry, you didn't reply in time!")

# ===============================================================================================================================

    @commands.command(name="tag_edit", aliases=["tag-edit", "tagedit"])
    async def tag_edit(self, ctx, *,tag_name = None):
        """Edits the content of a tag"""
        if tag_name is None:
            return await ctx.send("You need to specify which tag I should edit.")
            
        # else:
        str_tag = str(tag_name)
        mydb = self.bot.mongo_client.tags_database
        mycol = mydb[f"{ctx.guild.id}"]
        tag_name_lower = str_tag.lower().strip()
        query = await mycol.find_one({"tag_name" : tag_name_lower, "guild_id" : f"{ctx.guild.id}"})

        if query is None:
            return await ctx.send("That tag doesn't exists.")

        # only tag owner can edit tag
        if (str(ctx.author.id) == (query['tag_owner_id'])):
            await ctx.send(f"Alright. What should be the new content for {tag_name_lower} ?")
            def check(temp):
                return temp.author.id == ctx.author.id
            try:
                confirmation = await self.bot.wait_for("message", check=check, timeout=25)
                

                content = (confirmation.content.lower())
                old_values = ({"tag_name" : tag_name, "guild_id" : f"{ctx.guild.id}"})
                new_values = {"$set" : {"content" : content}}
                await mycol.update_one(old_values, new_values)
                await ctx.send(f"`{tag_name_lower}` is successfully edited.")

            except asyncio.TimeoutError:
                await ctx.send("Sorry, you didn't reply in time!")
        else:
            await ctx.send("You do not have the permission to edit this tag.")

# ===============================================================================================================================
def setup(bot):
    bot.add_cog(Tags(bot))
    print("Tags cog is loaded")