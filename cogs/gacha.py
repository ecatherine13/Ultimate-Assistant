import discord
from discord.ext import commands
from .config import *
import re
import random
import json
import asyncio

class Gacha(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Returns the item string to add to inventory. Can return None to indicate depletion of item.
	# If increase False, item is being dropped
	def get_item_str(self, item_name, increase=True):
		regex = "(.*) \(x([0-9]*)\)$"
		captures = re.search(regex, item_name)

		if (captures): # There is more than 1 item
			item_name = captures.group(1)
			item_amount = int(captures.group(2))

			if (increase): # add one
				if (item_amount >= 2): # Don't use number for less than 2
					item_str = f"{item_name} (x{item_amount+1})"
				else:
					item_str = item_name
			else: # remove one
				if (item_amount == 2): # Going down to 1
					item_str = item_name
				else:
					item_str = f"{item_name} (x{item_amount-1})"
		else: # Only one of the item (no number captured)
			if (increase):
				item_str = f"{item_name} (x2)"
			else:
				item_str = None
		return item_str

	# Take the full name and return the string without any (xn)
	def item_to_base(self, item_name_full):
		regex = "( \(x[0-9]*\))$"
		return re.sub(regex, "", item_name_full)

	# Display all gacha items with descriptions for guild. Returns list of embeds
	def embed_gacha(self, guild):
		# Get the character name by GuildID, UserID, and Nickname
		cs.execute(f"SELECT * FROM Gacha WHERE GuildID == {guild.id}")

		gacha_entry = cs.fetchall()

		embed_0 = discord.Embed(title=f"Gacha for {guild}")

		embeds = [embed_0]
		
		i = 0 # embeds index
		n = 0 # item number
		idx = 0
		for item in gacha_entry:
			name = item[1]
			description = item[2]
			
			if (len(description) > 200):
				embeds[i].add_field(name=f"[{idx}] {name}", value=f"{description[0:200]}...", inline=False)
			else:
				embeds[i].add_field(name=f"[{idx}] {name}", value=description, inline=False)

			idx += 1
			
			n += 1

			if (n == 25):
				n = 0
				embed_n = discord.Embed()
				
				embeds.append(embed_n)
				
				i += 1
		return embeds

	# New item
	@commands.command(name="new_item", aliases=["ni", "newitem"], help="Add an item to server's gacha.")
	@commands.has_permissions(administrator=True)
	async def new_item(self, ctx, *, item_name):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		cont = True
		guild_id = ctx.guild.id

		# Check if item exists
		cs.execute(f"SELECT 1 FROM Gacha WHERE GuildID == {guild_id} AND ItemName == ? LIMIT 1", (f"{item_name.title()}",))

		item_in_db = cs.fetchone() is not None

		if (item_in_db == True):
			await ctx.send("You have already set up an item with that name! Please try again.")
			cont = False

		if (cont):

			await ctx.send(f"Enter a description for {item_name}:")

			try:
				description = await self.bot.wait_for('message', check=pred, timeout=60)
				description = description.content
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			await ctx.send(f"Enter an image URL for {item_name}. If none, enter anything ('.', 'n/a', etc).")

			try:
				image_url = await self.bot.wait_for('message', check=pred, timeout=60)
				image_url = image_url.content
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

		if (cont):
			# Add to db
			cs.execute(f"INSERT INTO Gacha (GuildID, ItemName, Description, ImageURL) VALUES ({guild_id}, ?, ?, ?)", (f"{item_name}", f"{description}", f"{image_url}"))
			conn.commit()

			await ctx.send(f"{item_name} added to server gacha!")

	# Remove item(s)
	@commands.command(name="rem_item", aliases=["ri", "remitem"], help="Remove one or more gacha item from server.")
	@commands.has_permissions(administrator=True)
	async def rem_item(self, ctx):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		guild_id = ctx.guild.id
		
		# Get items
		cs.execute(f"SELECT * FROM Gacha WHERE GuildID == {guild_id}")
		items = cs.fetchall()

		# Embed display
		embeds = self.embed_gacha(ctx.guild)
		for embed in embeds:
			await ctx.send(embed=embed)

		# Get and check user input
		await ctx.send("Enter a number, or a list of comma separated numbers: (ex. 1, 3, 10) \nEnter 'X' to exit without deleting.")

		try:
			entry = await self.bot.wait_for('message', check=pred, timeout=60)
			entry = entry.content
			idx_to_delete_strs = entry.split(',')
		except asyncio.TimeoutError:
			await ctx.send("Timer expired! Please try again.")
			idx_to_delete_strs = []
				
		for idx_str in idx_to_delete_strs:

			cont = True

			# Exit if idx_str.upper() == 'X'
			if (idx_str.upper() == 'X'):
				await ctx.send("Exiting!")
				cont = False
				break

			# Typecast to int will fail if it's not a number
			try:
				idx_to_delete = int(idx_str)

				# If that works, warn about numbers not in range (up to idx because exit option)
				if (0 > idx_to_delete or len(items) < idx_to_delete):
					await ctx.send(f"{idx_to_delete} is not within the given range!")
					cont = False

			except:
				await ctx.send(f"{idx_str} is not a valid number!")
				cont = False

			# If those both check out, delete
			if (cont):
				item_to_delete = items[idx_to_delete]

				cs.execute(f"DELETE FROM Gacha WHERE GuildID == {guild_id} AND ItemName == ?", (f"{item_to_delete[1]}",))
				conn.commit()

				await ctx.send(f"{item_to_delete[1]} deleted from gacha!")

	@commands.command(name="gacha_list", aliases=["gachalist", "gatcha_list", "gatchalist"], help="View gacha items with descriptions for server.")
	@commands.has_permissions(administrator=True)
	async def gacha_list(self, ctx):
		embeds = self.embed_gacha(ctx.guild)

		for embed in embeds:
			await ctx.send(embed=embed)

	# Set currency name (also tells bot that the server uses a currency/gacha)
	@commands.command(name="set_currency", help="Set a name for game currency (monocoins, dollars, etc.)")
	@commands.has_permissions(administrator=True)
	async def set_currency(self, ctx, *, currency_name):
		guild_id = ctx.guild.id

		# add to db. Nice and simple
		cs.execute(f"UPDATE GuildData SET CurrencyName = ? WHERE GuildID == {guild_id}", (f"{currency_name}",))
		conn.commit()

		await ctx.send(f"Set currency for {ctx.guild} to {currency_name}.")

	@commands.command(name="give_money", aliases=["pay", "givemoney", "givecoins", "give_coins"], help="Grant currency to a player using their character nickname. Enter a negative amount to subtract currency.")
	@commands.has_permissions(administrator=True)
	async def give_money(self, ctx, char_nickname, amount):
		guild_id = ctx.guild.id

		# Check that character exists
		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))
		char_entry = cs.fetchone()
		char_in_db = char_entry is not None

		if (char_in_db == False):
			await ctx.send("That character or nickname does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			try:

				amount = int(amount)
				new_amount = char_entry[18] + amount

				# Commit to db
				cs.execute(f"UPDATE Characters SET Currency = {new_amount} WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
				conn.commit()

				# currency name
				cs.execute(f"SELECT CurrencyName from GuildData WHERE GuildID == {guild_id}")

				currency_name = cs.fetchone()[0]
				
				if (amount > 0):
					await ctx.send(f"{amount} {currency_name} given to {char_entry[2]}.")
				else:
					await ctx.send(f"{abs(amount)} {currency_name} taken from {char_entry[2]}.")


			except:
				await ctx.send("That is not a valid number!")

	# Check how much money you have (player command)
	@commands.command(name="money", aliases=["wallet", "coins", "currency"], help="See how much currency you have.")
	async def money(self, ctx):
		guild_id = ctx.guild.id
		player_id = ctx.message.author.id

		# Get the player's character (if it exists)
		cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")
		try:
			char_nickname = cs.fetchone()[0]

			# Char info
			cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
			
			char_entry = cs.fetchone()
			char_name = char_entry[2]
			char_currency = char_entry[18]

			# Currency name
			cs.execute(f"SELECT CurrencyName FROM GuildData WHERE GuildID == {guild_id}")
			currency_name = cs.fetchone()[0]

			await ctx.send(f"{char_name} has {char_currency} {currency_name}.")

		except:
			await ctx.send("You are not currently playing a character on this server!")

	# TODO - Command for mods to see all character's current financial status

	# Draw from the gacha! Only allow if non-zero coins 
	@commands.command(name="gacha", aliases=["gatcha", "draw", "g"], help="Draw one item from the gacha!")
	async def gacha(self, ctx):
		guild_id = ctx.guild.id
		player_id = ctx.message.author.id

		cont = True

		# Get the player's character (if it exists)
		cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

		try:
			char_nickname = cs.fetchone()[0]
			has_char = char_nickname is not None

			if (has_char == False):
				await ctx.send("You are not currently playing a character on this server!")
				cont = False

		except AttributeError:
			await ctx.send("You are not currently playing a character on this server! If you should be, contact an administrator to set one up.")
			cont = False

		except TypeError:
			await ctx.send("You are not currently playing a character on this server! If you should be, contact an administrator to set one up.")
			cont = False

		# See if there are any gacha items set up. If none, don't continue.
		if (cont):
			cs.execute(f"SELECT * FROM Gacha WHERE GuildID == {guild_id}")
			gacha_list = cs.fetchall()

			if (len(gacha_list) == 0):
				await ctx.send("No gacha items available!")
				cont = False

		# Check character's currency. If <= 0, they cannot draw
		if (cont):
			# Char info
			cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
			
			char_entry = cs.fetchone()
			char_name = char_entry[2]
			char_currency = char_entry[18]

			# Currency name
			cs.execute(f"SELECT CurrencyName FROM GuildData WHERE GuildID == {guild_id}")
			currency_name = cs.fetchone()[0]

			if (char_currency <= 0):
				await ctx.send(f"{char_name} does not have any {currency_name} to draw!")
				cont = False
			else:
				# Subtract 1 from player currency
				new_amount = char_currency - 1
				cs.execute(f"UPDATE Characters SET Currency = {new_amount} WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
				conn.commit()

		# Finally, draw an item.
		if (cont):
			# Select a random item from the gacha list
			item_idx = random.randint(0, len(gacha_list)-1)
			item_drawn = gacha_list[item_idx]
			item_name_base = item_drawn[1]
			item_description = item_drawn[2]
			item_image_url = item_drawn[3]

			# Display item (part 1)
			color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
			embed = discord.Embed(title=f"{char_name} obtains {item_name_base}!", color=color, description=item_description)

			# Add item to the player's inventory. If they already have it, make a note of it.
			# TODO - account for multiple of same gacha item.
			inventory_json_str = str(char_entry[17])
			inventory = json.loads(inventory_json_str) # Dictionary object

			for item_name_full in inventory:

				item_name_base_inv = self.item_to_base(item_name_full)

				# Item exists. Prevents duplicates based on case sensitivity.
				if (item_name_base.lower() == item_name_base_inv.lower()):
					new_item_name_full = self.get_item_str(item_name_full, increase=True)
					inventory[new_item_name_full] = inventory[item_name_full]
					del inventory[item_name_full]
					cont = False
					embed.set_footer(text=f"Aw, it's a repeat. Duplicate given to {char_name}.")
					break

			if (cont): # Item wasn't in inventory
				inventory[item_name_base] = item_description
				embed.set_footer(text=f"{item_name_base} given to {char_name}!")

			# Dump to JSON
			json_dict_str = str(json.dumps(inventory))

			# Update entry
			cs.execute(f"UPDATE Characters SET Inventory = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname}"))
			conn.commit()

			try:
				embed.set_thumbnail(url=item_image_url)
				await ctx.send(embed=embed)
			except:
				embed.set_thumbnail(url="https://discord.com/null-image-placeholder.jpeg") # Hacky fix to prevent error
				await ctx.send(embed=embed)

def setup(bot):
	bot.add_cog(Gacha(bot))
