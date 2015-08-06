__author__ = 'colby'

import sdl  # pysdl2-cffi
import atexit
import weakref

assert sdl.init(0) == 0
assert sdl.image.init(0) == 0
atexit.register(sdl.quit)


class SDLException(Exception):
	def __init__(self, message, include_get_error=True):
		if include_get_error:
			message += ": %s" % sdl.getError()
		Exception.__init__(message)
		self.message = message


def check(handle, err):
	if handle == 0:
		raise SDLException(err)
	assert handle
	return handle

_windows = weakref.WeakValueDictionary()
class Window:
	sdl_destroyWindow = sdl.destroyWindow  # moved here to prevent shutdown issues
	POS_CENTERED = sdl.WINDOWPOS_CENTERED
	POS_UNDEFINED = sdl.WINDOWPOS_UNDEFINED

	def __init__(self, title, width, height, x=POS_CENTERED, y=POS_CENTERED):
		# TODO: flag control
		self.handle = check(sdl.createWindow(title, x, y, width, height, sdl.WINDOW_OPENGL), "Could not create window")
		self.winid = sdl.getWindowID(self.handle)
		self.size = width, height
		_windows[self.winid] = self

	def create_renderer(self):
		return Renderer(self)

	def destroy(self):
		if self.handle is not None:
			Window.sdl_destroyWindow(self.handle)
			del _windows[self.winid]
			self.handle = None

	def __del__(self):
		if self.handle is not None:
			print("Warning! Window not destroyed properly.")
			self.destroy()

class Renderer:
	sdl_destroyRenderer = sdl.destroyRenderer

	def __init__(self, window):
		assert window.handle is not None
		self.window = window
		# sdl.RENDERER_PRESENTVSYNC
		self.handle = check(sdl.createRenderer(window.handle, -1, sdl.RENDERER_ACCELERATED | 0), "Could not create renderer")

	def clear(self):
		assert self.handle is not None
		sdl.setRenderDrawColor(self.handle, 0, 0, 0, 255)
		if sdl.renderClear(self.handle) != 0:
			raise SDLException("Could not clear screen")

	def draw_line(self, x1, y1, x2, y2, color):
		assert self.handle is not None
		sdl.setRenderDrawColor(self.handle, color[0], color[1], color[2], color[3] if len(color) > 3 else 255)
		sdl.renderDrawLine(self.handle, x1, y1, x2, y2)

	def copy(self, texture, srcrect=None, dstrect=None):
		assert self.handle is not None
		assert isinstance(texture, Texture) and texture.handle is not None
		if sdl.renderCopy(self.handle, texture.handle, srcrect, dstrect) != 0:
			raise SDLException("Could not render texture")

	def present(self):
		assert self.handle is not None
		assert sdl.renderPresent(self.handle) is None

	def destroy(self):
		if self.handle is not None:
			Renderer.sdl_destroyRenderer(self.handle)
			self.handle = None

	def __del__(self):
		if self.handle is not None:
			print("Warning! Renderer not destroyed properly.")
			self.destroy()


class Surface:
	def __init__(self, handle):
		self.handle = check(handle, "Bad surface")

	def to_texture(self, renderer):
		assert isinstance(renderer, Renderer) and renderer.handle is not None
		return Texture(check(sdl.createTextureFromSurface(renderer.handle, self.handle), "Could not convert surface to Texture"))

	def destroy(self):
		# TODO: why doesn't SDL require destroying this?
		if self.handle is not None:
			# sdl_destroySurface(self.handle)
			self.handle = None

	def __del__(self):
		if self.handle is not None:
			print("Warning! Surface not destroyed properly.")
			self.destroy()


class Texture:
	sdl_destroyTexture = sdl.destroyTexture

	def __init__(self, handle):
		self.handle = check(handle, "Bad texture")

	def destroy(self):
		if self.handle is not None:
			Texture.sdl_destroyTexture(self.handle)
			self.handle = None

	def __del__(self):
		if self.handle is not None:
			print("Warning! Texture not destroyed properly.")
			self.destroy()

	def get_size(self):
		out = sdl.queryTexture(self.handle)
		assert out[0] == 0, "invalid texture"
		return out[3], out[4]

def image(name):
	return Surface(check(sdl.image.load(name), "Could not load image"))


def delay(millis):
	sdl.delay(millis)


_event = sdl.Event()

def pump(on_quit=None, on_key_down=None, on_key_up=None, on_mouse_motion=None, on_mouse_down=None, on_mouse_up=None, on_mouse_wheel=None):
	while sdl.pollEvent(_event):
		if _event.type == sdl.QUIT and on_quit:
			on_quit()
		elif _event.type == sdl.KEYDOWN and on_key_down:
			on_key_down(_windows[_event.key.windowID], _event.key.keysym.sym, _event.key.keysym.scancode, _event.key.keysym.mod, _event.key.repeat)
		elif _event.type == sdl.KEYUP and on_key_up:
			on_key_up(_windows[_event.key.windowID], _event.key.keysym.sym, _event.key.keysym.scancode, _event.key.keysym.mod)
		elif _event.type == sdl.MOUSEMOTION and on_mouse_motion:
			on_mouse_motion(_windows[_event.motion.windowID], _event.motion.x, _event.motion.y, _event.motion.state)
		elif _event.type == sdl.MOUSEBUTTONDOWN and on_mouse_down:
			on_mouse_down(_windows[_event.button.windowID], _event.button.x, _event.button.y, _event.button.button, _event.button.clicks)
		elif _event.type == sdl.MOUSEBUTTONUP and on_mouse_up:
			on_mouse_up(_windows[_event.button.windowID], _event.button.x, _event.button.y, _event.button.button, _event.button.clicks)
		elif _event.type == sdl.MOUSEWHEEL and on_mouse_wheel:
			on_mouse_wheel(_windows[_event.wheel.windowID], _event.wheel.x, _event.wheel.y, _event.wheel.direction == sdl.MOUSEWHEEL_FLIPPED)
		else:
			pass  # ignore it and try again
