__author__ = 'colby'
# depends on pysdl2-cffi
# Interesting technical part of this: this game is tickless!

import sdle
import sdl
import world
import tile

import door
import player
import loader


class MainLoop:
	running = True
	direction_keycodes = (sdl.SCANCODE_W, sdl.SCANCODE_A, sdl.SCANCODE_S, sdl.SCANCODE_D)

	def __init__(self):
		self.win_size = 640, 480
		self.window = sdle.Window("Tickless", self.win_size[0], self.win_size[1])
		self.tileset = world.Tileset("tileset2.png", 4, 4)
		self.event_loop = sdle.EventLoop(
			on_quit=self.on_quit, on_mouse_down=self.on_click, on_key_down=self.on_key_down, on_key_up=self.on_key_up)
		self.world = loader.load("map.txt", self.tileset, self.event_loop)
		# world.World(19, 14, self.tileset, (0, 0), [(0, 0), (2, 0)], self.event_loop)
		self.directions = [False, False, False, False]

		self.gui = None
		self.gui_size = 0, 0
		self.player = None

		self.generate_world()

	def on_quit(self):
		self.running = False

	def on_click(self, win, x, y, button, clicks):
		if self.gui is not None:
			w, h = self.gui_size
			rx, ry = x - self.win_size[0] / 2, y - self.win_size[1] / 2
			if -w/2 <= rx <= w/2 and -h/2 <= ry <= h/2:
				self.gui.click(rx, ry, button)
			else:
				gui = self.gui
				self.gui = None
				gui.on_close()
		else:
			vx, vy = self.get_viewport_position()
			cx, cy, rx, ry = self.world.unmap(x - vx, y - vy)
			if cx and self.player is not None:
				self.player.control_click(cx, cy, rx, ry)

	def on_key_down(self, win, sym, scancode, mod, repeat):
		if not repeat and scancode in self.direction_keycodes:
			self.directions[self.direction_keycodes.index(scancode)] = True
			self.update_motion()

	def on_key_up(self, win, sym, scancode, mod):
		if scancode in self.direction_keycodes:
			self.directions[self.direction_keycodes.index(scancode)] = False
			self.update_motion()

	def get_viewport_position(self):
		return 0, 0

	def update_motion(self):
		if self.player is not None:
			dx = self.directions[3] - self.directions[1]
			dy = self.directions[2] - self.directions[0]
			self.player.control_move(dx, dy)

	def generate_world(self):
#		for x in range(3, 13):
#			if x == 7:
#				self.world[x, 7] = door.DoorTile()
#				continue
#			for y in range(6, 9):
#				self.world[x, y] = (1, 0)
		self.player = self.world.add_entity(player.Player(7.5 * 32, 7 * 32, self.open_gui))

	def open_gui(self, gui):
		self.gui = gui

	def mainloop(self):
		while self.running:
			# LOOP FOREVER AS FAST AS POSSIBLE
			# Unlimited FPS ftw?
			self.event_loop.pump()
			self.window.clear()
			vx, vy = self.get_viewport_position()
			self.world.render(self.window, vx, vy)
			if self.gui is not None:
				self.gui_size = self.gui.render(self.window, self.win_size[0] / 2, self.win_size[1] / 2)
			else:
				self.gui_size = 0, 0
			self.window.present()

	def destroy(self):
		self.window.destroy()

if __name__ == "__main__":
	ml = MainLoop()
	ml.mainloop()
	ml.destroy()
