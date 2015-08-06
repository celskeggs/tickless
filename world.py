__author__ = 'colby'

import bisect
import math
import tile
import sdle


class Tileset:
	def __init__(self, name, width, height, cell_width=32, cell_height=32):
		self.image = name
		real_height, real_width = sdle.get_image_size(name)
		self.cw, self.ch = cell_width, cell_height
		self.w, self.h = width, height
		assert real_width == width * cell_width and real_height == height * cell_height, "Tileset has unexpected bounds!"

	def render(self, renderer, texture_x, texture_y=None, base_x=0, base_y=0, cells_x=0, cells_y=0):
		if texture_y is None:
			if type(texture_x) == tuple:
				texture_x, texture_y = texture_x
			else:
				texture_y = texture_x / self.w
				texture_x %= self.w
		assert 0 <= texture_x < self.w and 0 <= texture_y < self.h
		renderer.draw_image(
			self.image,
			(texture_x * self.cw, texture_y * self.ch, self.cw, self.ch),
			(base_x + cells_x * self.cw, base_y + cells_y * self.ch, self.cw, self.ch))

	def unmap(self, mouse_x, mouse_y):
		return mouse_x // self.cw, mouse_y // self.ch, mouse_x % self.cw, mouse_y % self.ch

	def cell_size(self):
		return self.cw, self.ch


DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]
IDX_UP = DIRECTIONS.index(DIR_UP)
IDX_DOWN = DIRECTIONS.index(DIR_DOWN)
IDX_LEFT = DIRECTIONS.index(DIR_LEFT)
IDX_RIGHT = DIRECTIONS.index(DIR_RIGHT)
DIRECTION_COLORS = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0)]


