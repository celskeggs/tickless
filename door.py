__author__ = 'colby'

import gui
import tile

TILE_DOOR_OPEN = (3, 0)
TILE_DOOR_CLOSED = (2, 0)


class DoorGUI(gui.GUI):
	def __init__(self, ent):
		self.ent = ent

	def click(self, rx, ry, btn):
		self.ent.is_open = not self.ent.is_open

	def render(self, renderer, cx, cy):
		return renderer.draw_image_centered("door_open.png" if self.ent.is_open else "door_closed.png", None, cx, cy)


class DoorComponent:
	def __init__(self, open, closed):
		self.open_icon = open
		self.closed_icon = closed

	def on_add(self, ent):
		ent.is_open = False

	def on_click(self, ent, player, x, y):
		player.open_gui(DoorGUI(ent))

	def on_update_is_open(self, ent):
		ent.set_icon(self.open_icon if ent.is_open else self.closed_icon)

DoorTile = tile.TileType(DoorComponent(TILE_DOOR_OPEN, TILE_DOOR_CLOSED))
