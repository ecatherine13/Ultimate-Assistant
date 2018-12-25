import discord
from discord.ext import commands
from .config import *
import re
import random
import os
import asyncio
import json
import math

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
	async def kg_sim(self, ctx):

		# Returns parsed event string and pops off characters mentioned from char_list. The list is trusted to have characters available for the event. This is for non-death prologue
		def parse_event_prologue(char_list):
			finished = False
			while (not finished):
				event_str = random.choice(self.prologue_events)
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

					return parsed_event_str #, mentioned_chars
					finished = True
				else:
					pass

		def parse_event_dl(char_list):
			finished = False
			while (not finished):
				event_str = random.choice(self.daily_life_events)
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

					return parsed_event_str #, mentioned_chars
					finished = True
				else:
					pass

		# Daily life deaths, no victims/killers/accomplices. Only involve one character at a time
		# Char list only includes eligible characters (traitor and mm cannot die in daily life or prologue)
		def parse_death_event_prologue(char_list, dead_char_list):

			# Make sure char_list isn't empty (no eligible deaths, just exit method and move on)
			if (len(char_list) == 0):
				return None
			else:
				dead_char = char_list.pop()
				dead_char_list.append(dead_char)

				event_str = random.choice(self.prologue_deaths)

				parsed_event_str = event_str

				rep_seg = "<1>"
				parsed_event_str = parsed_event_str.replace(rep_seg, f"**{dead_char}**")
				return parsed_event_str

		def parse_death_event_dl(char_list, dead_char_list):
			# Make sure char_list isn't empty (no eligible deaths, just exit method and move on)
			if (len(char_list) == 0):
				return None
			else:
				dead_char = char_list.pop()
				dead_char_list.append(dead_char)

				event_str = random.choice(self.daily_life_deaths)

				parsed_event_str = event_str

				rep_seg = "<1>"
				parsed_event_str = parsed_event_str.replace(rep_seg, f"**{dead_char}**")
				return parsed_event_str

		def parse_bda(char_list, dead_char_list):
			finished = False

			while (not finished):
				bda, case = random.choice(list(self.bdas_murders.items()))

				# Search bda and case for k, v, a, w
				# killer(s), accomplice(s), victim(s), witness(es). Victim status > Killer status
				regex_k = "\<k([0-9]*)\>"
				regex_a = "\<a([0-9]*)\>"
				regex_v = "\<v([0-9]*)\>"
				regex_w = "\<w([0-9]*)\>"

				k_nums = [int(x) for x in re.findall(regex_k, bda+case)]
				a_nums = [int(x) for x in re.findall(regex_a, bda+case)]
				v_nums = [int(x) for x in re.findall(regex_v, bda+case)]
				w_nums = [int(x) for x in re.findall(regex_w, bda+case)]

				try:
					num_k = max(k_nums)
				except:
					num_k = 0

				try:
					num_a = max(a_nums)
				except:
					num_a = 0

				try:
					num_v = max(v_nums)
				except:
					num_v = 0

				try:
					num_w = max(w_nums)
				except:
					num_w = 0

				total_participants = num_k + num_a + num_v +  num_w

				if (len(char_list) < total_participants):
					continue
				else:
					victims = [char_list.pop() for _ in range(0,num_v)]
					dead_char_list.extend(victims)
					killers = random.sample(char_list, num_k)
					available_w = [x for x in char_list if x not in killers]
					witnesses = random.sample(available_w, num_w)
					available_a = [x for x in char_list if x not in killers and x not in witnesses]
					accomplices = random.sample(available_a, num_a)

					# print(f"V: {victims}\nK: {killers}\nW: {witnesses}\nA: {accomplices}")
					# Replace as needed
					bda_parsed = bda
					case_parsed = case

					# Victims
					for i in range(0, num_v):
						# BDA
						bda_parsed = bda_parsed.replace(f"<v{i+1}>", f"**{victims[i]}**")

						# Case
						case_parsed = case_parsed.replace(f"<v{i+1}>", f"**{victims[i]}**")

					# Killers
					for i in range(0, num_k):
						# BDA
						bda_parsed = bda_parsed.replace(f"<k{i+1}>", f"**{killers[i]}**")

						# Case
						case_parsed = case_parsed.replace(f"<k{i+1}>", f"**{killers[i]}**")

					# Accomplices
					for i in range(0, num_a):
						# BDA
						bda_parsed = bda_parsed.replace(f"<a{i+1}>", f"**{accomplices[i]}**")

						# Case
						case_parsed = case_parsed.replace(f"<a{i+1}>", f"**{accomplices[i]}**")

					# Witnesses
					for i in range(0, num_w):
						# BDA
						bda_parsed = bda_parsed.replace(f"<w{i+1}>", f"**{witnesses[i]}**")

						# Case
						case_parsed = case_parsed.replace(f"<w{i+1}>", f"**{witnesses[i]}**")

					finished = True

					return bda_parsed, case_parsed, victims, killers

		def parse_event_trial(char_list):
			finished = False
			while (not finished):
				event_str = random.choice(self.trial_events)
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

					return parsed_event_str #, mentioned_chars
					finished = True
				else:
					pass

		# Returns arrays reg_chars, mm_chars, t_chars, and the integer n_svr. mm and t can be empty
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

			# Finally, choose number of survivors. Cannot exceed leng(reg_chars)
			n_svr = random.gauss(4, 2)

			if (n_svr <= 0):
				n_svr = 1
			elif (n_svr >= len(reg_chars)):
				n_svr = round(len(reg_chars) / 3)
			else:
				n_svr = round(n_svr)

			return reg_chars, mm_chars, t_chars, n_svr

		def get_headcount(reg_chars, mm_chars, t_chars, reg_dead, mm_dead, t_dead):
			alive_chars = reg_chars + mm_chars + t_chars
			dead_chars = reg_dead + mm_dead + t_dead
			alive_chars.sort()
			dead_chars.sort()

			headcount_str_alive = ", ".join(alive_chars)
			headcount_str_dead = ", ".join(dead_chars)

			headcount_str = f"**Alive**: {headcount_str_alive}\n**Dead**: {headcount_str_dead}"
			return headcount_str

		cont_outer = True
		cs.execute(f"SELECT CharName from Characters WHERE GuildID == {ctx.guild.id}")
		characters = [x[0] for x in cs.fetchall()]

		# await ctx.send("Command not written yet!")
		# cont_outer = False

		n_chars = len(characters)
		# print(f"\n{characters}")
		if(cont_outer and n_chars < 5):
			await ctx.send(f"You need at least 5 characters to play a game!")
			cont_outer = False
		
		# Choose setting and shuffle characters into reg_chars, mm_chars, t_chars,  - Done
		if (cont_outer):
			setting_num = random.randint(0, len(self.setting_choices)-1)
			raw_setting = self.setting_choices[setting_num]
			await ctx.send(raw_setting.replace("{n_chars}", f"**{n_chars}**"))

			# Choose mms and traitors
			reg_chars, mm_chars, t_chars, n_svr = choose_chars(characters)
			reg_dead = []
			mm_dead = []
			t_dead = []
			mm_chars_original = [x for x in mm_chars]
			t_chars_original = [x for x in t_chars]

			print(f"Regular: {reg_chars}\nMM: {mm_chars}\nTraitor: {t_chars}\nNo. Survivors: {n_svr}")

		# Prologue
		if (cont_outer):
			await asyncio.sleep(3)	
			await ctx.send("**__~Prologue Start~__**")
				
			prologue_str = ''
			# Probability of mm, traitor, and regular deaths
			p_mmd = 0
			p_td = 0
			p_rd = 0.01

			# num_unmentioned_chars = len(reg_chars + mm_chars + t_chars)
			unmentioned_chars = reg_chars + mm_chars + t_chars
			random.shuffle(unmentioned_chars)
			while (len(unmentioned_chars) > 0):
				p = random.uniform(0, 1)

				# Normal event
				if (p > p_rd):
					# # Choose event
					# event_str = random.choice(self.prologue_events)
					event_parsed = parse_event_prologue(unmentioned_chars)
					# num_unmentioned_chars -= 1

					prologue_str += f"{event_parsed}\n\n"
					# print(unmentioned_chars)
				else: # death event
					# only regular characters can die in the prologue, pop from reg_chars to reg_dead
					reg_unmentioned = [x for x in unmentioned_chars if x in reg_chars]
					event_parsed = parse_death_event_prologue(reg_unmentioned, reg_dead)

					# Remove dead character from unmentioned_characters

					if (event_parsed != None):
						unmentioned_chars = [x for x in unmentioned_chars if x not in reg_dead]
						reg_chars = [x for x in reg_chars if x not in reg_dead]
						prologue_str += f"{event_parsed}\n\n"

			await asyncio.sleep(3)
			await ctx.send(prologue_str)
			await asyncio.sleep(3)
			await ctx.send("**__~Prologue End~__**")
			await ctx.send(get_headcount(reg_chars, mm_chars, t_chars, reg_dead, mm_dead, t_dead))

		# Chapters until number of survivors is reached
		if (cont_outer):
			mm_won = False
			ch_idx = 1
			while (len(reg_chars) > n_svr):
				await asyncio.sleep(8)
				await ctx.send(f"**__~Ch. {ch_idx} Start~__**")

				# Daily Life
				# Daily life death probability
				p_rd = 0.005 # 0.5% chance

				# Choose how many days it lasts. N(2, 1), m > 0
				daily_life_len = random.gauss(2, 1)
				if (daily_life_len <= 0):
					daily_life_len = 1
				else:
					daily_life_len = round(daily_life_len)

				# Daily Life single day
				for j in range(0, daily_life_len):
					await asyncio.sleep(8)
					await ctx.send(f"**__Day {j+1}__**")

					unmentioned_chars = reg_chars + t_chars + mm_chars
					random.shuffle(unmentioned_chars)
					dl_str = ''

					while (len(unmentioned_chars) > 0):
						p = random.uniform(0, 1)

						# Normal event
						if (p > p_rd):
							# # Choose event
							# event_str = random.choice(self.prologue_events)
							event_parsed = parse_event_dl(unmentioned_chars)
							# num_unmentioned_chars -= 1

							dl_str += f"{event_parsed}\n\n"
							# print(unmentioned_chars)
						else: # death event
							# only regular characters can die in the prologue, pop from reg_chars to reg_dead
							reg_unmentioned = [x for x in unmentioned_chars if x in reg_chars]
							event_parsed = parse_death_event_dl(reg_unmentioned, reg_dead)

							# Remove dead character from unmentioned_characters

							if (event_parsed != None):
								unmentioned_chars = [x for x in unmentioned_chars if x not in reg_dead]
								reg_chars = [x for x in reg_chars if x not in reg_dead]
								dl_str += f"{event_parsed}\n\n"

					# End of a day
					# print(dl_str)
					await ctx.send(dl_str)
					# await asyncio.sleep(1)
				
				# After j days, death!
				# If survivors <= planned number, kill off mm
				if (len(reg_chars) <= n_svr):
					pass
				else:
					# Regular bda
					p_td = 0.05 # small chance of traitor involvement, only applicable if len(t_chars) > 0. Zero until I fix the dead list adjustments

					p = random.uniform(0, 1)

					if (p < p_td and len(t_chars) > 0): # Traitor death
						involved_chars = t_chars + reg_chars
						involved_dead = []
						bda_parsed, case_parsed, victims, killers = parse_bda(involved_chars, involved_dead)

						t_dead = [x for x in t_chars if x in involved_dead]
						reg_dead = [x for x in reg_chars if x in involved_dead]
						t_chars = [x for x in t_chars if x not in t_dead]
						reg_chars = [x for x in reg_chars if x not in reg_dead]

						await asyncio.sleep(8)
						await ctx.send(f"***DING DONG BING BONG***\n{bda_parsed}")

						# Trial events
						unmentioned_chars = mm_chars + t_chars + reg_chars
						random.shuffle(unmentioned_chars)
						trial_str = ''

						while (len(unmentioned_chars) > 0):
							event_parsed = parse_event_trial(unmentioned_chars)

							trial_str += f"{event_parsed}\n\n"

						await asyncio.sleep(4)
						await ctx.send(f"**__~Trial {ch_idx} Start~__**")
						await ctx.send(trial_str)

						# Trial outcome, lower for traitor death
						p_success = 0.75

						p = random.uniform(0, 1)
						await asyncio.sleep(8)
						if (p <= p_success):
							# Choose a CI-er
							ci_er = random.choice(reg_chars)

							await ctx.send(f"**{ci_er}** delivers a CI and reveals the truth!")
							await ctx.send(case_parsed)

							# Kill off killers, may be either regular or traitor
							for killer in killers:
								if (killer in reg_chars):
									reg_dead.append(killer)
								elif (killer in t_chars):
									t_dead.append(killer)

							reg_chars = [x for x in reg_chars if x not in reg_dead]
							t_chars = [x for x in t_chars if x not in t_dead]

						else:
							await ctx.send("No one was able to discover the truth in time!")
							await ctx.send(case_parsed)

							# Regular characters die
							reg_dead.extend(reg_chars)
							reg_chars = []
							mm_won = True
						
					else: # Regular characters only
						bda_parsed, case_parsed, victims, killers = parse_bda(reg_chars, reg_dead)
						await asyncio.sleep(8)
						await ctx.send(f"***DING DONG BING BONG***\n{bda_parsed}")
						# await ctx.send(f"**Case**: {case_parsed}")

						# Trial events
						unmentioned_chars = mm_chars + t_chars + reg_chars
						random.shuffle(unmentioned_chars)
						trial_str = ''

						while (len(unmentioned_chars) > 0):
							event_parsed = parse_event_trial(unmentioned_chars)

							trial_str += f"{event_parsed}\n\n"

						await asyncio.sleep(4)
						await ctx.send(f"**__~Trial {ch_idx} Start~__**")
						await ctx.send(trial_str)

						# Trial outcome
						p_success = 0.95

						p = random.uniform(0, 1)
						await asyncio.sleep(8)
						if (p <= p_success):
							# Choose a CI-er
							ci_er = random.choice(reg_chars + mm_chars + t_chars)

							await ctx.send(f"**{ci_er}** delivers a CI and reveals the truth!")
							await ctx.send(case_parsed)

							reg_dead.extend(killers)
							reg_chars = [x for x in reg_chars if x not in reg_dead]
						else:
							await ctx.send("No one was able to discover the truth in time!")
							await ctx.send(case_parsed)
							reg_dead.extend(reg_chars)
							reg_chars = []
							mm_won = True
							break

				# End of chapter
				await ctx.send(f"**__~Ch. {ch_idx} End~__**")
				await ctx.send(get_headcount(reg_chars, mm_chars, t_chars, reg_dead, mm_dead, t_dead))
				ch_idx += 1

			# Final chapter (mm death), or decide win or lose
			if (mm_won): # Lost trial
				await ctx.send("Sadly for everyone, the truth slipped away and the mastermind(s) won...")
			elif (len(mm_chars) > 0): # Reveal mm in one last trial
				involved_chars = mm_chars + reg_chars
				involved_dead = []
				bda_parsed, case_parsed, victims, killers = parse_bda(involved_chars, involved_dead)

				mm_dead = [x for x in mm_chars if x in victims]
				reg_dead.extend([x for x in reg_chars if x in victims])
				mm_chars = [x for x in mm_chars if x not in t_dead]
				reg_chars = [x for x in reg_chars if x not in reg_dead]

				await asyncio.sleep(8)
				await ctx.send(f"***DING DONG BING BONG***\n{bda_parsed}")

				# Trial events
				unmentioned_chars = mm_chars + t_chars + reg_chars
				random.shuffle(unmentioned_chars)
				trial_str = ''

				while (len(unmentioned_chars) > 0):
					event_parsed = parse_event_trial(unmentioned_chars)

					trial_str += f"{event_parsed}\n\n"

				await asyncio.sleep(4)
				await ctx.send(f"**__~Trial {ch_idx} Start~__**")
				await ctx.send(trial_str)

				await asyncio.sleep(8)
				revealer = random.choice(reg_chars)
				await ctx.send(f"In a final showdown, **{revealer}** discovers the truth behind the killing game...")
				mm_dead.extend(mm_chars)
				mm_chars = []
			else: # No mms
				await asyncio.sleep(8)
				revealer = random.choice(reg_chars)
				await ctx.send(f"In a final showdown, **{revealer}** discovers the truth behind the killing game...")

			await asyncio.sleep(2)
			await ctx.send("**__~Game end!~__**")

			survivors = reg_chars + t_chars + mm_chars
			deaths = mm_dead + t_dead + reg_dead

			if (len(mm_chars_original) == 0):
				mm_chars_original = ["The friends they made along the way"]

			if (len(t_chars_original) == 0):
				t_chars_original = ["Their own mutual distrust"]

			survivors_str = ", ".join(survivors)
			mm_str = ", ".join(mm_chars_original)
			traitor_str = ", ".join(t_chars_original)
			dead_str = ", ".join(deaths)

			await ctx.send(f"**Mastermind(s)**: {mm_str}\n\n**Traitor(s)**: {traitor_str}\n\n**Dead**: {dead_str}\n\n**Survivor(s)**: {survivors_str}")

	

def setup(bot):
	bot.add_cog(Memes(bot))