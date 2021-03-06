import discord
from discord.ext import commands
from .config import *
import json
import random
import re
import asyncio

class Inventory(commands.Cog):
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

	# Most players will only have one character. The most recently created one is automatically assigned to them. This allows them to view who they're playing as.
	@commands.command(name="playing_as", aliases=["iam", "my_char", "mc"], help="View who you're playing as")
	async def playing_as(self, ctx):
		cs.execute(f"SELECT * FROM UserData WHERE GuildID == {ctx.guild.id} AND UserID == {ctx.message.author.id} LIMIT 1")

		try:
			char_nickname = cs.fetchone()[2]

			if(char_nickname == None):
				await ctx.send("You do not have a character set up! If you should, contact an admin.")
			else:
				# Get the character name by GuildID, UserID, and Nickname
				cs.execute(f"SELECT * FROM Characters WHERE GuildID == {ctx.guild.id} AND PlayerID == {ctx.message.author.id} AND CharNickname == ? LIMIT 1", (f"{char_nickname}",))

				char_name = cs.fetchone()[2]
				await ctx.send(f"{ctx.message.author} is playing as {char_name}!")

		except TypeError:
			await ctx.send("You do not have a character set up! If you should, contact an admin.")

	# Switch the character you're playing as. Very situational, like NPCs
	@commands.command(name="set_char", aliases=["setchar"], help="Switch your 'playing as' character. Very situational.")
	async def set_char(self, ctx):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		guild_id = ctx.guild.id
		player_id = ctx.message.author.id

		cs.execute(f"SELECT CharName, CharNickname FROM Characters WHERE GuildID == {guild_id} AND PlayerID == {player_id}")

		char_entries = cs.fetchall()
		embed_str = ''
		idx = 0
		for char in char_entries:
			embed_str = embed_str + f"[{idx}] {char[0]} - {char[1]}\n"
			idx += 1

		if (embed_str == ''):
			await ctx.send("You do not have any characters set up on this server! If you should, contact an admin to set one up.")
		else:
			cont = True
			color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
			embed = discord.Embed(title=f"Characters played by {ctx.message.author} on {ctx.guild}", color=color, description=embed_str)
			await ctx.send(embed=embed)

			await ctx.send("Enter a number: ")

			try:
				entry_num = await self.bot.wait_for('message', check=pred, timeout=60)
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

			if (cont):
				try:
					char_to_set = char_entries[int(entry_num.content)]

					cs.execute(f"UPDATE UserData SET PlayingAs = ? WHERE GuildID == {guild_id} AND UserID == {player_id}", (f"{char_to_set[1]}",))
					conn.commit()

					await ctx.send(f"{ctx.message.author} is now playing as {char_to_set[0]}!")
				except IndexError:
					await ctx.send("You did not enter a valid number!")
				except ValueError:
					await ctx.send("That is not a number!")

	# Embed inventory. Returns embed
	def embed_inventory(self, guild_id, char_nickname):
		# Get the character name by GuildID, UserID, and Nickname
		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()

		char_name = char_entry[2]
		inventory_json_str = str(char_entry[17])
		inventory = json.loads(inventory_json_str) # Dictionary object

		try:
			embed_0 = discord.Embed(title=f"Inventory for {char_name}", color=int(f"0x{char_entry[15]}", 16))
		except:
			embed_0 = discord.Embed(title=f"Inventory for {char_name}")

		embeds = [embed_0]
		
		i = 0 # embeds index
		n = 0 # item number

		for item, description in inventory.items():
			try:
				if (len(description) <= 200):
					embeds[i].add_field(name=item, value=description, inline=False)
				else:
					embeds[i].add_field(name=item, value=f"{description[0:200]}...", inline=False)
			except:
				embeds[i].add_field(name=item, value="No description", inline=False)
			n += 1

			if (n == 25):
				n = 0
				try:
					embed_n = discord.Embed(color=int(f"0x{char_entry[15]}", 16))
				except:
					embed_n = discord.Embed()
				
				embeds.append(embed_n)
				
				i += 1
		return embeds

	# The ever helpful inventory stuff!
	@commands.command(name="take", help="Add something to inventory. Optional (short) description. If the item name is more than one word, remember to use quotation marks!")
	async def take(self, ctx, item_name_base, *, description=None):

		player_id = ctx.message.author.id
		guild_id = ctx.guild.id

		# First, check for a character
		cs.execute(f"SELECT * FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

		try:
			char_nickname = cs.fetchone()[2]

			if(char_nickname == None):
				await ctx.send("You do not have a character set up!")
			else:
				# Get the character name by GuildID, UserID, and Nickname
				cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname}",))

				char_entry = cs.fetchone()

				char_name = char_entry[2]
				inventory_json_str = str(char_entry[17])
				inventory = json.loads(inventory_json_str) # Dictionary object

				cont = True

				# Loops through the inventory because the names may contain a trailing ' (xn)'
				for item_name_full in inventory:
					item_name_base_inv = self.item_to_base(item_name_full)

					# Item exists. Prevents duplicates based on case sensitivity.
					if (item_name_base.lower() == item_name_base_inv.lower()):
						new_item_name_full = self.get_item_str(item_name_full, increase=True)
						print(new_item_name_full)
						inventory[new_item_name_full] = inventory[item_name_full]
						del inventory[item_name_full]
						cont = False
						break

				if (cont): # Item wasn't in inventory
					inventory[item_name_base] = description

				# Dump to JSON
				json_dict_str = str(json.dumps(inventory))

				# Update entry
				cs.execute(f"UPDATE Characters SET Inventory = ? WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname}"))
				conn.commit()

				await ctx.send(f"{char_name} takes {item_name_base}.")

		except TypeError:
			await ctx.send("You do not have a character set up!")

	# Removing an item. TODO Allow null input for numbered list
	@commands.command(name="drop", help="Remove an item from inventory by name.")
	async def drop(self, ctx, *, item_name_base):
		player_id = ctx.message.author.id
		guild_id = ctx.guild.id

		# First, check for a character
		cs.execute(f"SELECT * FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")
		try:
			char_nickname = cs.fetchone()[2]

			if(char_nickname == None):
				await ctx.send("You do not have a character set up!")
			else:
				# Get the character name by GuildID, UserID, and Nickname
				cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname}",))

				char_entry = cs.fetchone()

				char_name = char_entry[2]
				inventory_json_str = str(char_entry[17])
				inventory = json.loads(inventory_json_str) # Dictionary object
				
				cont = True

				# Loops through the inventory because the names may contain a trailing ' (xn)'
				for item_name_full in inventory:
					item_name_base_inv = self.item_to_base(item_name_full)

					# Item exists
					if (item_name_base.lower() == item_name_base_inv.lower()):
						new_item_name_full = self.get_item_str(item_name_full, increase=False)

						if (new_item_name_full): # Not Null
							inventory[new_item_name_full] = inventory[item_name_full]

						del inventory[item_name_full]

						# Update entry
						json_dict_str = str(json.dumps(inventory))
						cs.execute(f"UPDATE Characters SET Inventory = ? WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname}"))
						conn.commit()

						await ctx.send(f"{char_name} drops {item_name_base}.")
						
						cont = False
						break

				if (cont): # Item wasn't in inventory
					await ctx.send(f"{char_name} does not have that in their inventory!")
					cont = False

		except TypeError:
			await ctx.send("You do not have a character set up!")

	# Viewing inventory. 25 items per embed
	@commands.command(name="inventory", aliases=["items"], help="View your inventory")
	async def inventory(self, ctx):
		player_id = ctx.message.author.id
		guild_id = ctx.guild.id

		# First, check for a character
		cs.execute(f"SELECT * FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")
		try:
			char_nickname = cs.fetchone()[2]

			if(char_nickname == None):
				await ctx.send("You do not have a character set up!")
			else:
				
				embeds = self.embed_inventory(guild_id, char_nickname)

				# Send
				for embed in embeds:
					await ctx.send(embed=embed)
		except TypeError:
			await ctx.send("You do not have a character set up!")			

	# Give and take commands for admins
	@commands.command(name="give", aliases=["give_item"], help="Add an item to any character's inventory.")
	@commands.has_permissions(administrator=True)
	async def give(self, ctx, *, char_nickname):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		# Check existance
		guild_id = ctx.guild.id

		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))
		char_entry = cs.fetchone()
		char_in_db = char_entry is not None

		if (char_in_db == False):
			await ctx.send("That character or nickname does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			# Display current inventory
			embeds = self.embed_inventory(guild_id, char_nickname)

			# Send
			for embed in embeds:
				await ctx.send(embed=embed)

			# Take input
			cont = True

			await ctx.send(f"Enter an item to give {char_entry[2]}:")

			try:
				item_name = await self.bot.wait_for('message', check=pred, timeout=60)
				item_name_base = item_name.content
			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				cont = False

			if (cont):
				await ctx.send(f"Enter a description for {item_name_base}:")

				try:
					description = await self.bot.wait_for('message', check=pred, timeout=60)
					description = description.content
				except asyncio.TimeoutError:
					await ctx.send("Timer expired! Please try again.")
					cont = False

			if (cont):
				inventory_json_str = str(char_entry[17])
				inventory = json.loads(inventory_json_str) # Dictionary object
			
			# Almost copy pasted code from !take. Should be modularized but I'm lazy

			# Loops through the inventory because the names may contain a trailing ' (xn)'
			if (cont):
				for item_name_full in inventory:
					item_name_base_inv = self.item_to_base(item_name_full)

					# Item exists. Prevents duplicates based on case sensitivity.
					if (item_name_base.lower() == item_name_base_inv.lower()):
						new_item_name_full = self.get_item_str(item_name_full, increase=True)
						inventory[new_item_name_full] = inventory[item_name_full]
						del inventory[item_name_full]
						cont = False
						break

			if (cont): # Item wasn't in inventory
				inventory[item_name_base] = description

			if (cont):
				# Dump to JSON
				json_dict_str = str(json.dumps(inventory))

				# Update entry
				cs.execute(f"UPDATE Characters SET Inventory = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname.title()}"))
				conn.commit()

				await ctx.send(f"{item_name_base} given to {char_entry[2]}.")

	@commands.command(name="confiscate", aliases=["take_from", "takefrom"], help="Take an item from any character's inventory.")
	@commands.has_permissions(administrator=True)
	async def confiscate(self, ctx, *, char_nickname):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		guild_id = ctx.guild.id

		# First, check for a character
		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()

		if(char_entry == None):
			await ctx.send("That character does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			# Display inventory
			embeds = self.embed_inventory(guild_id, char_nickname)
			for embed in embeds:
				await ctx.send(embed=embed)

			# Get input
			await ctx.send("Enter an item name to remove:")

			try:
				item_to_remove = await self.bot.wait_for('message', check=pred, timeout=60)
				item_name_base = item_to_remove.content

				# Set up things
				char_name = char_entry[2]
				inventory_json_str = str(char_entry[17])
				inventory = json.loads(inventory_json_str) # Dictionary object

			except asyncio.TimeoutError:
				await ctx.send("Timer expired! Please try again.")
				inventory = []
				
			cont = False
			# More or less copy-pasted from !drop because I'm too dumb to modularize

			# Loops through the inventory because the names may contain a trailing ' (xn)'
			for item_name_full in inventory:
				cont = True
				item_name_base_inv = self.item_to_base(item_name_full)

				# Item exists
				if (item_name_base.lower() == item_name_base_inv.lower()):
					new_item_name_full = self.get_item_str(item_name_full, increase=False)

					if (new_item_name_full): # Not Null
						inventory[new_item_name_full] = inventory[item_name_full]
					del inventory[item_name_full]

					# Update entry
					json_dict_str = str(json.dumps(inventory))
					cs.execute(f"UPDATE Characters SET Inventory = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"{item_name_base} taken from {char_name}.")
					
					cont = False
					break

			if (cont): # Item wasn't in inventory
				await ctx.send(f"{char_name} does not have that in their inventory!")

	# Admin command to see a player's inventory
	@commands.command(name="ainventory", aliases=["aitems"], help="View any character's inventory by nickname")
	@commands.has_permissions(administrator=True)
	async def ainventory(self, ctx, *, char_nickname):
		
		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {ctx.guild.id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()

		if(char_entry == None):
			await ctx.send("That character does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			# Display inventory
			embeds = self.embed_inventory(ctx.guild.id, char_nickname)
			for embed in embeds:
				await ctx.send(embed=embed)

	# Admin command to see a player's money
	@commands.command(name="amoney", aliases=["awallet"], help="View any character's currency")
	@commands.has_permissions(administrator=True)
	async def amoney(self, ctx, *, char_nickname):
		
		cs.execute(f"SELECT CharName, Currency FROM Characters WHERE GuildID == {ctx.guild.id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()

		if(char_entry == None):
			await ctx.send("That character does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			char_name = char_entry[0]
			char_currency = char_entry[1]

			# Get currency name
			cs.execute(f"SELECT CurrencyName FROM GuildData WHERE GuildID == {ctx.guild.id} LIMIT 1")
			currency_name = cs.fetchone()[0]

			await ctx.send(f"{char_name} has {char_currency} {currency_name}.")
			
def setup(bot):
	bot.add_cog(Inventory(bot))