class World:
	def __init__(self, width, height, tileset, default_tile, solid_tiles, time_provider):
		self.tileset = tileset
		self.time_provider = time_provider
		self.layer = [[default_tile] * height for _ in range(width)]
		self.tiles = {}
		self.segments = [[], [], [], []]
		self.solid_tiles = solid_tiles
		self.cache_dirty = True
		self.entities = []

	def add_entity(self, ent):
		self.entities.append(ent)
		ent.world = self
		ent.on_add(self)
		return ent

	def __getitem__(self, item):
		if item in self.tiles:
			return self.tiles[item]
		x, y = item
		return self.layer[x][y]

	def __setitem__(self, item, value):
		x, y = item
		if item in self.tiles:
			self.tiles[item].remove()
			del self.tiles[item]
		if isinstance(value, tile.Tile):
			self.tiles[item] = value
			self.layer[x][y] = None
			value.add(self, x, y)
			assert self.layer[x][y] is not None, "Tile didn't add an icon!"
		else:
			self.layer[x][y] = value
		self.dirty_cache()

	def update_icon_only(self, x, y, value):
		self.layer[x][y] = value
		self.dirty_cache()

	def dirty_cache(self):
		if not self.cache_dirty:
			self.time_provider.on_next(self.on_update_map)
			self.cache_dirty = True

	def on_update_map(self):
		assert self.cache_dirty
		for ent in self.entities:
			ent.on_update_map()

	def get_icon_only(self, x, y):
		return self.layer[x][y]

	def render(self, renderer, rx, ry):
		for x, column in enumerate(self.layer):
			for y, cell in enumerate(column):
				self.tileset.render(renderer, cell, base_x=rx, base_y=ry, cells_x=x, cells_y=y)
		# these are subtly different, which is why they aren't refactored yet
		# also, they're just debugging
		if False:
			for y, x1, x2 in self.segments[IDX_UP]:
				renderer.draw_line(rx + x1, ry + y, rx + x2, ry + y, (0, 255, 0))
			for y, x1, x2 in self.segments[IDX_DOWN]:
				renderer.draw_line(rx + x1, ry + y, rx + x2, ry + y, (0, 0, 255))
			for x, y1, y2 in self.segments[IDX_LEFT]:
				renderer.draw_line(rx + x, ry + y1, rx + x, ry + y2, (255, 0, 0))
			for x, y1, y2 in self.segments[IDX_RIGHT]:
				renderer.draw_line(rx + x, ry + y1, rx + x, ry + y2, (255, 255, 0))
		# end of debugging
		now = self.time_provider.now()
		for ent in self.entities:
			ent.render(renderer, rx, ry, now)

	def unmap(self, mouse_x, mouse_y):
		if 0 <= mouse_x and 0 <= mouse_y:
			cx, cy, rx, ry = self.tileset.unmap(mouse_x, mouse_y)
			if cx < len(self.layer) and cy < len(self.layer[cx]):
				return cx, cy, rx, ry
		return None, None, None, None

	def is_solid(self, x, y):
		return x < 0 or x >= len(self.layer) or y < 0 or y >= len(self.layer[x]) or self.layer[x][y] in self.solid_tiles

	def is_type_solid(self, cell):
		return cell in self.solid_tiles

	def recalculate_cache(self):
		assert self.cache_dirty
		for i, direction in enumerate(DIRECTIONS):
			vertical = not direction[0]
			# represented by the (x, y) of the cell to the lower-right. so the two upper-left-corner lines are both (0, 0)
			# and the two lower-right-corner lines are both (width, height)
			lines = set()
			for x, column in enumerate(self.layer):
				for y, cell in enumerate(column):
					if self.is_type_solid(cell) and not self.is_solid(x + direction[0], y + direction[1]):
						# the weird additions are to account for the fact that we're in a different cell than the target
						rx = x + (direction == DIR_RIGHT)
						ry = y + (direction == DIR_DOWN)
						lines.add((ry, rx) if vertical else (rx, ry))
			# now, that's not our final representation.
			# our final representation is (x, y1, y2) where y1 < y2 OR (y, x1, x2) where x1 < x2
			# we choose that order so that sorting and binary search are easy.
			merged = []
			while lines:
				dep, idp = lines.pop()
				idp1, idp2 = idp, idp
				while (dep, idp1 - 1) in lines:
					idp1 -= 1
					lines.remove((dep, idp1))
				while (dep, idp2 + 1) in lines:
					idp2 += 1
					lines.remove((dep, idp2))
				merged.append((dep, idp1, idp2 + 1))
			merged.sort()
			# ... and now let's make it in pixels instead of cells
			if vertical:
				cd, ci = self.tileset.cell_size()
			else:
				ci, cd = self.tileset.cell_size()
			self.segments[i] = [(dep * cd, idp1 * ci, idp2 * ci) for dep, idp1, idp2 in merged]
		self.cache_dirty = False

	def ray_cast(self, origin, direction, is_vertical, fudge_factor):  # returns distance
		if self.cache_dirty:
			self.recalculate_cache()
		# we will work with HORIZONTAL segments when we're VERTICAL, and vice versa.
		if is_vertical:
			dependent, independent = origin
			direction_dependent, direction_independent = direction
			segments = self.segments[IDX_DOWN if direction_independent < 0 else IDX_UP]
		else:
			independent, dependent = origin
			direction_independent, direction_dependent = direction
			segments = self.segments[IDX_RIGHT if direction_independent < 0 else IDX_LEFT]
		if direction_independent == 0:
			return float("inf")  # directly horizontal or vertical
		# slope... or not-quite-slope, depending on orientation
		slope = direction_dependent / float(direction_independent)
		# first, find where to start. we use binary search.
		if direction_independent > 0:  # downwards
			# we want the leftmost element greater than (independent, -1, -1)
			start_at = bisect.bisect_right(segments, (independent - fudge_factor, -1, -1))
			for i in range(start_at, len(segments)):
				this_independent, dependent_min, dependent_max = segments[i]
				this_dependent = dependent + slope * (this_independent - independent)
				if dependent_min + fudge_factor <= this_dependent <= dependent_max - fudge_factor:
					delta_dependent = this_dependent - dependent
					delta_independent = this_independent - independent
					return math.sqrt(delta_dependent * delta_dependent + delta_independent * delta_independent)
		elif direction_independent < 0:  # upwards
			# we want the rightmost element less than (independent+1, -1, -1)
			start_at = bisect.bisect_left(segments, (independent + fudge_factor, -1, -1)) - 1
			for i in range(start_at, -1, -1):
				this_independent, dependent_min, dependent_max = segments[i]
				this_dependent = dependent + slope * (this_independent - independent)
				if dependent_min + fudge_factor <= this_dependent <= dependent_max - fudge_factor:
					delta_dependent = this_dependent - dependent
					delta_independent = this_independent - independent
					return math.sqrt(delta_dependent * delta_dependent + delta_independent * delta_independent)
		# infinite distance when nothing gets hit (which shouldn't happen much in practice)
		return float("inf")
