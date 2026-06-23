import discord
from discord.ext import commands
import json
import os
import uuid
import ast

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

DATA_FILE = "points_eco.json"
TOKEN_FILE = "token.txt"
SHOP_FILE = "shop.json"
ORDER_FILE = "orders.json"

class ItemCreatorModal(discord.ui.Modal, title="Item Creator"):
	name = discord.ui.TextInput(label="Name", style=discord.TextStyle.short)
	uid = discord.ui.TextInput(label="ID", style=discord.TextStyle.short)
	description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long)
	price = discord.ui.TextInput(label="Price", style=discord.TextStyle.short)
	
	async def on_submit(self, interaction: discord.Interaction):
		name = self.name
		uid = self.uid
		description = self.description
		price = self.price
		shop = get_shop()
		add_shop_item(str(name), str(description), int(str(price)), str(uid))
		embed = uembed("Item Creator", f"Created Item: \n Name: {name} \n ID: {uid} \n Description: {description} \n Price: {price}", color())
		await interaction.response.send_message(embed=embed)

class ShopButtonsView(discord.ui.View):
	def __init__(self):
	   super().__init__(timeout=180)
    
	@discord.ui.button(label="Purchase an item", style=discord.ButtonStyle.primary, custom_id="purchase")
	async def purchase_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		embed = uembed("Purchase", "What would you like to purchase?", color())
		view = PurchasableItemsView()
		await interaction.response.send_message(ephemeral=True, embed=embed, view=view)

	@discord.ui.button(label="View items", style=discord.ButtonStyle.primary, custom_id="view")
	async def view_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		shop = get_shop()
		text = ""
		for item in shop:
			text = text + f'**{shop[item]["name"]}**\n*{shop[item]["description"]}*\nPrice: {shop[item]["price"]} \nID: {shop[item]["id"]}\n\n'
		embed = uembed("Shop", text, color())
		await interaction.response.send_message(embed=embed)
		
	@discord.ui.button(label="Edit shop", style=discord.ButtonStyle.primary, custom_id="edit")
	async def edit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
		embed = error("Sorry, you don't have permissions to use this command.")
		if user_check(interaction.user.id):
			await interaction.response.send_modal(ItemCreatorModal())
		else:
			await interaction.response.send_message(embed=embed)

class PurchasableItems(discord.ui.Select):
	def __init__(self):
		options = shop_to_options()
		super().__init__(placeholder="Choose an item...", min_values=1, max_values=1, options=options)
		
	async def callback(self, interaction: discord.Interaction):
		item = self.values[0]
		await interaction.response.send_message(f"Sent a request to purchase {self.values[0]}! Please wait until it gets accepted.", ephemeral=True)
		shop = get_shop()
		uitem = shop[item]
		embed = error("Not enough points to purchase!")
		if points_more(interaction.user.id, int(uitem["price"])):
			orderid = create_order(ast.literal_eval(str(uitem)), str(interaction.user.id))
			embed = uembed("DRP Request", f'{interaction.user.global_name} wants {uitem["name"]}({uitem["id"]}) for {uitem["price"]} points.\n\nIf you do not know how to accept requests, just type the Order ID to accept one. That easy!  \n\n Order ID: {orderid}', color())
		await send_embed(embed)

class PurchasableItemsView(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=180)
		self.add_item(PurchasableItems())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    
@bot.event
async def on_message(message):
	if message.author == bot.user:
		return
	
	if message.guild == None:
		if user_check(message.author.id):
			embed = uembed("Order", f"Searching for order...", color())
			response = await message.channel.send(embed=embed)
			orders = get_orders()
			if message.content not in orders:
				embed = error("Order not found!")
				await response.edit(embed=embed)
				return
			order = orders[message.content]
			data = load_data()
			user = order["user"]
			person = await bot.fetch_user(str(user))
			username = person.display_name
			data[user] -= int(order["product"]["price"])
			user_points = data[str(user)]
			embed = uembed("Order", f"Order found and accepted!\n\nOrder:\n-UUID: {message.content}\n-User: {order['user']}\n-Item Name: {order['product']['name']}\n-Item ID: {order['product']['id']}\n-Price: {order['product']['price']}\n\n{username} has {user_points} points remaining.", color())
			await response.edit(embed=embed)
			embed = uembed("Order", f"Your order has been accepted! You currently have {user_points} points, and have obtained {order['product']['name']}!", color())
			await person.send(embed=embed)
			remove_order(message.content)
			save_data(data)
			
	await bot.process_commands(message)
	
