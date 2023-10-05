from math import log, gcd

# Calculates equal temperament tuning of n semitones
def equal_temp(n):
	return 2**(n / 12)

# calculates cent difference between two notes
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
	# fractions of (12-tone) equal temperament intervals
	_NOTE_EQTT = [ equal_temp(i) for i in range(12) ]

	@staticmethod
	def normalise(numer, denom):
		while (numer / denom < 1):
			denom /= 2
		while (numer / denom >= 2):
			denom *= 2
		while not (is_int(numer) and is_int(denom)):
			numer *= 2
			denom *= 2
		numer = int(numer)
		denom = int(denom)
		cd = gcd(numer, denom)
		return numer//cd, denom//cd

	def __init__(self, numer, denom, fundamental=None):
		self.numer, self.denom = Interval.normalise(numer, denom)
		self.fundamental = fundamental

		frac = self.numer / self.denom
		dist = 100
		for i in range(12):
			d = abs(cent_diff(frac, Interval._NOTE_EQTT[i]))
			if d < dist:
				dist = d
				self.note_i = i

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
		return Interval._NOTE_EQTT[self.note_i]

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

	def copy(self):
		return Interval(self.numer, self.denom)

	# difference in cents
	def __sub__(self, other):
		return cent_diff(self.fraction, other.fraction)

	# "musically" added intervals, i.e. M3 * P5 == M7
	# if other is number, multiply frequency
	def __mul__(self, other):
		try:
			return Interval(self.numer * other.numer, self.denom * other.denom)
		except AttributeError:
			return self.frequency * other
	__rmul__ = __mul__

	def __pow__(self, other):
		I_n = self.copy()
		for i in range(other-1):
			I_n *= self
		return I_n

	def __truediv__(self, other):
		return Interval(self.numer, other.numer)

	def __str__(self):
		return f"[{self.numer}:{self.denom}]({self.frequency:.2f}) {self.note_name} {cent_diff(self.fraction, self.closest_eqtt):+.1f} cents"

	def __repr__(self):
		return f"<class Interval: {self.__str__()}>"