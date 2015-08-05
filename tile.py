__author__ = 'colby'


class Tile:
	valid_messages = ()

	def __init__(self, *components):
		self.components = components
		self.x = None
		self.y = None
		self.zlevel = None

	def add(self, zlevel, x, y):
		self.x = x
		self.y = y
		self.zlevel = zlevel
		self.post_event("on_add")

	def remove(self):
		self.post_event("on_remove")
		self.x = self.y = self.zlevel = None

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
			return self.zlevel.time_provider.now()
		raise AttributeError("%r object has no attribute %r" % (self.__class__, name))

	def set_icon(self, icon):
		self.zlevel.grid.update_icon_only(self.x, self.y, icon)

	def get_icon(self):
		return self.zlevel.grid.get_icon_only(self.x, self.y)

class SimpleIcon:
	def __init__(self, icon):
		self.icon = icon

	def on_add(self, ent):
		ent.set_icon(self.icon)

class ChangingIcon:
	def __init__(self, icon1, icon2):
		self.icon1, self.icon2 = icon1, icon2

	def on_add(self, ent):
		self._update(ent)

	def _update(self, ent):
		ent.set_icon(self.icon1 if ent.get_icon() == self.icon2 else self.icon2)
		ent.zlevel.time_provider.add_timer(1, self._update, ent)

def ExampleTile(icon1, icon2):
	return Tile(ChangingIcon(icon1, icon2))
