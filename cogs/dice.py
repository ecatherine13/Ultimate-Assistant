import discord
from discord.ext import commands
import re
import random
from .config import *
import json

class Dice(commands.Cog):
	
	def __init__(self, bot):
		self.bot = bot

	def embed_stats(self, guild_id, char_nickname):
		cs.execute(f"SELECT CharName, EmbedColor, Stats FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()
		char_name = char_entry[0]
		embed_color = char_entry[1]
		stats_str = char_entry[2]

		stats_dict = json.loads(stats_str)

		stats_str = ""
		for stat_name, stat_value in stats_dict.items():
			stats_str = stats_str + f"**{stat_name}**: {stat_value}\n"

		if (stats_str == ""):
			stats_str = "None set up!"

		try:
			embed = discord.Embed(title=f"Stats for {char_name}:", color=int(f"0x{embed_color}"), description=stats_str)
		except:
			embed = discord.Embed(title=f"Stats for {char_name}:", description=stats_str)

		return embed

	def embed_custom_rolls(self, guild_id, char_nickname):
		cs.execute(f"SELECT CharName, EmbedColor, CustomRolls FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

		char_entry = cs.fetchone()
		char_name = char_entry[0]
		embed_color = char_entry[1]
		custom_rolls_str = char_entry[2]

		custom_rolls_dict = json.loads(custom_rolls_str)

		custom_rolls_str = ""
		for roll_name, roll_str in custom_rolls_dict.items():
			custom_rolls_str = custom_rolls_str + f"**{roll_name}**: {roll_str}\n"

		if (custom_rolls_str == ""):
			custom_rolls_str = "None set up!"

		try:
			embed = discord.Embed(title=f"Custom rolls for {char_name}:", color=int(f"0x{embed_color}"), description=custom_rolls_str)
		except:
			embed = discord.Embed(title=f"Custom rolls for {char_name}:", description=custom_rolls_str)

		return embed

	def single_roll(self, n, m):
		results = []
		result = 0
		
		if (int(n) <= 1000): # avoid memory errors
			for i in range(0, int(n)):
				result = random.randint(1, int(m))
				results.append(result)
		else: # TODO give proper warning
			return [0]
		
		return results

	def full_roll(self, ctx, s):
		player_name = ctx.message.author

		re1 = '([0-9]*d[0-9]+)' # Finds all instances of ndm, captures 'ndm'
		re2 = '([\+|-])' # plus or minus
		re3 = '(\D)' # Finds all numbers

		matches1 = re.findall(re1, s)
		matches2 = re.findall(re2, s)
		matches3 = (re.sub("\D", " ", s)).split()

		# insert positive into matches2, since the first operation is always +
		matches2.insert(0, '+')

		dice_msg1 = ''
		dice_msg2 = ''
		
		dice_total = 0
		count = 0 # For later
		regex_d = '([0-9]*)[d|D]([0-9]*)'
		d_max = 0
		d_min = 0
		for i in range(0, len(matches1)):
			roll_str = matches1[i]
			operation = matches2[i]

			matches = re.match(regex_d, roll_str)

			if (matches.group(1) == ''):
				n = 1
				m = int(matches.group(2))
				count += 1
			else:
				n = int(matches.group(1))
				m = int(matches.group(2))
				count += 2
			d_max += n*m
			d_min += n

			dice_results = self.single_roll(int(n), int(m))

			if(operation == "+" and i > 0):
				dice_msg1 =dice_msg1 + " + " + str(dice_results)
				dice_msg2 = dice_msg2 + " + " + str(sum(dice_results))
				dice_total += sum(dice_results)
			elif(operation == "+" and i == 0):
				dice_msg1 = dice_msg1 + str(dice_results)
				dice_msg2 = dice_msg2 + str(sum(dice_results))
				dice_total += sum(dice_results)
			elif(operation == "-"):
				dice_msg1 = dice_msg1 + " - " + str(dice_results)
				dice_msg2 = dice_msg2 + " - " + str(sum(dice_results))
				dice_total -= sum(dice_results)

		# Now deal with the modifiers portion

		remaining_operations = len(matches3) - count

		mod_msg1 = ''
		mod_msg2 = ''
		matches3 = matches3[-remaining_operations:]
		matches2 = matches2[-remaining_operations:]

		mod_total = 0

		for i in range(0, remaining_operations):
			operation = matches2[i]
			mod = matches3[i]
			if (operation == "+"):
				mod_msg1 = mod_msg1 + " + " + str(mod)
				mod_msg2 = mod_msg2 + " + " + str(mod)
				mod_total += int(mod)
			elif (operation == "-"):
				mod_msg1 = mod_msg1 + " - " + str(mod)
				mod_msg2 = mod_msg2 + " - " + str(mod)
				mod_total -= int(mod)

		# put it all together
		msg1 = dice_msg1 + mod_msg1
		msg2 = dice_msg2 + mod_msg2
		total = dice_total + mod_total

		color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
		s = "{} rolls {}".format(player_name, s)
		
		# Long die rolls will break the embed limit. In this case, make msg 1 the embed description
		if (len(msg1) < 256):
			embed = discord.Embed(title=s, color=color)
			embed.add_field(name=msg1, value=msg2+" = **" + str(total) + "**", inline=True)
		elif (len(msg1) >= 256 and len(msg1) < 2048):
			embed = discord.Embed(title=s, color=color, description=msg1)
			embed.add_field(name=f"{msg2} =", value="**" + str(total) + "**", inline=True)
		else:
			embed = discord.Embed(title=s, color=color, description=f"{msg1[0:2040]}...")
			embed.add_field(name=f"{msg2} =", value="**" + str(total) + "**", inline=True)

		return embed

	# Dice rolls that are fancier than Tatsu's (though definitely less robust)
	# There has to be a more efficient way to do this, so please send feedback!
	@commands.command(name="roll", aliases=['r'], help="Use standard notation such as 1d4+d6-1")
	async def roll(self, ctx, *, s):
		embed = self.full_roll(ctx, s)

		await ctx.send(embed=embed)

		try:
			await ctx.message.delete()
		except:
			pass
		
	@roll.error
	async def roll_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong! Are you sure you used the right notation? For example:\n`2d6+d4-2`")

	# Calculator. Could go in Utilities, but having the stats readily is helpful
	@commands.command(name="calc", aliases=['c', "calculate"], help="Evaluate a simple math expression, or use your defined stat names as input. Uses python math notation. For help, see https://en.wikibooks.org/wiki/Python_Programming/Basic_Math#Mathematical_Operators")
	async def calc(self, ctx, *, expression):
		# Can be used by anyone, but if they have a character, look for stats
		try:
			guild_id = ctx.guild.id
			player_id = ctx.message.author.id

			# Get the player's character (if it exists)
			cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

			char_nickname = cs.fetchone()[0]

			# Char info
			cs.execute(f"SELECT Stats FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

			# parse Stats json string
			stats_str = str(cs.fetchone()[0])
			stats_dict = json.loads(stats_str)
			# for each stat in stats_dict, replace with its value. The stat-setting method should check to make sure it's a proper floating point number. This one can assume validity.
			for stat, stat_val in stats_dict.items():
				expression = expression.lower().replace(stat.lower(), stat_val)

		except:
			pass
		try:
			result = eval(expression)

			await ctx.send(result)

		except:
			await ctx.send("That is not a valid expression!")

	# setting stats
	@commands.command(name="set_stat", aliases=["ns", "ss", "newstat", "us", "updatestat", "setstat"], help="Add or update a stat for a character to use in calculations. Stat names must be a single word.")
	async def set_stat(self, ctx, stat_name, stat_value):

		# first, make sure stat_value is a proper float
		cont = True

		try:
			float(stat_value)
		except:
			await ctx.send("Please use a number for the stat value!")
			cont = False

		if (cont):
			try:
				guild_id = ctx.guild.id
				player_id = ctx.message.author.id

				# Get the player's character (if it exists)
				cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

				char_nickname = cs.fetchone()[0]

				# Char info
				cs.execute(f"SELECT Stats FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

				# parse Stats json string
				stats_str = str(cs.fetchone()[0])
				stats_dict = json.loads(stats_str)

			except:
				await ctx.send("You must have a character set to use this!")
				cont = False

		if (cont):
			stats_dict[stat_name] = str(stat_value)

			json_dict_str = json.dumps(stats_dict)

			# update db and commit
			cs.execute(f"UPDATE Characters SET Stats = ? WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname.title()}"))
			conn.commit()

			await ctx.send(f"Set {stat_name} to {stat_value} for {char_nickname}.")

			embed = self.embed_stats(guild_id,char_nickname)

			await ctx.send(embed=embed)

	# Setting stats, admin version
	@commands.command(name="aset_stat", aliases= ["ans", "anewstat", "aus", "aupdatestat", "asetstat"], help="Add or update a stat for a character to use in calculations. Stat names must be a single word. Admin version")
	@commands.has_permissions(administrator=True)
	async def aset_stat(self, ctx, char_nickname, stat_name, stat_value):
		# first, make sure stat_value is a proper float
		cont = True

		try:
			float(stat_value)
		except:
			await ctx.send("Please use a number for the stat value!")
			cont = False

		if (cont):
			try:
				guild_id = ctx.guild.id

				# Char info
				cs.execute(f"SELECT Stats FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

				# parse Stats json string
				stats_str = str(cs.fetchone()[0])
				stats_dict = json.loads(stats_str)

			except:
				await ctx.send("That nickname does not exist in this server!")
				cont = False

		if (cont):
			stats_dict[stat_name] = str(stat_value)

			json_dict_str = json.dumps(stats_dict)

			# update db and commit
			cs.execute(f"UPDATE Characters SET Stats = ? WHERE GuildID == {guild_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname.title()}"))
			conn.commit()

			await ctx.send(f"Set {stat_name} to {stat_value} for {char_nickname}.")

			embed = self.embed_stats(guild_id,char_nickname)

			await ctx.send(embed=embed)

	# display the stats. That is all
	@commands.command(name="stats", help="See stats for a character by nickname")
	async def stats(self, ctx, *, char_nickname):

		try:
			embed = self.embed_stats(ctx.guild.id, char_nickname)
			await ctx.send(embed=embed)
		except:
			await ctx.send("That nickname does not exist in this server!")

	# custom roll
	@commands.command(name="rcs", aliases=["rollc", "rollcs"], help="Custom roll")
	async def rollc(self, ctx, *, roll_name):

		cont = True

		# check for character
		try:
			player_id = ctx.message.author.id
			guild_id = ctx.guild.id

			cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

			char_nickname = cs.fetchone()[0]

			cs.execute(f"SELECT CustomRolls FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

			custom_rolls_str = cs.fetchone()[0]
			custom_rolls_dict = json.loads(custom_rolls_str)

		except:
			await ctx.send("You must have a character set up to use this!")
			cont = False

		if (cont):
			try:
				roll_str = custom_rolls_dict[roll_name]
				embed = self.full_roll(ctx, roll_str)

				await ctx.send(embed=embed)

				try:
					await ctx.message.delete()
				except:
					pass

			except:
				pass # Not a command they set

	# set up a custom roll
	@commands.command(name="new_croll", aliases=["ncr", "ncrs"], help="Set up or update a custom die roll. Roll name is highly recommended to be single word.")
	async def new_croll(self, ctx, roll_name, *, roll_str):
		cont = True

		# check for character
		try:
			player_id = ctx.message.author.id
			guild_id = ctx.guild.id

			cs.execute(f"SELECT PlayingAs FROM UserData WHERE GuildID == {guild_id} AND UserID == {player_id} LIMIT 1")

			char_nickname = cs.fetchone()[0]

			cs.execute(f"SELECT CustomRolls FROM Characters WHERE GuildID == {guild_id} AND CharNickname == ? LIMIT 1", (f"{char_nickname.title()}",))

			custom_rolls_str = cs.fetchone()[0]
			custom_rolls_dict = json.loads(custom_rolls_str)

		except:
			await ctx.send("You must have a character set up to use this!")
			cont = False

		if (cont):
			custom_rolls_dict[roll_name] = roll_str

			json_dict_str = json.dumps(custom_rolls_dict)

			# update db and commit
			cs.execute(f"UPDATE Characters SET CustomRolls = ? WHERE GuildID == {guild_id} AND PlayerID == {player_id} AND CharNickname == ?", (f"{json_dict_str}", f"{char_nickname.title()}"))
			conn.commit()

			await ctx.send(f"Set {roll_name} to `{roll_str}` for {char_nickname}.")

			embed = self.embed_custom_rolls(guild_id, char_nickname)

			await ctx.send(embed=embed)

	# display the custom rolls. That is all
	@commands.command(name="crolls", help="See stats for a character by nickname")
	async def crolls(self, ctx, *, char_nickname):

		try:
			embed = self.embed_custom_rolls(ctx.guild.id, char_nickname)
			await ctx.send(embed=embed)
		except:
			await ctx.send("That nickname does not exist in this server!")

def setup(bot):
	bot.add_cog(Dice(bot))
