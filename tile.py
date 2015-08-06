__author__ = 'colby'

import gui


class Tile:
	valid_messages = ("on_click", "on_event")

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

	def __setattr__(self, name, value):
		object.__setattr__(self, name, value)
		self.post_event("on_update_" + name)

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
	def __init__(self, icon1, icon2, var):
		self.icon1, self.icon2, self.var = icon1, icon2, var

	def on_add(self, ent):
		self._update(ent)

	def var_update(self, ent, name):
		if name == self.var:
			self._update(ent)

	def _update(self, ent):
		ent.set_icon(self.icon1 if getattr(ent, self.var) else self.icon2)

class DoorComponent:
	def __init__(self, open, closed):
		self.open_icon = open
		self.closed_icon = closed

	def on_add(self, ent):
		ent.is_open = False

	def on_click(self, ent, x, y):
		ent.zlevel.gui = gui.DoorGUI(ent)

	def toggle(self, ent):
		ent.is_open = not ent.is_open

	def on_update_is_open(self, ent):
		ent.set_icon(self.open_icon if ent.is_open else self.closed_icon)

def Door():
	return Tile(DoorComponent((2, 0), (3, 0)))
