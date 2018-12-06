import discord
from discord.ext import commands
from .config import *
import re
import random
import os
import asyncio
import json

class Memes:
	def __init__(self, bot):
		self.bot = bot

		# KG sim
		THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

		with open(os.path.join(THIS_FOLDER, 'kg', 'settings.txt')) as fh:
			self.setting_choices = [x.strip() for x in fh.readlines()]

		with open(os.path.join(THIS_FOLDER, 'kg', 'prologue_events.txt')) as fh:
			self.prologue_events = [x.strip() for x in fh.readlines()]

		with open(os.path.join(THIS_FOLDER, 'kg', 'prologue_deaths.txt')) as fh:
			self.prologue_deaths = [x.strip() for x in fh.readlines()]

		with open(os.path.join(THIS_FOLDER, 'kg', 'daily_life_events.txt')) as fh:
			self.daily_life_events = [x.strip() for x in fh.readlines()]

		with open(os.path.join(THIS_FOLDER, 'kg', 'daily_life_deaths.txt')) as fh:
			self.daily_life_deaths = [x.strip() for x in fh.readlines()]

		# Special case, this is a JSON string
		with open(os.path.join(THIS_FOLDER, 'kg', 'bdas_murders.txt')) as fh:
			self.bdas_murders = fh.read().replace("\n", "")
			self.bdas_murders = json.loads(self.bdas_murders)

		with open(os.path.join(THIS_FOLDER, 'kg', 'trial_events.txt')) as fh:
			self.trial_events = [x.strip() for x in fh.readlines()]


	# Hunger Games :deflate:"
	@commands.command(name="kg_sim", aliases=["kg"], help="Randomized KG sim a la Hunger Games Sim")
	async def hunger_games(self, ctx):

		# Display headcount. Returns
		# Alive (n_alive): Alive chars
		# Dead (n_dead): Dead chars
		async def display_headcount(ctx, alive_chars, dead_chars, mm_chars, t_chars):
			try:
				dead_chars = [x for sublist in dead_chars for x in sublist]
				dead_chars_str = ", ".join(dead_chars)
	
				alive_chars = [x for x in alive_chars if x not in dead_chars]
				alive_chars_str = ", ".join(alive_chars)
			except:
				dead_chars_str = "None!"

			if (set(mm_chars).issubset(set(dead_chars)) and set(t_chars).issubset(set(dead_chars))):
				mm_str = ", ".join(mm_chars)
				t_str = ", ".join(t_chars)
				await ctx.send(f"The Mastermind(s) and Traitor(s) are dead!\nMasterminds: {mm_str}\nTraitors: {t_str}")

			return f"**{len(dead_chars)} Dead**: {dead_chars_str}\n**{len(alive_chars)} Alive**: {alive_chars_str}"

		# Returns parsed event string and pops off characters mentioned from char_list. The list is trusted to have characters available for the event.
		def parse_event(event_str, char_list):
			
			cont = True

			# Find instances of "{[0-9]*}"
			regex = "\<([0-9]*)\>"
			numbers_in_event = [int(x) for x in re.findall(regex, event_str)]
			# numbers_in_event.sort() # Sort by value

			num_chars_mentioned = max(numbers_in_event)
			
			# Pop them off the list and add them in accordingly. If there are too many mentioned characters, jump out of method.
			if (len(char_list) < num_chars_mentioned):
				cont = False
			else:
				mentioned_chars = [char_list.pop() for _ in range(0,num_chars_mentioned)]
			
			if (cont):
				parsed_event_str = event_str
				# Replace the string instances
				for i in numbers_in_event:
					rep_seg = f"<{i}>"
					parsed_event_str = parsed_event_str.replace(rep_seg, f"**{mentioned_chars[i-1]}**")

				return parse_event_str, mentioned_chars
			else:
				return None
			
		def parse_event_death(event_str, alive_char_list, dead_char_list, mm_char_list, t_char_list):

			# 2% chance of t death
			# 1% chance of mm death

			cont = True

			# killer(s), accomplice(s), victim(s), witness(es). Victim status > Killer status
			regex_k = "\<k([0-9]*)\>"
			regex_a = "\<a([0-9]*)\>"
			regex_v = "\<v([0-9]*)\>"
			regex_w = "\<w([0-9]*)\>"

			k_nums = [int(x) for x in re.findall(regex_k, event_str)]
			a_nums = [int(x) for x in re.findall(regex_a, event_str)]
			v_nums = [int(x) for x in re.findall(regex_v, event_str)]
			w_nums = [int(x) for x in re.findall(regex_w, event_str)]

			num_k = max(k_nums)
			num_a = max(a_nums)
			num_v = max(v_nums)
			num_w = max(w_nums)

			total_participants = num_k + num_a + num_v +  num_w

			if (len(alive_chars) < total_participants):
				cont = False
			else:
				rem_v = num_v
				#Check traitor death
				p_t = random.uniform(0, 1)
				p_mm = random.uniform(0, 1)
				if (p_t < 0.02 and ("Their Own Mutual Distrust" not in t_char_list)): # traitor death
					t_victim = t_char_list.pop()
					rem_v = num_v-1
				elif (p_mm < 0.01 and ("The Friends They Made Along the Way" not in mm_char_list)):
					mm_victim = mm_char_list.pop()
					rem_v = num_v-1
				else:
					# eligible victims are alive chars that aren't mm or t
					eligible_victims = [x for x in alive_char_list if x not in mm_chars]
					eligible_victims = [x for x in eligible_victims if x not in t_chars]

				victims = [alive_char_list.pop() for _ in range(0,rem_v)]
				dead_char_list.append(victims)



			return 0

		async def daily_life_day(ctx, alive_chars, dead_chars, mm_chars, t_chars):
			unmentioned_chars = [x for x in alive_chars]
			random.shuffle(unmentioned_chars)

			embeds = []
			while (len(unmentioned_chars) > 0):
				# 2% chance of death
				p = random.uniform(0, 1)
				if (p < 0.02): # Death event. Cannot happen to mms in Daily Life.
					possible_deaths = [x for x in unmentioned_chars if x not in mm_chars]
					event = random.choice(self.daily_life_deaths)
					event_parsed_info = parse_event(event, possible_deaths)
					try:
						newly_dead = event_parsed_info[0]
						dead_chars.append(newly_dead)
						unmentioned_chars = [x for x in unmentioned_chars if x not in newly_dead]
						alive_chars = [x for x in alive_chars if x not in newly_dead]
						event_parsed = event_parsed_info[1]

						try:
							color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
							embed = discord.Embed(title=event_parsed, color=color)
							embeds.append(embed)
						except:
							continue
					except:
						pass
				else: # Normal event
					event = random.choice(self.daily_life_events)
					try:
						event_parsed = parse_event(event, unmentioned_chars)[1]

						try:
							color = int("%06x" % random.randint(0, 0xFFFFFF), 16)
							embed = discord.Embed(title=event_parsed, color=color)
							embeds.append(embed)
						except:
							continue
					except:
						continue

			# Display
				
			for embed in embeds:
				await ctx.send(embed=embed)

			return alive_chars
		
		def choose_chars(all_chars_list):
			# shuffle characters so they can just be popped
			random.shuffle(all_chars_list)

			# Decide number of mms
			cont_mm = True
			n_mm = 0
			if (random.uniform(0, 1) > 0.05): # 5% chance of no MM
				n_mm = 1
			else:
				cont_mm = False

			# Choose additional mm's with decreasing probability 0.25 -> p/5
			p_mm = 0.25
			while (cont_mm):
				if (random.uniform(0, 1) < p_mm):
					n_mm += 1
					p_mm = p_mm/5
				else:
					cont_mm = False

			# Decide number of traitors
			cont_t = True
			n_t = 0
			if (random.uniform(0, 1) > 0.1): # 10% chance of no traitor
				n_t = 1
			else:
				cont_t = False

			# Choose additional t's with decreasing probability 0.33 -> p/3
			p_t = 0.333
			while (cont_t):
				if (random.uniform(0, 1) < p_t):
					n_t += 1
					p_t = p_t/3
				else:
					cont_t = False

			# Using n_mm and n_t, make lists reg_chars, mm_chars, t_chars
			if (len(all_chars_list) < n_mm):
				n_mm = len(all_chars_list)
			mm_chars = [all_chars_list.pop() for _ in range(0, n_mm)]
			
			if (len(all_chars_list) < n_t):
				n_t = len(all_chars_list)
			t_chars = [all_chars_list.pop() for _ in range(0, n_t)]
			
			reg_chars = all_chars_list

			return reg_chars, mm_chars, t_chars

		def headcount_str(reg_chars, mm_chars, t_chars, reg_alive, mm_alive, t_alive):
			alive_chars = reg_alive + mm_alive + t_alive
			reg_dead = [x for x in reg_chars if x not in reg_alive]
			mm_dead = [x for x in mm_chars if x not in mm_alive]
			t_dead = [x for x in t_chars if x not in t_alive]
			dead_chars = reg_dead + mm_dead + t_dead

			# Display in alphabetical order
			alive_str = ", ".join(alive_chars.sort())
			dead_str = ", ".join(dead_chars.sort())

			return f"**Alive**: {alive_str}\n**Dead**: {dead_str}"

		def get_headcount(reg_chars, mm_chars, t_chars, reg_is_alive, mm_is_alive, t_is_alive):
			all_chars = reg_chars + mm_chars + t_chars
			all_alive = reg_is_alive + mm_is_alive + t_is_alive

			alive_chars = [x for x, y in zip(all_chars, all_alive) if y==1]
			dead_chars = [x for x, y in zip(all_chars, all_alive) if y==0]

			return alive_chars, dead_chars

		cont_outer = True
		cs.execute(f"SELECT CharName from Characters WHERE GuildID == {ctx.guild.id}")
		characters = [x[0] for x in cs.fetchall()]

		await ctx.send("Command not written yet!")
		cont_outer = False

		n_chars = len(characters)
		# print(f"\n{characters}")
		if(n_chars < 2):
			await ctx.send(f"You need at least 2 characters to play a game!")
			cont_outer = False
		
		# Choose setting
		if (cont_outer):
			setting_num = random.randint(0, len(self.setting_choices)-1)
			raw_setting = self.setting_choices[setting_num]
			await ctx.send(raw_setting.replace("{n_chars}", str(n_chars)))

			# Choose mms and traitors
			reg_chars, mm_chars, t_chars = choose_chars(characters)
			reg_alive = [x for x in reg_chars]
			mm_alive = [x for x in mm_chars]
			t_alive = [x for x in t_chars]

		# Prologue
		if (cont_outer):	
			await ctx.send("**__~Prologue Start~__**")
			
			# Probability of mm, traitor, and regular deaths
			p_mmd = 0
			p_td = 0
			p_rd = 0.02

			alive_chars, dead_chars = get_headcount(reg_chars, mm_chars, t_chars, reg_alive, mm_alive, t_alive)

			unmentioned_chars = random.shuffle([x for x in alive_chars])

			while (len(unmentioned_chars) > 0):
				# Choose an event.
				if (random.uniform(0, 1) > p_rd): #Normal event
					event_str = random.choice(self.prologue_events)
					event_str_parsed, mentioned_chars = parse_event(event_str, unmentioned_chars)

					unmentioned_chars = [x for x in unmentioned_chars if x not in mentioned_chars]

					await ctx.send(embed=discord.Embed(title=event_str_parsed, color=int("%06x" % random.randint(0, 0xFFFFFF), 16)))

				else: #Death event 
					event_str = random.choice(self.prologue_deaths)
					possible_deaths = [x for x in unmentioned_chars if x not in mm_chars]
					possible_deaths = [x for x in possible_deaths if x not in t_chars]

					event_str_parsed, mentioned_chars = parse_event(event_str, possible_deaths)

					unmentioned_chars = [x for x in unmentioned_chars if x not in mentioned_chars]
					
					await ctx.send


def setup(bot):
	bot.add_cog(Memes(bot))