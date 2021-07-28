import discord
from discord.ext import commands
import itertools
import asyncio
import os

token = os.getenv("BOT_TOKEN")
staff_role_id = os.getenv("BOT_STAFF_ID")
prefix = os.getenv("BOT_PREFIX")

description = '''A raid managment bot'''

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix=prefix, description=description, intents=intents)

bot.remove_command("help")

whitelist = []

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@commands.check_any(commands.has_role(staff_role_id), commands.has_permissions(ban_members=True))
@bot.command()
async def ping(ctx):
    """Gets bot ping"""
    await ctx.send("Pong :ping_pong:")

@commands.check_any(commands.has_role(staff_role_id), commands.has_permissions(ban_members=True))
@bot.command(name="whitelist")
async def _whitelist(ctx, member: discord.Member):
    """Whistlists a user"""
    whitelist.append(member.id)
    await ctx.send(f":white_check_mark: `{member}` has been whitelisted.")

# util function
def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk

@commands.check_any(commands.has_role(staff_role_id), commands.has_permissions(ban_members=True))
@bot.command()
async def mass_ban(ctx, starting_member: discord.Member, ending_member: discord.Member):
    """Bans a large amount of members"""
    msg = await ctx.send("Caching users, please wait")
    await ctx.guild.chunk()
    await ctx.send("Caching complete, compiling user list")
    watchlist = []
    for member in ctx.guild.members:
        if (starting_member.joined_at <= member.joined_at <= ending_member.joined_at) and member.id not in whitelist:
            watchlist.append(member)
    await ctx.send("Watchlist compiled")
    watchlist_info_message = f"Watchlist info:\n The watchlist contains **{len(watchlist)}** users.\n"+"\n".join([f"`{x.name} ({x.id})`" for x in watchlist])+"\n"+f"**To ban all of these users, send `I want to ban the {len(watchlist)} members in the watchlist`. You have 30 seconds.**"
    for chunk in [watchlist_info_message[i:i+1999 ] for i in range(0, len(watchlist_info_message), 1999 )]:
        await ctx.send(chunk)
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    msg = await bot.wait_for("message", check=check, timeout=30)
    if msg.content.lower() == f"I want to ban the {len(watchlist)} members in the watchlist".lower():
        await ctx.send(f"Ban wave started by {ctx.author} ({ctx.author.id})")
        for chunk in grouper(5, watchlist):
            await asyncio.gather(x.ban(reason=f"Mass ban by {ctx.author} ({ctx.author.id})") for x in chunk)
        await ctx.send(f":white_check_mark: **Banned {len(watchlist)} users**")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error,commands.MemberNotFound):
        await ctx.send("`I could not find one or more users that you provided`")
    else:
        await ctx.send(str(error))

bot.load_extension("jishaku")

bot.run(token)
