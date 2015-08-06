__author__ = 'colby'


class Tile:
	valid_messages = ("on_click", "on_event")

	def __init__(self, *components):
		self.components = components
		self.x = None
		self.y = None
		self.world = None

	def add(self, world, x, y):
		self.x = x
		self.y = y
		self.world = world
		self.post_event("on_add")

	def remove(self):
		self.post_event("on_remove")
		self.x = self.y = self.world = None

	def post_event(self, name, *args):
		for component in self.components:
			if hasattr(component, name):
				out = getattr(component, name)(self, *args)
				if out:
					return out

	def __getattr__(self, name):
		if name in Tile.valid_messages:
			return lambda *args: self.post_event(name, *args)
		if name == "now":
			return self.world.time_provider.now()
		raise AttributeError("%r object has no attribute %r" % (self.__class__, name))

	def __setattr__(self, name, value):
		object.__setattr__(self, name, value)
		self.post_event("on_update_" + name)

	def set_icon(self, icon):
		self.world.update_icon_only(self.x, self.y, icon)

	def get_icon(self):
		return self.world.get_icon_only(self.x, self.y)

class SimpleIcon:
	def __init__(self, icon):
		self.icon = icon

	def on_add(self, ent):
		ent.set_icon(self.icon)

class TileType:
	def __init__(self, *components):
		self.components = components

	def __call__(self):
		return Tile(*self.components)
