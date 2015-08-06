__author__ = 'colby'

import sdl_ll
import time
import heapq


class Window:
	def __init__(self, title, width, height):
		self.window = sdl_ll.Window(title, width, height)
		self.window.sdle_window = self
		self.renderer = self.window.create_renderer()

	def destroy(self):
		self.renderer.destroy()
		self.window.destroy()

	def load_image(self, name):
		return Image(name, self)

	def draw_line(self, x1, y1, x2, y2=None, color=None):
		if y2 is None:
			assert color is None
			color = x2
			x2, y2 = y1
			x1, y1 = x1
		else:
			assert color is not None
		self.renderer.draw_line(x1, y1, x2, y2, color)

	def clear(self):
		self.renderer.clear()

	def present(self):
		self.renderer.present()

	def get_size(self):
		return self.window.size

class Image:
	def __init__(self, name, window):
		assert isinstance(window, Window)
		self.window = window
		self.image = sdl_ll.image(name)
		self.texture = self.image.to_texture(window.renderer)

	def destroy(self):
		self.texture.destroy()
		self.image.destroy()

	def render(self, srcrect=None, dstrect=None):
		self.window.renderer.copy(self.texture, srcrect, dstrect)

	def get_size(self):
		return self.texture.get_size()


def _wrap_cb(orig):
	return lambda winraw, *args: orig(winraw.sdle_window, *args)

def do_nothing():
	pass

class EventLoop:
	def __init__(self, **events):
		# wrap the callbacks so that they convert to sdle windows
		self.events = dict((key, _wrap_cb(orig)) for key, orig in events.items() if key != "on_quit")
		if "on_quit" in events:
			self.events["on_quit"] = events["on_quit"]
		self.timers = []
		self.entryid = 0
		self._now = time.monotonic()

	def now(self):
		return self._now

	def on_next(self, cb, *args):
		self.add_timer(0, cb, *args)

	def add_timer_at(self, mono, cb, *args):
		if mono == float("inf"):
			return do_nothing  # don't even bother
		tup = (mono, self.entryid, cb) + tuple(args)
		heapq.heappush(self.timers, tup)
		self.entryid += 1

		def remove():
			if not self.timers or self.timers[0][0] > mono:
				return
			self.timers[self.timers.index(tup)] = (mono, tup[1], do_nothing)
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
