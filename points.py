import discord
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

DATA_FILE = "points_eco.json"
TOKEN_FILE = "token.txt"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")

@commands.command()
async def points(ctx, type, user: discord.Member = None, amount: int = 0):
    if type == "test":
    	await ctx.send("Online!")
    if type == "unregister":
    	if ctx.author.id == 1258323457674838028 or ctx.author.id == 1224550701259030598 or ctx.author.id == 1409793395555307541:
    		data = load_data()
    		data2 = data.pop(user.id, None)
    		save_data(data2)
    if type == "debug":
    	data = load_data()
    	await ctx.send(data)
    	save_data(data)
    if type == "register":
    	for member in ctx.guild.members:
	    	data = load_data()
	    	if not str(member.id) in data:
	    		username = await bot.fetch_user(member.id)
	    		display_name = username.display_name
	    		await ctx.send(f'{display_name} just got registered.')
	    		open_account(member.id, data)
	    		save_data(data)
    if type == "help":
    	await ctx.send("help \nShows the list of subcommands and their definitions. Usable by all.\n\nshow\nShows you your current point balance. Usable by all.\n\nmodify\nChanges the amount of points someone has, by default the target user is you. Usable by Hallowxity and Soup.\n\nleaderboard\nShows a leaderboard containing everyone registered in it. This command takes a while due to it looking up the user associated with everyone registered's ID. Usable by all.\n\nregister\nRegisters the whole server. Usable by all.\n\nunregister\nUnregisters the target user from the system, used if people leave the developer team. Usable by Hallowxity and Soup.\n\ntest\nTells you if the bot is online, if it is it will respond with 'Online!.' Otherwise it doesn't respond at all. Usable by all.\n\ndebug\nSays the current contents of points_eco.json. (The file containing the points data.) Usable by all.\n\nThe structure of $points is '$points <subcommand> <user> <amount>'. User and amount are optional, although amount is required for modify and user is required for modify and unregister.\n\nIf you would like to contribute to this, you can visit the Github repository [here](https://github.com/SpideyByte/phantasmagoria-points).")
    if type == "show":
    	target = user or ctx.author
    	target_ping = str(f'<@{target.id}>')
    	data = load_data()
    	open_account(target.id, data)
    	points = data[str(target.id)]
    	await ctx.send(f'{target_ping} currently has {points} points.')
    	save_data(data)
    if type == "leaderboard":
    	await ctx.send("This command takes a while to load. Please wait.")
    	target = ctx.author
    	data = load_data()
    	open_account(target.id, data)
    	leaderboard = ""
    	sorted_points = sorted(data.items(), key=lambda item: item[1], reverse=True)
    	for rank, (player, score) in enumerate(sorted_points, start=1):
    		username = await bot.fetch_user(player)
    		display_name = username.display_name
    		leaderboard = leaderboard + (f"{rank}. {display_name} - {score}\n")
    	await ctx.send(leaderboard)
    	save_data(data)
    if type == "modify":
    	if ctx.author.id == 1258323457674838028 or ctx.author.id == 1224550701259030598 or ctx.author.id == 1409793395555307541:
	    	if amount > 0:
		    	target = user or ctx.author
		    	target_ping = str(f'<@{target.id}>')
		    	data = load_data()
		    	open_account(target.id, data)
		    	data[str(target.id)] += amount
		    	points = data[str(target.id)]
		    	await ctx.send(f'{target_ping} just got {amount} more points! {target_ping} is currently at {points} points. ')
		    	save_data(data)
	    	if 0 > amount:
		    	target = user or ctx.author
		    	target_ping = str(f'<@{target.id}>')
		    	data = load_data()
		    	open_account(target.id, data)
		    	data[str(target.id)]+= amount
		    	points = data[str(target.id)]
		    	calculated_amount = str(amount).removeprefix("-")
		    	await ctx.send(f'{target_ping} just lost {calculated_amount} points! {target_ping} is currently at {points} points. ')
		    	save_data(data)
 
def get_token():
	if os.path.exists(TOKEN_FILE):
		with open(TOKEN_FILE, "r") as f:
			return f.read()
		
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def open_account(user_id, data):
    user_str = str(user_id)
    if user_str not in data:
        data[user_str] = 100
        return True
    return False

bot.add_command(points)

bot.run(get_token())
