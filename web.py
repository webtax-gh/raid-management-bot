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

allowed_mentions = discord.AllowedMentions.none() 

bot = commands.Bot(command_prefix=prefix, description=description, intents=intents, allowed_mentions=allowed_mentions)

bot.remove_command("help")

whitelist = []

class Confirm(discord.ui.View):
    def __init__(self, author_id : int):
        super().__init__()
        self.author_id = author_id
        self.value = None
    
    @discord.ui.button(label="Ban", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("You cannot use this button", ephemeral=True)
        await interaction.response.send_message('Banning...', ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("You cannot use this button", ephemeral=True)
        await interaction.response.send_message('Cancelled', ephemeral=False)
        self.value = False
        self.stop()


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
    view = Confirm(author_id = ctx.author.id)

    for chunk in [watchlist_info_message[i:i+4000 ] for i in range(0, len(watchlist_info_message), 4000 )]:
        await ctx.send(embed=discord.Embed(description=chunk, color=discord.Color.blurple()), view=view)
    
    await view.wait()

    if view.value is None:
        await ctx.send("Buttons timed out") 
    elif view.value == False:
        return # already handled in the view 
    if view.value == True:
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
