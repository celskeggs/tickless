__author__ = 'colby'

import math


class Entity:
	# note: get_velocity must be constant between posts of on_kinematic_update
	valid_messages = ("on_add", "get_pos", "on_kinematic_update", "get_velocity", "get_size", "on_collide", "set_velocity", "control_move", "on_update_map")

	def __init__(self, *components):
		if len(components) == 1 and type(components[0]) == list:
			components = components[0]
		self.components = components
		self.zlevel = None  # gets set by ZLevel
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

	def render(self, rx, ry, now):
		for comp in self.rendering_components:
			if comp.render(self, rx, ry, now):
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
			return self.zlevel.time_provider.now()
		raise AttributeError("%r object has no attribute %r" % (self.__class__, name))


class RenderImage:
	def __init__(self, image, srcrect=None, size=None):
		self.image = image
		self.srcrect = srcrect
		self.size = size if size else ((srcrect[2], srcrect[3]) if srcrect else image.get_size())

	def render(self, ent, rx, ry, now):
		px, py = ent.get_pos(now)
		w, h = self.size
		self.image.render(self.srcrect, (int(px + rx - w / 2), int(py + ry - h / 2), w, h))

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

	def on_add(self, ent, zlevel):
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
	def __init__(self, speed):
		self.speed = speed

	def control_move(self, ent, rx, ry):
		mag = math.sqrt(rx * rx + ry * ry)
		if mag == 0:
			ent.set_velocity(0, 0)
		else:
			mul = self.speed / mag
			ent.set_velocity(mul * rx, mul * ry)


FUDGE_FACTOR = 0.001


class GridCollider:
	def on_add(self, ent, zlevel):
		ent.last_timer_cancel = None
		self.on_kinematic_update(ent)

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
			distance_horizontal = ent.zlevel.grid.ray_cast(corner, direction, is_vertical=False, fudge_factor=FUDGE_FACTOR)
			distance_vertical = ent.zlevel.grid.ray_cast(corner, direction, is_vertical=True, fudge_factor=FUDGE_FACTOR)
			distance = min(distance, distance_horizontal, distance_vertical)
			if distance_horizontal <= FUDGE_FACTOR:
				colliding_horizontally = True
			if distance_vertical <= FUDGE_FACTOR:
				colliding_vertically = True
		time = distance / speed
		if colliding_vertically or colliding_horizontally:
			ent.on_collide(colliding_horizontally, colliding_vertically)
		else:
			ent.last_timer_cancel = ent.zlevel.time_provider.add_timer(time, ent.on_kinematic_update)


def EntExample(x, y, vx, vy, image):
	return Entity(RenderImage(image), PositionVelocity(x, y, vx, vy), GridCollider(), Controllable(64))
