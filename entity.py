__author__ = 'colby'

import math
import sdle
import tile


class Entity:
	# note: get_velocity must be constant between posts of on_kinematic_update
	valid_messages = ("on_add", "get_pos", "on_kinematic_update", "get_velocity", "get_size", "on_collide", "set_velocity", "control_move", "control_click", "on_update_map", "open_gui")

	def __init__(self, *components):
		if len(components) == 1 and type(components[0]) == list:
			components = components[0]
		self.components = components
		self.world = None  # gets set by World
		self.rendering_components = [comp for comp in components if hasattr(comp, "render")]
		self.position_components = [comp for comp in components if hasattr(comp, "get_pos")]
		assert self.position_components, "No positioning component for entity!"
		if len(self.position_components) == 1:
			self.get_pos = lambda now: self.position_components[0].get_pos(self, now)

	def get_pos(self, now):
		for comp in self.position_components:
			out = comp.get_pos(self, now)
			if out:
				return out

	def render(self, renderer, rx, ry, now):
		for comp in self.rendering_components:
			if comp.render(renderer, self, rx, ry, now):
				return

	def post_event(self, name, *args):
		for component in self.components:
			if hasattr(component, name):
				out = getattr(component, name)(self, *args)
				if out:
					return out

	def __getattr__(self, name):
		if name in Entity.valid_messages:
			return lambda *args: self.post_event(name, *args)
		if name == "now":
			return self.world.time_provider.now()
		raise AttributeError("%r object has no attribute %r" % (self.__class__, name))


class RenderImage:
	def __init__(self, image, srcrect=None, size=None):
		self.image = image
		self.srcrect = srcrect
		self.size = size if size else (srcrect[2:4] if srcrect else sdle.get_image_size(image))

	def render(self, renderer, ent, rx, ry, now):
		px, py = ent.get_pos(now)
		renderer.draw_image_centered(self.image, self.srcrect, px + rx, py + ry)

	def get_size(self, ent):
		return self.size


class PositionStatic:
	def __init__(self, x, y):
		self.pos = x, y

	def get_pos(self, ent, now):
		return self.pos

	def get_velocity(self, ent):
		return 0, 0


class PositionVelocity:
	def __init__(self, x, y, vx, vy):
		self.orig_pos_vel = x, y, vx, vy

	def on_add(self, ent, world):
		ent.pos_vel_time = self.orig_pos_vel + (ent.now,)

	def get_pos(self, ent, now):
		x, y, vx, vy, start_time = ent.pos_vel_time
		delta = ent.now - start_time
		return x + vx * delta, y + vy * delta

	def get_velocity(self, ent):
		return ent.pos_vel_time[2:4]

	def on_collide(self, ent, horizontally, vertically):
		_, _, vx, vy, _ = ent.pos_vel_time
		ent.set_velocity(0 if horizontally else vx, 0 if vertically else vy)

	def on_update_map(self, ent):
		_, _, vx, vy, _ = ent.pos_vel_time
		ent.set_velocity(vx, vy)

	def set_velocity(self, ent, new_vx, new_vy):
		x, y, vx, vy, start_time = ent.pos_vel_time
		now = ent.now
		time_delta = now - start_time
		ent.pos_vel_time = x + vx * time_delta, y + vy * time_delta, new_vx, new_vy, now
		ent.on_kinematic_update()


class Controllable:
	def __init__(self, speed, gui_cb):
		self.speed = speed
		self.gui_cb = gui_cb

	def control_move(self, ent, rx, ry):
		mag = math.sqrt(rx * rx + ry * ry)
		if mag == 0:
			ent.set_velocity(0, 0)
		else:
			mul = self.speed / mag
			ent.set_velocity(mul * rx, mul * ry)

	def control_click(self, ent, cx, cy, rx, ry):
		tent = ent.world[cx, cy]
		if isinstance(tent, tile.Tile):
			tent.on_click(ent, rx, ry)

	def open_gui(self, ent, gui):
		self.gui_cb(gui)

FUDGE_FACTOR = 0.001


class GridCollider:
	def on_add(self, ent, world):
		ent.last_timer_cancel = None
		world.time_provider.on_next(self.on_kinematic_update, ent)

	def on_kinematic_update(self, ent):
		if ent.last_timer_cancel:
			ent.last_timer_cancel()
			ent.last_timer_cancel = None
		# TODO: don't assume that the bounding box of the moving object is smaller than the wall bounding box
		w, h = ent.get_size()
		x, y = ent.get_pos(ent.now)
		vx, vy = ent.get_velocity()
		print("UPDATE", "%s,%s" % (x, y), "%sx%s" % (w, h), "%s,%s" % (vx, vy))
		distance = float("inf")
		speed = math.sqrt(vx * vx + vy * vy)
		if speed == 0:
			return
		direction = vx / speed, vy / speed
		colliding_horizontally, colliding_vertically = False, False
		for corner in ((x - w/2, y - h/2), (x + w/2, y - h/2), (x - w/2, y + h/2), (x + w/2, y + h/2)):
			# trace each component separately (as in, only look for vertical lines and then only look for horizontal lines)
			distance_horizontal = ent.world.ray_cast(corner, direction, is_vertical=False, fudge_factor=FUDGE_FACTOR)
			distance_vertical = ent.world.ray_cast(corner, direction, is_vertical=True, fudge_factor=FUDGE_FACTOR)
			distance = min(distance, distance_horizontal, distance_vertical)
			if distance_horizontal <= FUDGE_FACTOR:
				colliding_horizontally = True
			if distance_vertical <= FUDGE_FACTOR:
				colliding_vertically = True
		time = distance / speed
		if colliding_vertically or colliding_horizontally:
			ent.on_collide(colliding_horizontally, colliding_vertically)
		else:
			ent.last_timer_cancel = ent.world.time_provider.add_timer(time, ent.on_kinematic_update)


LAMBDA_TYPE = type(lambda: None)


class EntityType:
	def __init__(self, *components):
		self.lambdas = [component for component in components if type(component) == LAMBDA_TYPE]
		self.arg_count = sum(lmb.__code__.co_argcount for lmb in self.lambdas)
		self.components = [component for component in components if type(component) != LAMBDA_TYPE]

	def __call__(self, *args):
		if len(args) != self.arg_count:
			raise TypeError("EntityType() missing %d required positional argument", self.arg_count)
		components = self.components[:]
		index = 0
		for lmb in self.lambdas:
			count = lmb.__code__.co_argcount
			components.append(lmb(*args[index:index+count]))
			index += count
		assert index == self.arg_count
		return Entity(*components)
