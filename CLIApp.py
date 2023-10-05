import os
from interval import Interval


##################################
#   Print functions
##################################
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
		    " > add E 5:4")

	for note in chord:
		print(f"[{note}] {chord[note]}")


def print_help():
	print("Available commands:")
	print_rows(
		"[ Add note ]",
		" > add <name> <numerator>:<denominator> <fundamental>")
	print_rows(
		"[ Copy note ]",
		" > copy <name> <new note>")
	print_rows(
		"[ Rename note ]",
		" > name <note> <new name>")
	print_rows(
		"[ Delete note ]",
		" > del <name>")
	print_rows(
		"[ Tune notes ]",
		" > tune <name> <frequency>")
	print_rows(
		"[ Print help menu ]",
		" > help")


##################################
#   Input Parsers
##################################
def not_quit(s):
	s = s.strip()
	return s != "q" and s != "quit"


def parse_instruction(string):
	strings = [ s.strip() for s in string.split(" ") ]
	if len(strings) == 0:
		return None, None
	else:
		return strings[0], strings[1:]


def get_yes_no(s):
	out = str(s) + " (y/n)"
	ans = input(out)
	if ans == "y":
		return true
	elif ans == "n":
		return false
	else:
		raise Exception("y/n answer not recognised!")


##################################
#   Command handlers
##################################
def add_note(chord, name, ratio, fundamental=None):
	numer, denom = [ int(x) for x in ratio.split(":") ]
	if fundamental in chord:
		fundamental = chord[fundamental]
	else:
		fundamental = float(fundamental)

	interval = Interval(numer, denom, fundamental=fundamental)
	if name not in chord or \
	   get_yes_no(f"{name} already exists in your chord, overwrite?"):
		chord[name] = interval


def del_note(chord, name):
	if name not in chord:
		raise Exception(f'Cannot find note "{name}"')
	del chord[name]


def tune_notes(chord, name, freq):
	chord[name].rescale_to(float(freq))


def name_note(chord, name, new_name):
	if name not in chord:
		raise Exception(f'Cannot find note "{name}"')
	chord[new_name] = chord.pop(name)


def copy_note(chord, name, new_note):
	if name not in chord:
		raise Exception(f'Cannot find note "{name}"')
	chord[new_name] = chord[name].copy()

##################################
#   MAIN
##################################
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

			elif cmd == "del":
				try:
					del_note(chord, *args)
				except Exception as e:
					error = f"Could not delete note! ({e})"

			elif cmd == "copy":
				try:
					copy_note(chord, *args)
				except Exception as e:
					error = f"Could not copy note! ({e})"

			elif cmd == "name":
				try:
					name_note(chord, *args)
				except Exception as e:
					error = f"Could not rename note! ({e})"

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