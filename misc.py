class SortedList():
	def __init__(self, max_size, key=lambda x:x):
		self.max_size = max_size
		self.data = []
		self.f = key

	@property
	def n(self):
		return len(self.data)

	@property
	def top(self):
		return self.get(0)

	# return true if added
	def push(self, e):
		if self.max_size > self.n:
			self.data.append(e)
		else:
			if self.f(self.data[-1]) <= self.f(e):
				return False
			else:
				self.data[-1] = e

		self.data.sort(key=self.f)
		return True

	def as_list(self):
		return self.data

	def __getitem__(self, i):
		return self.data[i]

	def __str__(self):
		return str(self.data)
	__repr__ = __str__

	def __bool__(self):
		return self.n != 0