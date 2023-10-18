from math import log, gcd, ceil
from misc import SortedList

# Calculates equal temperament tuning of n semitones
def equal_temp(n, base = 12):
	return 2**(n / base)

# calculates cent difference between two frequencies
def cent_diff(a, b):
	return log(a/b, 2) * 1200

def is_int(a):
	return int(a) == a

class Interval():
	_NOTE_NAMES = [
		"Perfect Prime",
		"Minor Second",
		"Major Second",
		"Minor Third",
		"Major Third",
		"Perfect Fourth",
		"Tritone",
		"Perfect Fifth",
		"Minor Sixth",
		"Major Sixth",
		"Minor Seventh",
		"Major Seventh",
	]
	_NOTE_ABBR = [
		"P1",
		"m2",
		"M2",
		"m3",
		"M3",
		"P4",
		"TT",
		"P5",
		"m6",
		"M6",
		"m7",
		"M7",
	]

	@staticmethod
	def normalise(numer, denom, in_octave=True):
		while in_octave and (numer / denom < 1):
			denom /= 2
		while in_octave and (numer / denom >= 2):
			denom *= 2

		while not (is_int(numer) and is_int(denom)):
			numer *= 2
			denom *= 2
		numer = int(numer)
		denom = int(denom)
		cd = gcd(numer, denom)
		return numer//cd, denom//cd

	def __init__(self, numer, denom, fundamental=None, in_octave=False):
		if numer <= 0 or denom <= 0:
			raise Exception(f"Invalid interval ratio: {numer}:{denom}")
		self.numer, self.denom = Interval.normalise(numer, denom, in_octave=in_octave)
		self.fundamental = fundamental

		# calc closest eqtt interval
		n_norm, d_norm = Interval.normalise(numer, denom)
		frac = n_norm / d_norm
		dist = 100
		for i in range(12):
			d = abs(cent_diff(frac, equal_temp(i)))
			if d < dist:
				dist = d
				self.note_i = i
		# check P8 as P1
		frac /= 2
		d = abs(cent_diff(frac, equal_temp(0)))
		if d < dist:
			self.note_i = 0

	@property
	def fraction(self):
		return self.numer / self.denom

	@property
	def note_name(self):
		return Interval._NOTE_NAMES[self.note_i]

	@property
	def note_abbr(self):
		return Interval._NOTE_ABBR[self.note_i]

	@property
	def closest_eqtt(self):
		return equal_temp(self.note_i)

	@property
	def cents_off(self):
		d = cent_diff(self.normalised().fraction, self.closest_eqtt)
		if d > 50:
			return (d % 100) - 100
		return d

	@property
	def cents_off_piano(self):
		d = cent_diff(self.frequency, 440)
		d = d % 100
		if d > 50:
			d -= 100
		return d

	@property
	def frequency(self):
		if (self.fundamental is None):
			return self.fraction
		try: 
			# fundamental is interval
			return self.fraction * self.fundamental.frequency
		except AttributeError:
			# fundamental is frequency
			return self.fraction * self.fundamental

	def rescale_to(self, frequency):
		new_fundamental = (frequency * self.denom) / self.numer
		try:
			self.fundamental.rescale_to(new_fundamental)
		except AttributeError:
			self.fundamental = new_fundamental

	def reduce_closest(self, max_depth=None, n=1):
		closest = SortedList(n, key=lambda x: abs(x.fraction - self.fraction))

		if max_depth is not None:
			max_depth = min(max_depth, self.denom-1)
		else:
			max_depth = self.denom-1

		for i in range(max_depth, 0, -1):
			x = ceil(self.fraction * i) # always round up to avoid 0/i
			if closest.push(Interval(x, i, fundamental=self.fundamental)):
				offset = 0
				while True:
					offset += 1
					add_over = closest.push(Interval(x + offset, i, fundamental=self.fundamental))
					add_under = closest.push(Interval(max(x - offset, 1), i, fundamental=self.fundamental))
					if not add_over and not add_under:
						break
		if closest:
			return closest
		else:
			return [self.copy()]


	def copy(self):
		return Interval(self.numer, self.denom, fundamental=self.fundamental)

	def normalised(self):
		return Interval(*Interval.normalise(self.numer, self.denom), fundamental=self.fundamental)

	# difference in cents
	def __sub__(self, other):
		if isinstance(other, Interval):
			return cent_diff(self.fraction, other.fraction)
		else:
			return cent_diff(self.fraction, other)

	# "musically" added intervals, i.e. M3 * P5 == M7
	# if other is number, multiply frequency
	def __mul__(self, other):
		if isinstance(other, Interval):
			return Interval(self.numer * other.numer, self.denom * other.denom, fundamental=self.fundamental)
		else:
			return Interval(self.numer * float(other), self.denom, fundamental=self.fundamental)
	__rmul__ = __mul__

	def __pow__(self, other):
		try:
			other = int(other)
		except:
			raise ValueError(f"{other} cannot be converted to an integer")
		I_n = self.copy()
		for i in range(other-1):
			I_n *= self
		return I_n

	def __truediv__(self, other):
		if isinstance(other, Interval):
			return Interval(self.frequency, other.frequency, fundamental=other)
		else:
			return Interval(self.numer / float(other), self.denom, fundamental=self.fundamental)

	def __str__(self):
		return f"[{self.numer}:{self.denom}][{self.frequency:.2f} Hz] ({self.note_abbr} {self.cents_off:+.1f} cents | {self.cents_off_piano:+.1f} cents off piano)"

	def __repr__(self):
		return f"<class Interval: {self.__str__()}>"