import discord
from discord.ext import commands
import re
import random
from .config import *

class Utilities:
	# Comment to test .gitignore
	def __init__(self, bot):
		self.bot = bot

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

			try:
				await recipient.send(embed=embed)
			except:
				await ctx.send("I am unable to send a DM to that person! They may only accept DMs from friends, or have me blocked.")
				cont = False

		if (cont):
			await ctx.send("Message sent!")

			# DM record to server administrators.
			admin_embed = discord.Embed(title=f"{sender_name} has sent {recipient_name} an anonymous DM!", color=color, description=dm)
			admin_embed.set_footer(text=f"Disclaimer: The developer is not responsible for the content of these messages. If you have a concern, please contact the sender and recipient.")
			
			guild_members = ctx.guild.members

			for member in guild_members:
				if (member.guild_permissions.administrator):

					try:
						await member.send(embed=admin_embed)
					except:
						await ctx.send(f"Unable to DM admin member {member.display_name}!")

	# Sends me feedback.
	@commands.command(name="feedback", help="This bot is still a WIP, and your feedback/suggestions are welcomed. Use this to send the developer a DM. The DM is completely anonymous save for user ID in order to screen for abuse/harassment.")
	async def feedback(self, ctx, *, msg):
		user = self.bot.get_user(367692200030502912)
		await user.send(f"**[FEEDBACK]**\nID: {ctx.message.author.id}\n{msg[0:1950]}\n--------------------------------------------")
		await ctx.send("Feedback sent!")

	# Link to README
	@commands.command(name="source", aliases=["readme", "docs", "src"], help="Posts a link to UA's github page.")
	async def source(self, ctx):
		# TODO link here
		await ctx.send("https://github.com/ecatherine13/Ultimate-Assistant/")

def setup(bot):
	bot.add_cog(Utilities(bot))