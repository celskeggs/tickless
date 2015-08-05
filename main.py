__author__ = 'colby'
# depends on pysdl2-cffi
# Interesting technical part of this: this game is tickless!

import sdle, sdl
import time
import world
import entity

running = True

def quitt(*args):
	global running
	running = False

def main():
	window = sdle.Window("Example", 640, 480)
	tileset = world.Tileset(window, "tileset.png", 4, 4)
	pyramid = window.load_image("pyramid_small.png")
	print(pyramid.get_size())

	render_frames = 0

	cycle = [(3, 0), (1, 1),  (1, 0), (2, 1), (1, 2), (0, 1),  (0, 0), (2, 0), (2, 2), (0, 2)]

	def click(win, x, y, button, clicks):
		tup = zlevel.grid.unmap(x - 5, y - 5)
		if tup:
			zlevel.grid[tup] = cycle[(cycle.index(zlevel.grid[tup]) + (1 if button == 1 else -1)) % len(cycle)]
	directions = [False, False, False, False]
	direction_codes = (sdl.SCANCODE_W, sdl.SCANCODE_A, sdl.SCANCODE_S, sdl.SCANCODE_D)

	def update_motion():
		dx = directions[3] - directions[1]
		dy = directions[2] - directions[0]
		if player is not None:
			player.control_move(dx, dy)

	def key_down(win, sym, scancode, mod, repeat):
		if not repeat and scancode in direction_codes:
			directions[direction_codes.index(scancode)] = True
			update_motion()

	def key_up(win, sym, scancode, mod):
		if scancode in direction_codes:
			directions[direction_codes.index(scancode)] = False
			update_motion()
	loop = sdle.EventLoop(on_quit=quitt, on_mouse_down=click, on_key_down=key_down, on_key_up=key_up)

	zlevel = world.ZLevel(world.Grid(19, 14, tileset, window, (3, 0), [(3, 0)]), loop)
	for x in range(5, 10):
		for y in range(6, 9):
			zlevel.grid[x, y] = (1, 1)
	player = zlevel.add_entity(entity.EntExample(7.5 * 32, 7 * 32, 0, 0, pyramid))

	print("READY", running)

	now = time.monotonic()
	while running:
		# LOOP FOREVER AS FAST AS POSSIBLE
		# Unlimited FPS ftw?
		loop.pump()
		window.clear()
		zlevel.render(5, 5)
		window.present()
		render_frames += 1
		if render_frames % 3000 == 0:
			here = time.monotonic()
			print(render_frames / (here - now), loop.now())
			now = here
			render_frames = 0

	tileset.destroy()
	pyramid.destroy()
	window.destroy()

main()
