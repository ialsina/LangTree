class Node:
	def __init__(self, name, children=None):
		self.name = name.replace('\n', '').strip()
		if isinstance(children, list):
			if len(children) == 0:
				self.children = []
			else:
				self.__assert(*children)
				self.children = children

		elif children is None:
			self.children = []

		else:
			raise TypeError("Argument 'children' must be list or None.")

	def add(self, *children):
		self.__assert(*children)
		self.children.extend(children)

	def __repr__(self):
		return "NODE: {} | CHILDREN_COUNT: {}".format(self.name, len(self.children))

	def __getitem__(self, ind):
		if isinstance(ind, int):
			return self.children[ind]
		elif isinstance(ind, str):
			for child in self.children:
				if child.name == ind:
					return child
			for child in self.children:
				if ind in child.name:
					return child
			return None

	def __setitem__(self, ind, child):
		self.__assert(child)
		if not isinstance(ind, int):
			raise ValueError
		self.children[ind] = child

	def __assert(self, *seq):
		if not all(isinstance(el, __class__) for el in seq):
			raise TypeError("Not all elements in input sequence belong to {}.".format(__class__))

	def json(self):
		if len(self.children) == 0:
			return self.name
		else:
			return {self.name: [child.json() for child in self.children]}

	def __draw_level(self, stack=[]):
		pattern = ''.join(list(map(lambda x: {False: "   ", True: "┃  "}.get(x), stack[:-1])))
		if len(stack) == 0:
			pass
		else:
			pattern += {True: "┠─ ", False: "┖─ "}.get(stack[-1])
		print(pattern + self.name)
		#print("┃  "*(stack-1) + ("┠─ " + self.name if stack else self.name))
		for (i, child) in enumerate(self.children):

			child.__draw_level(stack=stack+[i!=len(self.children)-1])



	def tree(self):

		self.__draw_level()


a = Node("a", [Node("a{}".format(i)) for i in range(1, 8)])
b = Node("b", [Node("b{}".format(i)) for i in range(1, 10)])
c = Node("c", [Node("c{}".format(i)) for i in range(1, 12)])
d = Node("d", [Node("d{}".format(i)) for i in range(1, 4)])

b[3] = d

z = Node("z", [a, b, Node("x"), c])