@commands.command()
async def points(ctx, type, user: discord.Member = None, amount: int = 0):
    if type == "orders":
    	orders = get_orders()
    	if orders != {}:
	    	text = ""
	    	for order in orders:
	    		values_list = [key for key in orders.keys()]
	    		uuid = ""
	    		for i in values_list:
	    			if orders[i] == orders[order]:
	    				uuid = i
	    		text = text + f"Order:\n-UUID: {uuid}\n-User: {orders[order]['user']}\n-Item Name: {orders[order]['product']['name']}\n-Item ID: {orders[order]['product']['id']}\n-Price: {orders[order]['product']['price']}\n\n"
	    	embed = uembed("Orders", text, color())
	    	await ctx.send(embed=embed)
    	else:
	    	embed = error("Empty orders file!")
	    	await ctx.send(embed=embed)
	    	
    if type == "shop":
    	embed = uembed("Shop", "Welcome to the shop! \n What would you like to do?", color())
    	view = ShopButtonsView()
    	await ctx.send(embed=embed, view=view)
    if type == "test":
    	embed = uembed("Test", "Online!", color())
    	await ctx.send(embed=embed)
    if type == "unregister":
    	if user_check(ctx.author.id):
    		data = load_data()
    		data2 = data.pop(user.id, None)
    		embed = uembed("Unregister", f"Sucessfully unregistered {user.name}!", color())
    		await ctx.send(embed=embed)
    		save_data(data2)
    	else:
    	 embed = error("Sorry, you don't have permissions to use this command.")
    	 await ctx.send(embed=embed)    		
    if type == "debug":
    	data = load_data()
    	shop = get_shop()
    	orders = get_orders()
    	embed = uembed("Debug Data", f"{data}", color())
    	await ctx.send(embed=embed)
    	embed = uembed("Debug Shop", f'{shop}', color())
    	await ctx.send(embed=embed)
    	embed = uembed("Debug Orders", f'{orders}', color())
    	await ctx.send(embed=embed)
    	save_data(data)
    if type == "register":
    	list = ""
    	for member in ctx.guild.members:
	    	data = load_data()
	    	if not str(member.id) in data:
	    		username = await bot.fetch_user(member.id)
	    		display_name = username.display_name
	    		list = list + (f'{display_name}\n')
	    		open_account(member.id, data)
	    		save_data(data)
    	embed = uembed("Register", f"Sucessfully registered: \n {str(list).replace('[', '').replace(']', '')}", color())
    	await ctx.send(embed=embed)
    if type == "help":
    	embed = uembed("Help", "**help** \nShows the list of subcommands and their definitions. Usable by all.\n\n**show**\nShows you your current point balance. Usable by all.\n\n**modify**\nChanges the amount of points someone has, by default the target user is you. Usable by Hallowxity and Soup.\n\n**leaderboard**\nShows a leaderboard containing everyone registered in it. This command takes a while due to it looking up the user associated with everyone registered's ID. Usable by all.\n\n**register**\nRegisters the whole server. Usable by all.\n\n**unregister**\nUnregisters the target user from the system, used if people leave the developer team. Usable by Hallowxity and Soup.\n\n**test**\nTells you if the bot is online, if it is it will respond with 'Online!.' Otherwise it doesn't respond at all. Usable by all.\n\n**debug**\nSays the current contents of points_eco.json, shop.json, and orders.json. (The files containing the entirety of the bot's data.) Usable by all.\n\n**shop**\nResponds with a menu that lets you purchase, view or edit the shop. Edit's only available for Hallowxity, and Soup, otherwise usable by all. \n\nThe structure of $points is '$points <subcommand> <user> <amount>'. User and amount are optional, although amount is required for modify and user is required for modify and unregister.\n\nIf you would like to contribute to this, you can visit the Github repository [here](https://github.com/SpideyByte/phantasmagoria-points).", color())
    	await ctx.send(embed=embed)
    if type == "show":
    	target = user or ctx.author
    	target_ping = str(f'<@{target.id}>')
    	data = load_data()
    	open_account(target.id, data)
    	points = data[str(target.id)]
    	embed = uembed("Show", f'{target_ping} currently has {points} points.', color())
    	await ctx.send(embed=embed)
    	save_data(data)
    if type == "leaderboard":
    	embed = uembed("Leaderboard", "This command takes a while to load. Please wait.", color())
    	message = await ctx.send(embed=embed)
    	target = ctx.author
    	data = load_data()
    	open_account(target.id, data)
    	leaderboard = ""
    	sorted_points = sorted(data.items(), key=lambda item: item[1], reverse=True)
    	for rank, (player, score) in enumerate(sorted_points, start=1):
    		username = await bot.fetch_user(player)
    		display_name = username.display_name
    		leaderboard = leaderboard + (f"{rank}. {display_name} - {score}\n")
    	embed = uembed("Leaderboard", leaderboard, color())
    	await message.edit(embed=embed)
    	save_data(data)
    if type == "modify":
    	if user_check(ctx.author.id):
    		if 0 == amount:
		    	embed = error("Modify does not accept 0 as an input.")
		    	await ctx.send(embed=embed)
	    	if amount > 0:
		    	target = user or ctx.author
		    	target_ping = str(f'<@{target.id}>')
		    	data = load_data()
		    	open_account(target.id, data)
		    	data[str(target.id)] += amount
		    	points = data[str(target.id)]
		    	embed = uembed("Modify", f'{target_ping} just got {amount} more points! {target_ping} is currently at {points} points. ', color())
		    	await ctx.send(embed=embed)
		    	save_data(data)
	    	if 0 > amount:
		    	target = user or ctx.author
		    	target_ping = str(f'<@{target.id}>')
		    	data = load_data()
		    	open_account(target.id, data)
		    	data[str(target.id)]+= amount
		    	points = data[str(target.id)]
		    	calculated_amount = str(amount).removeprefix("-")
		    	embed = uembed("Modify", f'{target_ping} just lost {calculated_amount} points! {target_ping} is currently at {points} points. ', color())
		    	await ctx.send(embed=embed)
		    	save_data(data)
    	else:
    	 embed = error("Sorry, you don't have permissions to use this command.")
    	 await ctx.send(embed=embed)

