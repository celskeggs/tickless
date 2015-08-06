__author__ = 'colby'

import sdl_ll
import time
import heapq
import os
import atexit

_images = {}
def _cleanup_images():
	for image in _images.values():
		image.destroy()
atexit.register(_cleanup_images)

def _get_image(name):
	if name not in _images:
		_images[name] = sdl_ll.image(os.path.join("assets", name))
	return _images[name]

def get_image_size(name):
	img = _get_image(name)
	return img.get_size()

def round_rect(rect):
	if rect is not None:
		x, y, w, h = rect
		return round(x), round(y), round(w), round(h)

class Window:
	def __init__(self, title, width, height):
		self.window = sdl_ll.Window(title, width, height)
		self.window.sdle_window = self
		self.renderer = self.window.create_renderer()
		self.texture_cache = {}

	def destroy(self):
		for texture in self.texture_cache.values():
			texture.destroy()
		self.renderer.destroy()
		self.window.destroy()

	def draw_line(self, x1, y1, x2, y2=None, color=None):
		if y2 is None:
			assert color is None
			color = x2
			x2, y2 = y1
			x1, y1 = x1
		else:
			assert color is not None
		self.renderer.draw_line(x1, y1, x2, y2, color)

	def _get_image(self, name):
		if name not in self.texture_cache:
			texture = _get_image(name).to_texture(self.renderer)
			self.texture_cache[name] = texture
		return self.texture_cache[name]

	def draw_image(self, name, srcrect=None, dstrect=None):
		self.renderer.copy(self._get_image(name), round_rect(srcrect), round_rect(dstrect))

	def draw_image_centered(self, name, srcrect=None, cx=None, cy=None):
		assert cx is not None
		w, h = srcrect[2:4] if srcrect else get_image_size(name)
		if cy is None:
			cx, cy = cx
		self.draw_image(name, srcrect, (cx - w / 2, cy - h / 2, w, h))
		return w, h

	def clear(self):
		self.renderer.clear()

	def present(self):
		self.renderer.present()

	def get_size(self):
		return self.window.size


class EventLoop:
	def __init__(self, **events):
		# wrap the callbacks so that they convert to sdle windows
		self.events = dict((key, EventLoop._wrap_cb(orig)) for key, orig in events.items() if key != "on_quit")
		if "on_quit" in events:
			self.events["on_quit"] = events["on_quit"]
		self.timers = []
		self.entryid = 0
		self._now = time.monotonic()

	@staticmethod
	def do_nothing():
		pass

	@staticmethod
	def _wrap_cb(orig):
		return lambda winraw, *args: orig(winraw.sdle_window, *args)

	def now(self):
		return self._now

	def on_next(self, cb, *args):
		self.add_timer(0, cb, *args)

	def add_timer_at(self, mono, cb, *args):
		if mono == float("inf"):
			return EventLoop.do_nothing  # don't even bother
		tup = (mono, self.entryid, cb) + tuple(args)
		heapq.heappush(self.timers, tup)
		self.entryid += 1

		def remove():
			if not self.timers or self.timers[0][0] > mono:
				return
			self.timers[self.timers.index(tup)] = (mono, tup[1], EventLoop.do_nothing)
		return remove

	def add_timer(self, timeout, cb, *args):
		return self.add_timer_at(self.now() + timeout, cb, *args)

	def add_interval(self, interval, cb, *args):
		def wrap_cb():
			self.add_timer(interval, wrap_cb)
			cb(*args)
		self.add_timer(interval, wrap_cb)

	def pump(self):
		now = time.monotonic()
		while self.timers and self.timers[0][0] <= now:
			timer = heapq.heappop(self.timers)
			self._now = timer[0]
			timer[2](*timer[3:])
		self._now = now
		sdl_ll.pump(**self.events)

delay = sdl_ll.delay
