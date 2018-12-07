import discord
from discord.ext import commands
import re
import random
from .config import *

class Utilities:
	# Comment to test .gitignore
	def __init__(self, bot):
		self.bot = bot

	def single_roll(self, n, m):
		results = []
		result = 0
		for i in range(0, int(n)):
			result = random.randint(1, int(m))
			results.append(result)
		
		return results

	# Dice rolls that are fancier than Tatsu's (though definitely less robust)
	# There has to be a more efficient way to do this, so please send feedback!
	@commands.command(name="roll", aliases=['r'], help="Use standard notation such as 1d4+d6-1")
	async def roll(self, ctx, *, s):
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

		await ctx.send(embed=embed)
		await ctx.message.delete()

	@roll.error
	async def roll_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong! Are you sure you used the right notation? For example:\n`2d6+d4-2`")

	# TODO Archive feature.

	# Private messaging feature
	@commands.command(name="anon_dm", aliases=["anondm", "anon_pm", "anonpm", "adm", "apm"], help="Send an anonymous message from one character to another. The developer is not responsible for the content sent with this. Server administrators are all DM'ed a record of the message.")
	async def anon_dm(self, ctx, recipient_nickname, *, dm):

		# Note, message cannot break limit due to discord's message limit of 2000
		# TODO check that the sender is a player to prevent harassment.

		cont = True

		# First check if AnonDMs are enabled in guild
		cs.execute(f"SELECT AnonDMs from GuildData WHERE GuildID == {ctx.guild.id} LIMIT 1")
		adms_on = cs.fetchone()[0]

		if(adms_on == 0):
			await ctx.send(f"Anon DMs are disabled for {ctx.guild}!")
			cont = False

		#Check that the player can send
		if (cont):
			cs.execute(f"SELECT PlayingAs from UserData WHERE GuildID == {ctx.guild.id} AND UserID == {ctx.message.author.id} LIMIT 1")
			has_char = cs.fetchone()[0] is not None
			
			if(has_char == False):
				await ctx.send("You must be a player to send Anon DMs!")
				cont = False

		# Check that they entered a proper recipient
		if (cont):
			cs.execute(f"SELECT PlayerID, CharName from Characters WHERE GuildID == {ctx.guild.id} AND CharNickname == ? LIMIT 1", (f"{recipient_nickname.title()}",))
			
			sender_name = ctx.message.author
			entry = cs.fetchone()

			try:
				recipient_id = entry[0]
				recipient_name = self.bot.get_user(recipient_id)
				char_name = entry[1]

			except:
				await ctx.send("That is not an available recipient! Use `!lcn` or `!nicknames` to see list.")
				cont = False
		
		# Send message.
		if (cont):

			# Make embed
			color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
			embed = discord.Embed(title=f"{char_name} has received an anonymous message!", color=color, description=dm)
			embed.set_footer(text=f"Disclaimer: The developer is not responsible for the content of these messages. If you have a concern, please contact an administrator of {ctx.guild}. They have been automatically DM'ed a record of this.")
			
			# Send
			recipient = self.bot.get_user(recipient_id)
			await recipient.send(embed=embed)

			await ctx.send("Message sent!")

			# DM record to server administrators.
			admin_embed = discord.Embed(title=f"{sender_name} has sent {recipient_name} an anonymous DM!", color=color, description=dm)
			admin_embed.set_footer(text=f"Disclaimer: The developer is not responsible for the content of these messages. If you have a concern, please contact the sender and recipient.")
			
			guild_members = ctx.guild.members

			for member in guild_members:
				if (member.guild_permissions.administrator):
					await member.send(embed=admin_embed)


	# Sends me feedback.
	@commands.command(name="feedback", help="This bot is still a WIP, and your feedback/suggestions are welcomed. Use this to send the developer a DM. The DM is completely anonymous save for user ID in order to screen for abuse/harassment.")
	async def feedback(self, ctx, *, msg):
		user = self.bot.get_user(367692200030502912)
		await user.send(f"**[FEEDBACK]**\nID: {ctx.message.author.id}\n{msg[0:1950]}")
		await ctx.send("Feedback sent!")

	# Link to README
	@commands.command(name="source", aliases=["readme", "docs", "src"], help="Posts a link to UA's github page.")
	async def source(self, ctx):
		# TODO link here
		await ctx.send("https://github.com/ecatherine13/Ultimate-Assistant/")

def setup(bot):
	bot.add_cog(Utilities(bot))