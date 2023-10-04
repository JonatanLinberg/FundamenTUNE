import os
from interval import Interval

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')

def print_rows(*rows):
	print(*rows, "", sep='\n')

def print_header():
	print_rows(
		"================================================================",
		"==================        FundamenTUNE        ==================",
		"================================================================")

def print_chord(chord):
	if len(chord) == 0:
		print_rows(
			'Write "add <name> <numerator>:<denominator> <fundamental>" to add your first note.',
		    "Ex:",
		    " > add E 3:2")

	for note in chord:
		print(f"[{note}] {chord[note]}")

def print_help():
	print("Available commands:")
	print_rows(
		"[ Add note ]",
		" > add <name> <numerator>:<denominator> <fundamental>")
	print_rows(
		"[ tune notes ]",
		" > tune <name> <frequency>")
	print_rows(
		"[ Print help menu ]",
		" > help")

def not_quit(s):
	s = s.strip()
	return s != "q" and s != "quit"

def parse_instruction(string):
	strings = [ s.strip() for s in string.split(" ") ]
	if len(strings) == 0:
		return None, None
	else:
		return strings[0], strings[1:]

def add_note(chord, name, ratio, fundamental=1):
	numer, denom = [ int(x) for x in ratio.split(":") ]
	if fundamental in chord:
		fundamental = chord[fundamental]
	else:
		fundamental = float(fundamental)

	interval = Interval(numer, denom, fundamental=fundamental)
	if name in chord:
		ans = input(f"{name} already exists in your chord, overwrite? (y/n)")
		if ans == "y":
			chord[name] = interval
		elif ans != "n":
			raise Exception("y/n answer not recognised!")
	else:
		chord[name] = interval

def tune_notes(chord, name, freq):
	chord[name].rescale_to(float(freq))

def main(*args, **kwargs):
	chord = {}
	error = None

	while True:
		clear_screen()
		print_header()		
		print_chord(chord)
		if error is not None:
			print("[ERROR] ", error)
			error = None

		try:
			inp = input(" > ")
		except (EOFError, KeyboardInterrupt):
			clear_screen()
			break
		
		if (not_quit(inp)):
			cmd, args = parse_instruction(inp)
			if cmd is None:
				error = "Could not parse instruction!"

			elif cmd == "add":
				try:
					add_note(chord, *args)
				except Exception as e:
					error = f"Could not add note! ({e})"

			elif cmd == "tune":
				try:
					tune_notes(chord, *args)
				except Exception as e:
					error = f"Could note tune notes! ({e})"

			elif cmd == "help":
				clear_screen()
				print_header()
				print_help()
				input("Press any key to continue...")
			else:
				error = "Command not recognised!"
		
		else:
			clear_screen()
			break