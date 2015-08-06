__author__ = 'colby'

class GUI:
	def render(self, renderer, cx, cy):
		return 0, 0  # size

	def click(self, rx, ry, btn):
		pass

	def on_close(self):
		pass

class BasicGUI(GUI):
	def __init__(self, texture):
		self.texture = texture

	def render(self, renderer, cx, cy):
		return renderer.draw_image_centered(self.texture, None, cx, cy)
