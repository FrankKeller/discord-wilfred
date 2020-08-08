import discord
from discord.ext import commands
import utils.logging as log
import utils.colours as colour
import utils.values as value
import utils.database as sql
from utils.helpers import *


class Crates(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["loot", "crate"])
    async def crates(self, ctx, action = None, target : discord.Member = None):
        crates_no = sql.db_query("ibm.db", "SELECT crates FROM Members WHERE UserID = %s" % (str(ctx.author.id)))[0][0]
        args = ctx.message.content.split(" ")
        if len(args) == 1:
            embed = discord.Embed(description="You currently have **%s** crate(s)" % (str(crates_no)),
                                  color=colour.reds)
            embed.set_author(name="Crates")
            await ctx.send(embed=embed)
        elif action.upper() == "OPEN" or action.upper() == "USE":
            if crates_no == 0:
                await ctx.send("**Error:** You don't have any crates to open")
            else:
                if len(args) >= 3:
                    target_no = int(args[2])

                    if target_no > 10:
                        await ctx.send(embed=discord.Embed(title="Crates Opening Error",
                                                           description="You're trying to open too many crates, try a smaller number.",
                                                           color=colour.reds))

                        return
                    elif target_no <= 0:
                        await ctx.send(embed=discord.Embed(title="Crates Opening Error",
                                                           description="Please don't try to create a black hole and try a bigger number.",
                                                           color=colour.reds, ))

                        return
                else:
                    target_no = 1

                # If a user tries to open more crates than they have it'll default to how much they have
                if crates_no < target_no:
                    target_no = crates_no

                # Open crates
                crates = [open_crate(ctx, crates_no) for _ in range(0, target_no)]

                # Take however many crates the user opened
                crates_no = crates_no - target_no
                sql.execute_query("ibm.db",
                                  "UPDATE Members SET crates = %s WHERE UserID = %s" % (
                                      str(crates_no), str(ctx.author.id)))

                embed = discord.Embed(
                    description="Opening Crate" if target_no == 1 else "Opening %d Crates" % target_no)
                embed.set_author(name="Crate")
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(2)

                if target_no == 1:
                    print(crates)
                    embed = discord.Embed(title=crates[0][0], description=crates[0][1], color=crates[0][2])
                    embed.set_author(name=crates[0][3])
                    await msg.edit(embed=embed)
                else:
                    description = ""
                    for c in crates:
                        description += c[0].replace("You Won:", "**You Won:**").replace("(Duplicate)",
                                                                                        "**(Duplicate)**") + "\n"

                    embed = discord.Embed(title="You've successfully opened %d crates!" % target_no,
                                          description=description,
                                          colour=colour.primary)
                    await ctx.send(embed=embed)

        elif action.upper() == "GIVE":
            if "Manager" in [role.name for role in ctx.message.author.roles]:
                target = await commands.MemberConverter().convert(ctx, args[2])

                if target is not None:
                    amount = int(args[3])
                    crates_no = \
                        sql.db_query("ibm.db", "SELECT crates FROM Members WHERE UserID = %s" % (str(target.id)))[0][0]
                    crates_no = crates_no + amount
                    sql.execute_query("ibm.db", "UPDATE Members SET crates = %s WHERE UserID = %s" % (
                        str(crates_no), str(target.id)))
                    await ctx.send("Successfully gave %s **%s** crate(s)" % (target.mention, str(amount)))
            else:
                await ctx.send("**Insufficient Permissions:** This command requires permission rank `MANAGER`")


def open_crate(ctx, crates_no):
    # Pick rarity
    chance = random.randint(1, 100)
    if chance <= 50:
        rarity = "COMMON"
        embed_color = 0xFFFFFF
        dupe_reward = 250
    elif 50 < chance <= 75:
        rarity = "UNCOMMON"
        embed_color = 0x55FF55
        dupe_reward = 500
    elif 75 < chance <= 95:
        rarity = "RARE"
        embed_color = 0X5555FF
        dupe_reward = 750
    elif 95 < chance <= 99:
        rarity = "LEGENDARY"
        embed_color = 0xFFAA00
        dupe_reward = 1000
    elif chance == 100:
        rarity = "MYTHIC"
        embed_color = 0xFF5555
        dupe_reward = 0

    # select cosmetic
    if rarity == "MYTHIC":
        title = "You Won: " + "$25.00"
        description = "Some Money to spend on cool things."
        add_balance(ctx.author, float(25.00))
    else:
        items = sql.db_query("ibm.db", "SELECT * from cosmetics WHERE cosmetic_rarity = '%s'" % (str(rarity)))
        item = random.choice(items)
        inventory = eval(
            sql.db_query("ibm.db", "SELECT cosmetics FROM Members WHERE UserID = %s" % (str(ctx.author.id)))[0][0])
        if item[0] in inventory:
            title = "You Won: " + item[1] + " (Duplicate)"
            description = item[3] + "\nSince you already had this item you've been awarded %s exp" % (str(dupe_reward))
            add_exp(ctx.author.id, dupe_reward)
        else:
            title = "You Won: " + item[1]
            description = item[3]
            inventory.append(int(item[0]))
            sql.execute_query("ibm.db", "UPDATE Members SET cosmetics = '%s' WHERE UserID = %s" % (
                str(inventory), str(ctx.author.id)))

    return title, description, embed_color, rarity  # In this order to prevent confusion with indexes at the embed creation


def setup(client):
    client.add_cog(Crates(client))
