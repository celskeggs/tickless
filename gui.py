__author__ = 'colby'

class GUI:
	def render(self, cx, cy):
		pass

	def click(self, rx, ry, btn):
		pass

	def get_size(self):
		return 0, 0

	def on_close(self):
		pass

class BasicGUI(GUI):
	def __init__(self, zlevel, textures=()):
		self.textures = [zlevel.renderer.load_image(txt) for txt in textures]

	def render(self, cx, cy):
		tex = self.textures[self.get_active_texture()]
		w, h = tex.get_size()
		tex.render(None, (int(cx - w / 2), int(cy - h / 2), w, h))

	def get_size(self):
		return self.textures[self.get_active_texture()].get_size()

	def get_active_texture(self):
		return 0

	def on_close(self):
		for tex in self.textures:
			tex.destroy()

class DoorGUI(BasicGUI):
	def __init__(self, ent):
		BasicGUI.__init__(self, ent.zlevel, ("door_open.png", "door_closed.png"))
		self.ent = ent

	def click(self, rx, ry, btn):
		self.ent.is_open = not self.ent.is_open

	def get_active_texture(self):
		return int(not self.ent.is_open)