def get_orders():
    if not os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, "w") as f:
            json.dump({}, f)
    with open(ORDER_FILE, "r") as f:
        return json.load(f)

def save_orders(order):
    with open(ORDER_FILE, "w") as f:
        json.dump(order, f, indent=4)

def create_order(product_data, userid):
	orders = get_orders()
	orderid = str(uuid.uuid4())
	orders[orderid] = {"product": product_data, "user": userid}
	save_orders(orders)
	return orderid

def get_shop():
    if not os.path.exists(SHOP_FILE):
        with open(SHOP_FILE, "w") as f:
            json.dump({}, f)
    with open(SHOP_FILE, "r") as f:
        return json.load(f)

def save_shop(shop):
    with open(SHOP_FILE, "w") as f:
        json.dump(shop, f, indent=4)

def add_shop_item(name, description, price, id):
	shop = get_shop()
	shop[id] = {"name": name, "description": description, "price": price, "id": id}
	save_shop(shop)

def item_from_id(id):
	shop = get_shop()
	return shop[id]

def shop_to_options():
	shop = get_shop()
	arr = []
	for i in shop:
		arr.append(discord.SelectOption(label=shop[i]["name"], description=f'{shop[i]["description"]} Price: {shop[i]["price"]}', value=shop[i]["id"]))
	return arr

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

def uembed(utitle, utext, ucolor):
	embed = discord.Embed(
		title = utitle,
		description = utext,
		color = ucolor
	)
	return embed

def color():
	return discord.Color.green()

def error(reason):
	return uembed("Error", reason, color())

async def send_embed(embed):
	for item in user_list():
		user = await bot.fetch_user(item)
		await user.send(embed=embed)

def user_check(id):
	if str(id) in user_list():
		return True
	return False

def user_list():
	array = [
		"1409793395555307541",
		"1258323457674838028",
		"1224550701259030598"
	]
	return array
	
def remove_order(id):
	orders = get_orders()
	orders2 = orders.pop(id, None)
	save_orders(orders2)

def points_more(user, i):
	data = load_data()
	open_account(user, data)
	points = data[str(user)]
	if points >= i:
		return True
	return False

bot.add_command(points)

bot.run(get_token())