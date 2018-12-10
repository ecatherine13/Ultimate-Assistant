import discord
from discord.ext import commands
from .config import *
import re
import random

class Character_Management:
	def __init__(self, bot):
		self.bot = bot

	def embed_char_info(self, guild_id, char_nickname):
		# Get the info
		cs.execute(f"SELECT * FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		data = cs.fetchone()

		# At a minimum, an entry will have GuildID, PlayerID, CharName, CharNickname
		name = data[2]

		# Handle public bios > 1024 characters
		if(data[12] != None and len(data[12]) > 1024):
			if (data[15] != None): # > 1024, color
				embed = discord.Embed(title=name, color=int(f"0x{data[15]}", 16), description=data[12])
			else: # > 1024, color DNE
				embed = discord.Embed(title=name, description=data[12])
		else:
			if (data[15] != None): # <= 1024, color
				embed = discord.Embed(title=name, color=int(f"0x{data[15]}", 16))
			else: # <= 1024, color DNE
				embed = discord.Embed(title=name)
			
		embed_str = ''

		# Talent data[4]
		if (data[4] != None):
			embed_str += f"**Talent**: {data[4]}\n"

		# Age data[5]
		if (data[5] != None):
			embed_str += f"**Age**: {data[5]}\n"

		# Birthday data[6] (and so on so forth)
		if (data[6] != None):
			embed_str += f"**Birthday**: {data[6]}\n"

		# Height
		if (data[7] != None):
			embed_str += f"**Height**: {data[7]}\n"

		# Weight
		if (data[8] != None):
			embed_str += f"**Weight**: {data[8]}\n"

		# Chest *sigh
		if (data[9] != None):
			embed_str += f"**Chest**: {data[9]}\n"

		# Likes
		if (data[10] != None):
			embed_str += f"**Likes**: {data[10]}\n"

		# Dislikes
		if (data[11] != None):
			embed_str += f"**Dislikes**: {data[11]}\n"

		# End of first field
		if (embed_str != ''):
			embed.add_field(name="Public Info", value=embed_str[0:700], inline=False)

		# Public Bio. Separate field
		if (data[12] != None and len(data[12]) <= 1024):
			embed.add_field(name="Public Bio", value=data[12], inline=False)

		# Public Appearance. Separate field
		if (data[16] != None):
			embed.add_field(name="Public Appearance", value=data[16], inline=False)

		# Notes / Other. Separate field
		if (data[14] != None):
			embed.add_field(name="Other", value=data[14], inline=False)

		# Ref_URL data[13]
		# TODO - Prevent the bad-formed URL error if the url is not valid.
		if (data[13] != None):
			embed.set_thumbnail(url=data[13])

		return embed

	async def display_char_info(self, ctx, embed):
		try:
			await ctx.send(embed=embed)
		except:
			embed.set_thumbnail(url="https://discord.com/null-image-placeholder.jpeg") # Hacky fix to prevent error
			await ctx.send(embed=embed)

	@commands.command(name="new_char", aliases=["newchar", "nc"], help="Add a new character. You will have to ping the player.")
	@commands.has_permissions(administrator=True)
	async def new_char(self, ctx, player, *, char_name):
		# For checking input author
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		embed = discord.Embed(title=f"Setting up {char_name}! Please set a unique nickname now for look-up purposes. A one-word nickname is recommended, though not required. (ex. their first name)")
		embed.set_footer(text="timeout 60 s")

		await ctx.send(embed=embed)

		nickname = await self.bot.wait_for('message', check=pred, timeout=60)
		nickname = nickname.content

		# Add to db
		regex = "<@!?([0-9]{18})>" # user id capture

		player_id_str = re.findall(regex, player)
		player_id = int(player_id_str[0])

		guild_id = ctx.guild.id

		# If player is not in table (first character), add them
		cs.execute(f"SELECT 1 FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

		player_in_db = cs.fetchone() is not None

		if (player_in_db == False):
			cs.execute(f"INSERT INTO UserData (GuildID, UserID) VALUES ({guild_id}, {player_id})")

		# Check if it already exists. This also prevents two characters with the same nickname in one guild
		cs.execute(f"SELECT 1 FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{nickname.title()}",))

		char_in_db = cs.fetchone() is not None

		if (char_in_db == True):
			await ctx.send("You have already set up a character with that nickname! Please try again.")
		else:
			# Add to db
			cs.execute(f"INSERT INTO Characters (GuildID, PlayerID, CharName, CharNickname) VALUES ({guild_id}, {player_id}, ?, ?)", (f"{char_name}", f"{nickname.title()}"))
			
			# Assign to player (GuildID, UserID -> ActiveChar = 'Nickname')
			cs.execute(f"UPDATE UserData SET PlayingAs = ? WHERE GuildID == {guild_id} AND UserID == {player_id}", (f"{nickname.title()}",))

			conn.commit()

			await ctx.send(f"{char_name} set, please use `!uc {nickname}` to add info.")

	@new_char.error
	async def new_char_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong! Did you ping the player? `!new_char @Username Character Name`")

	@commands.command(name="update_char", aliases=["updatechar", "uc"], help="Update  a single character's info")
	@commands.has_permissions(administrator=True)
	async def update_char(self, ctx, *, char_nickname):
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
			player_id = char_entry[1]
			# Display embed with current info, and then menu
			embed = self.embed_char_info(guild_id, char_nickname)
			await self.display_char_info(ctx, embed)
			
			# Selection Menu Display
			menu_str_IC =	"""
							[1] Name
							[2] Talent
							[3] Age
							[4] Birthday
							[5] Height
							[6] Weight
							[7] Chest
							[8] Likes
							[9] Dislikes
							[10] Public Appearance
							[11] Public Bio
							[12] Reference
							"""
			menu_str_meta =	"""
							[13] Nickname (Name used for lookup)
							[14] Embed Color (Paste a hex code)
							[15] Other (Miscellaneous notes)\n
							[16] Finish Update
							"""
			
			menu_embed = discord.Embed(title="Choose an option:")
			menu_embed.add_field(name="IC Info", value=menu_str_IC, inline=True)
			menu_embed.add_field(name="Meta Info", value=menu_str_meta, inline=True)

			menu_embed.set_footer(text="Inputs are case sensitive! Timeout for all is 60 s")

			await ctx.send(embed=menu_embed)

			# Await user input on a loop
			cont = True
			while (cont):
				user_selection = await self.bot.wait_for("message", check=pred, timeout=60)

				try:
					user_selection = int(user_selection.content)
				except ValueError:
					await ctx.send("You did not input a number!")
					user_selection = 16

				# And this is where I lament the absence of switch statements in Python

				if (user_selection == 16): # Exit
					cont = False
					await ctx.send("Finished.")
					embed = self.embed_char_info(guild_id, char_nickname)
					await self.display_char_info(ctx, embed)
				
				elif (user_selection == 1): #Name
					await ctx.send("Enter a new name:")
					new_name = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET Charname = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_name.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set name to {new_name.content}. Choose another field or input [16] to Exit")

				elif (user_selection == 2): # Talent
					await ctx.send("Enter a new talent:")
					new_talent = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET PublicTalent = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_talent.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set talent to {new_talent.content}. Choose another field or input [16] to Exit")

				elif (user_selection == 3): # Age
					await ctx.send("Enter a new age:")
					new_age = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET CharAge = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_age.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set age to {new_age.content}. Choose another field or input [16] to Exit")

				elif (user_selection == 4): # Birthday
					await ctx.send("Enter a new birthday:")
					new_bday = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET CharBirthday = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_bday.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set birthday to {new_bday.content}. Choose another field or input [16] to Exit")
				
				elif (user_selection == 5): # Height
					await ctx.send("Enter a new height:")
					new_height = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET CharHeight = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_height.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set height to {new_height.content}. Choose another field or input [16] to Exit")

				elif (user_selection == 6): # Weight
					await ctx.send("Enter a new weight:")
					new_weight = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET CharWeight = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_weight.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set weight to {new_weight.content}. Choose another field or input [16] to Exit")
				
				elif (user_selection == 7): # Chest
					await ctx.send("Enter a new chest size:")
					new_chest = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET CharChest = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_chest.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set chest size to {new_chest.content}. Choose another field or input [16] to Exit")

				elif (user_selection == 8): # Likes
					await ctx.send("Enter list of likes:")
					likes = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET Likes = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{likes.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set likes to '{likes.content}'. Choose another field or input [16] to Exit")

				elif (user_selection == 9): # Dislikes
					await ctx.send("Enter list of dislikes:")
					dislikes = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET Dislikes = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{dislikes.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set dislikes to '{dislikes.content}'. Choose another field or input [16] to Exit")

				elif (user_selection == 10): # Public Appearance. Check length
					await ctx.send("Enter a public appearance: (Cannot exceed 1024 characters!)")
					appearance = await self.bot.wait_for("message", check=pred, timeout=60)

					if (len(appearance.content) <= 1024):
						# Commit to DB
						cs.execute(f"UPDATE Characters SET PublicAppearance = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{appearance.content}", f"{char_nickname.title()}"))
						conn.commit()

						await ctx.send(f"Set public appearance. Choose another field or input [16] to Exit")
					else:
						await ctx.send(f"Your entry is {len(appearance.content) - 1024} characters too lon! Input [10] to try again or [16] to Exit.")
				
				elif (user_selection == 11): # Public Bio.
					await ctx.send("Enter a public bio: (No character limit, but under 1024 is recommended.)")
					bio = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET PublicBio = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{bio.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set public bio. Choose another field or input [16] to Exit")
									
				elif (user_selection == 12): # Ref
					await ctx.send("Enter an image url: (must be the url, not a pasted image)")
					ref = await self.bot.wait_for("message", check=pred, timeout=60)

					# Commit to DB
					cs.execute(f"UPDATE Characters SET RefURL = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{ref.content}", f"{char_nickname.title()}"))
					conn.commit()

					await ctx.send(f"Set reference URL. Choose another field or input [16] to Exit")

				elif (user_selection == 13): # Nickname. Adjust char_nickname!
					await ctx.send("Enter a new nickname:")
					new_nickname = await self.bot.wait_for("message", check=pred, timeout=60)

					# Check if nickname already exists
					cs.execute(f"SELECT 1 FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{new_nickname.content.title()}",))

					char_entry = cs.fetchone()
					char_in_db = char_entry is not None

					if(char_in_db == True):
						await ctx.send("This nickname is already taken (or you didn't change it at all)! To try again, input [12], or exit with [16].")
					else:
						# Commit to DB
						cs.execute(f"UPDATE Characters SET CharNickname = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{new_nickname.content.title()}", f"{char_nickname.title()}"))

						# Update the nickname 'pointer' in UserData
						cs.execute(f"UPDATE UserData SET PlayingAs = ? WHERE GuildID == {guild_id} AND UserID == {player_id}", (f"{new_nickname.content.title()}",))

						conn.commit()

						char_nickname = new_nickname.content.title()

						await ctx.send(f"Set nickname to '{new_nickname.content}'. Choose another field or input [16] to Exit")

				elif (user_selection == 14): # Embed color. Check for validity.
					await ctx.send("Enter a hex code (ex. #FF0000 or ff0000):")
					hexcode = await self.bot.wait_for("message", check=pred, timeout=60)

					hex_match = re.search(r'^#?((?:[0-9a-fA-F]{3}){1,2})$', hexcode.content)

					if (hex_match == None):
						await ctx.send("That is not a valid hex code! To try again, enter [13], or exit with [16]")
					else:
						# Commit to DB
						cs.execute(f"UPDATE Characters SET EmbedColor = '{hex_match.group(1)}' WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
						conn.commit()

						await ctx.send(f"Set embed color. Choose another field or input [16] to Exit")

				elif (user_selection == 15): # Other
					await ctx.send("Enter any extra info you wish: (Cannot exceed 1024 characters!)")
					notes = await self.bot.wait_for("message", check=pred, timeout=60)

					if(len(notes.content) <= 1024):
						# Commit to DB
						cs.execute(f"UPDATE Characters SET Notes = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{notes.content}", f"{char_nickname.title()}"))
						conn.commit()

						await ctx.send(f"Set extra info. Choose another field or input [16] to Exit")
					else:
						await ctx.send(f"That is {str(len(notes.content) - 1024)} characters too long! Input [15] to try again, or [16] to exit.")

				else: # Invalid number
					await ctx.send("Not a valid number!")

	@update_char.error
	async def update_char_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong!. Did you enter a valid number?")

	@commands.command(name="rem_char_info", aliases=["ucr", "uc_remove"], help="Remove a field from a single character's info.")
	@commands.has_permissions(administrator=True)
	async def rem_char_info(self, ctx, *, char_nickname):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		# Check existance
		guild_id = ctx.guild.id

		cs.execute(f"SELECT 1 FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_in_db = cs.fetchone() is not None

		if(char_in_db == False):
			await ctx.send("That character or nickname does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			# Display embed with current info, and then menu
			embed = self.embed_char_info(guild_id, char_nickname)
			await self.display_char_info(ctx, embed)
			
			# Selection Menu Display
			menu_str_IC =	"""
							[1] Talent
							[2] Age
							[3] Birthday
							[4] Height
							[5] Weight
							[6] Chest
							[7] Likes
							[8] Dislikes
							[9] Public Appearance
							[10] Public Bio
							[11] Reference
							"""
			menu_str_meta =	"""
							[12] Embed Color
							[13] Other\n
							[14] Finish Update
							"""
			menu_embed = discord.Embed(title="Choose an option:")
			menu_embed.add_field(name="IC Info", value=menu_str_IC, inline=True)
			menu_embed.add_field(name="Meta Info", value=menu_str_meta, inline=True)

			menu_embed.set_footer(text="Inputs are case sensitive! Timeout for all is 60 s")

			await ctx.send(embed=menu_embed)

			# Await user input on a loop
			cont = True
			while (cont):
				user_selection = await self.bot.wait_for("message", check=pred, timeout=60)
				user_selection = int(user_selection.content)

				# And this is where I lament the absence of switch statements in Python

				if (user_selection == 14): # Exit
					cont = False
					await ctx.send("Finished.")
					await ctx.send(embed=self.embed_char_info(guild_id, char_nickname))

				elif (user_selection == 1): # Talent
					cs.execute(f"UPDATE Characters SET PublicTalent = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 2): # Age
					cs.execute(f"UPDATE Characters SET CharAge = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 3): # Birthday
					cs.execute(f"UPDATE Characters SET CharBirthday = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 4): # Height
					cs.execute(f"UPDATE Characters SET CharHeight = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 5): # Weight
					cs.execute(f"UPDATE Characters SET CharWeight = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 6): # Chest
					cs.execute(f"UPDATE Characters SET CharChest = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 7): # Likes
					cs.execute(f"UPDATE Characters SET Likes = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 8): # Dislikes
					cs.execute(f"UPDATE Characters SET Dislikes = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 9): # Public Appearance
					cs.execute(f"UPDATE Characters SET PublicAppearance = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 10): # Public Bio
					cs.execute(f"UPDATE Characters SET PublicBio = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 11): # Ref URL
					cs.execute(f"UPDATE Characters SET RefURL = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 12): # Embed Color
					cs.execute(f"UPDATE Characters SET EmbedColor = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				elif (user_selection == 13): # Other
					cs.execute(f"UPDATE Characters SET Notes = null WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_nickname.title()}",))
					conn.commit()

					await ctx.send("Done. Choose another field or finish with [14]")

				else:
					await ctx.send("Invalid input!")

	@rem_char_info.error
	async def rem_char_info_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong! Did you enter a valid number?")

	@commands.command(name="nicknames", aliases=["lcn", "list_char_nicknmes", "names", "listnames", "listnicknames"], help="Get a list of characters in server with corresponding nicknames")
	async def list_char_nicknames(self, ctx):
		guild_name = ctx.guild
		color = int("%06x" % random.randint(0, 0xFFFFFF), 16)

		embed = discord.Embed(color=color)
		embed_str = ''

		# Get all characters in guild
		guild_chars = cs.execute(f"SELECT CharName, CharNickname FROM Characters WHERE GuildID == {guild_name.id}")

		for char in guild_chars.fetchall():
			embed_str += f"{char[0]}: {char[1]}\n"

		if (embed_str != ''):
			embed.add_field(name=f"Characters in {guild_name}", value=embed_str)
		else:
			embed.add_field(name=f"Characters in {guild_name}", value="No characters yet!")

		await ctx.send(embed=embed)

	@commands.command(name="lookup", aliases=["search", "handbook", "profile"], help="Lookup a character by their nickname")
	async def lookup(self, ctx, *, char_nickname):
		# Check existance
		guild_id = ctx.guild.id

		cs.execute(f"SELECT 1 FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_in_db = cs.fetchone() is not None

		if(char_in_db == False):
			await ctx.send("That character or nickname does not exist! Use `!nicknames` or `!lcn` to see available characters.")
		else:
			# Display embed with current info, and then menu
			embed = self.embed_char_info(guild_id, char_nickname)
			await self.display_char_info(ctx, embed)

	@commands.command(name="rem_char", aliases=["rc", "remchar"], help="Remove a character using their nickname")
	@commands.has_permissions(administrator=True)
	async def rem_char(self, ctx, *, char_nickname):
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
			# Display their info to confirm
			embed = self.embed_char_info(guild_id, char_entry[3])
			await self.display_char_info(ctx, embed)

			# Confirmation
			await ctx.send(f"Are you sure you want to delete {char_entry[2]} from the server? (y/n)")
			confirm = await self.bot.wait_for('message', check=pred, timeout=60)

			if (confirm.content.lower() == 'y' or confirm.content.lower() == "yes"):
				cs.execute(f"SELECT PlayerID FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_entry[3]}",))
				player_id = cs.fetchone()[0]

				# Remove from Characters
				cs.execute(f"DELETE FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{char_entry[3]}",))
				conn.commit()

				# Set the player's character to Null in UserData
				cs.execute(f"UPDATE UserData SET PlayingAs = NULL WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

				await ctx.send(f"Removed {char_entry[2]} from {ctx.guild}")
			
			else:
				await ctx.send("Not confirmed. Exiting.")

def setup(bot):
	bot.add_cog(Character_Management(bot))