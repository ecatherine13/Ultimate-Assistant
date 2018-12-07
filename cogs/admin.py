import discord
from discord.ext import commands
from .config import *
import re
import random

class Admin:
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name="set_autorole", aliases=["set_ar", "setar", "sar", "ar"], help="Set a role to automatically assign new members. Leave blank for a list of options. Optional role argument (pings the role!) Discord does not allow any user to assign roles higher than their own.")
	@commands.has_permissions(administrator=True)
	async def set_autorole(self, ctx, *, role=None):
		guild = ctx.message.guild

		if (role == None):

			# For checking input author
			def pred(msg):
				return msg.author == ctx.message.author and msg.channel == ctx.message.channel

			guild_roles = guild.roles

			color = int("%06x" % random.randint(0, 0xFFFFFF), 16)

			embed = discord.Embed(title=f"Available roles for {guild.name}", color=color)
			embed_str = ''

			# Only display roles lower than bot's highest role

			bot_member= discord.utils.get(guild.members, id=self.bot.user.id)
			bot_highest_role = bot_member.roles[-1]

			# await ctx.send(bot_highest_role_id)

			i = 1
			for role in guild_roles[1:len(guild_roles)]: # excludes @everyone
				if(role < bot_highest_role):
					embed_str = embed_str + f"[{i}] {role.name}\n"
					i += 1
			if (embed_str != ''):
				embed.add_field(name="Enter a number to set auto role (enter 0 for @everyone):", value=embed_str)
				await ctx.send(embed=embed)

				role_idx = await self.bot.wait_for('message', check=pred, timeout=60)
				try:
					role_id = guild_roles[int(role_idx.content)].id
					cs.execute(f"UPDATE GuildData SET AutoRole = {role_id} WHERE GuildID = {guild.id}")
					conn.commit()
					await ctx.send(f"Set Auto Role to {guild_roles[int(role_idx.content)].name}")
				except:
					await ctx.send("Not a valid input!")
			
			else:
				await ctx.send("Bot needs a role to use this command!")

		else:
			regex = "<@&?([0-9]{18})>"

			role_id_str = re.findall(regex, role)
			
			cs.execute(f"UPDATE GuildData SET AutoRole = {int(role_id_str[0])} WHERE GuildID = {guild.id}")
			conn.commit()

			await ctx.send(f"Set Auto Role to {role}")

	@set_autorole.error
	async def set_autorole_error(self, ctx, error):
		if isinstance(error, commands.CommandInvokeError):
			await ctx.send("Something went wrong! Did you enter a valid role? To input directly, ping the role.")

	# TODO Command to reset auto role to None

	# Set time zone. Used for Automated Announcements
	@commands.command(name="set_timezone", aliases=["tz", "timezone", "settimezone"], help="Set server timezone in UTC format. Used to automate announcements. Default is UTC+0")
	@commands.has_permissions(administrator=True)
	async def set_timezone(self, ctx, *, new_timezone=None):
		def pred(msg):
			return msg.author == ctx.message.author and msg.channel == ctx.message.channel

		guild_id = ctx.guild.id
		
		# Get current timezone
		cs.execute(f"SELECT Timezone FROM GuildData WHERE GuildID == {guild_id} LIMIT 1")

		guild_entry = cs.fetchone()
		current_timezone = guild_entry[0]

		if (new_timezone == None):
			if(current_timezone < 0):
				await ctx.send(f"Current timezone for {ctx.guild} is **UTC{current_timezone}**. \nEnter a new number (ex. 1, -5, +3)")
			else:
				await ctx.send(f"Current timezone for {ctx.guild} is **UTC+{current_timezone}**. \nEnter a new number (ex. 1, -5, +3)")

			new_timezone = await self.bot.wait_for('message', check=pred, timeout=60)
			new_timezone = new_timezone.content

		# Check new_timezone validity
		try:
			new_timezone = int(new_timezone)

			# Timezones can only go from UTC-12 to UTC+14
			if (new_timezone < -12 or 14 < new_timezone):
				await ctx.send("You must enter a number between -12 and +14. Please try again.")
			
			else:
				# Set in DB
				cs.execute(f"UPDATE GuildData SET Timezone = {new_timezone} WHERE GuildID == {ctx.guild.id}")
				conn.commit()

				# TODO adjust Announcements for new timezone?

				await ctx.send(f"Set timezone for {ctx.guild}!")

		except:
			await ctx.send("That is not a valid number!")
	
	# Toggle anon dms
	@commands.command(name="toggle_adm", help="Toggle the anonymous DM feature. By default, it's set to OFF.")
	@commands.has_permissions(administrator=True)
	async def toggle_adm(self, ctx):
		cs.execute(f"SELECT AnonDMs FROM GuildData WHERE GuildID == {ctx.guild.id} LIMIT 1")

		adms_on = cs.fetchone()[0]

		if (adms_on == 0):
			adms_on = 1
			await ctx.send("Anon DMs are now **enabled**.")
		else:
			adms_on = 0
			await ctx.send("Anon DMs are now **disabled**.")

		cs.execute(f"UPDATE GuildData SET AnonDMs = {adms_on} WHERE GuildID == {ctx.guild.id} LIMIT 1")
		conn.commit()



def setup(bot):
	bot.add_cog(Admin(bot))