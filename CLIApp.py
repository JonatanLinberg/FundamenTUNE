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


def print_chord(chord, sort=True):
	if sort:
		chord = dict(sorted(chord.items(), key=lambda item: item[1].frequency))
	if len(chord) == 0:
		print_rows(
			'Write "add <name> <numerator>:<denominator> <fundamental>" to add your first note.',
		    "Ex:",
		    " > add E 5:4")
	else:
		for note in chord:
			print(f"[{note}] {chord[note]}")
		print()

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
		" > tune <name> <frequency>",
		"or",
		" > tune <name> <fundamental> <delta ratio>")
	print_rows(
		"[ Base notes ]",
		" > base <name> <new fundamental>")
	print_rows(
		"[ Downsample interval ]",
		" > crush <name> <max resolution>")
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
	strings = [ s.strip() for s in string.strip().split(" ") ]
	if len(strings) == 0:
		return None, None
	else:
		return strings[0], strings[1:]


def parse_arg(chord, s):
	if s in chord:
		return chord[s]
	else:
		return float(s)


def parse_dense_expression(expression, ops):
	for op in ops:
		if op in expression:
			a, b = expression.split(op)
			return a, op, b


def get_yes_no(s):
	out = str(s) + " (y/n): "
	ans = input(out)
	if ans == "y":
		return True
	elif ans == "n":
		return False
	else:
		raise Exception("y/n answer not recognised!")


##################################
#   Helper functions
##################################
def add_note(chord, name, interval):
	if name not in chord or \
	   get_yes_no(f"{name} already exists in your chord, overwrite?"):
		chord[name] = interval

def check_exists(chord, name):
	if name not in chord:
		raise Exception(f'Cannot find note "{name}"')

##################################
#   Command handlers
##################################
def cmd_add(chord, name, ratio=None, fundamental=None):
	try:
		numer, denom = [ int(x) for x in ratio.split(":") ]
	except ValueError: # probably freq
		numer = denom = 1
		if fundamental is None:
			try:
				fundamental = float(ratio)
			except ValueError:
				raise Exception(f"Could not parse arguments: (ratio: {ratio}, fundamental: {fundamental})")
	except AttributeError: # no ratio or fundamental
		numer = denom = 1
	
	if fundamental is None:
		fundamental = 1
	if fundamental in chord:
		fundamental = chord[fundamental]
	else:
		fundamental = float(fundamental)

	interval = Interval(numer, denom, fundamental=fundamental)
	add_note(chord, name, interval)


def cmd_del(chord, name):
	check_exists(chord, name)
	del chord[name]


def cmd_tune(chord, name, ref, d_ratio="1:1"):
	try:
		n, d = [int(a) for a in d_ratio.split(':')]
	except:
		raise Exception(f'Ratio {d_ratio} could not be parsed.')

	check_exists(chord, name)
	try:
		check_exists(chord, ref)
		freq = chord[ref].frequency * n / d
		chord[name].rescale_to(float(freq))
	except Exception:
		chord[name].rescale_to(float(ref))


def cmd_name(chord, name, new_name):
	check_exists(chord, name)
	chord[new_name] = chord.pop(name)


def cmd_copy(chord, name, new_note):
	check_exists(chord, name)
	chord[new_name] = chord[name].copy()


def cmd_base(chord, name, base):
	check_exists(chord, name)
	try: 
		check_exists(chord, base)
		chord[name].fundamental = chord[base]
	except Exception:
		chord[name].fundamental = float(base)


def cmd_calc(chord, name, *expression):
	if len(expression) == 1:
		ops = ("**", "*", "/")
		expression = parse_dense_expression(expression[0], ops)
	
	if len(expression) != 3:
		raise Exception("Only binary expressions are supported at this time")

	op = expression[1]
	a = parse_arg(chord, expression[0])
	b = parse_arg(chord, expression[2])

	if op == "*":
		interval = a*b
	elif op == "/":
		interval = a/b
	elif op == "**":
		interval = a**b
	else:
		raise Exception(f"{op} is not a valid operator")

	add_note(chord, name, interval)

def cmd_crush(chord, name, max_depth=None):
	check_exists(chord, name)
	if max_depth is not None:
		max_depth = int(max_depth)

	chord[name] = chord.pop(name).reduce_closest(max_depth=max_depth)[0]



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
			cmd = cmd.lower()
			if cmd is None:
				error = "Could not parse instruction!"

			elif cmd == "add":
				try:
					cmd_add(chord, *args)
				except Exception as e:
					error = f"Could not add note! ({e})"

			elif cmd == "del":
				try:
					cmd_del(chord, *args)
				except Exception as e:
					error = f"Could not delete note! ({e})"

			elif cmd == "copy":
				try:
					cmd_copy(chord, *args)
				except Exception as e:
					error = f"Could not copy note! ({e})"

			elif cmd == "name":
				try:
					cmd_name(chord, *args)
				except Exception as e:
					error = f"Could not rename note! ({e})"

			elif cmd == "tune":
				try:
					cmd_tune(chord, *args)
				except Exception as e:
					error = f"Could not tune notes! ({e})"

			elif cmd == "base":
				try:
					cmd_base(chord, *args)
				except Exception as e:
					error = f"Could not rebase note! ({e})"

			elif cmd == "calc":
				try:
					cmd_calc(chord, *args)
				except Exception as e:
					error = f"Could not calc note! ({e})"

			elif cmd == "crush":
				try:
					cmd_crush(chord, *args)
				except Exception as e:
					error = f"Could not crush note! ({e})"

			elif cmd == "help":
				clear_screen()
				print_header()
				print_help()
				input("Press Enter to continue...")
			else:
				error = "Command not recognised!"
		
		else:
			clear_screen()
			break