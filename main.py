from kivy.config import Config
from kivy.utils import platform

#Config.set('graphics','width','400')
if platform == 'android':
	Config.set('kivy','log_dir','/sdcard/kivy/KvLog/.kivy/logs')
	Config.write()

import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger, LoggerHistory, LOG_LEVELS
from kivy.properties import ObjectProperty
from kivy.clock import Clock

from plyer import accelerometer

import os
import re

files = {}
timekeys=[]
current_log = ''


def get_log_path():

	if platform == 'android':
		#return os.path.dirname(os.environ['ANDROID_APP_PATH'])
		return '/sdcard/kivy'
	elif platform == 'linux' or paltform == 'ios' or platform == 'macosx': # not yet tested on iOS and OSX.
		return kivy.kivy_home_dir + "/logs/"
	else:
		return None

	"""
	if platform == 'linux':
		return os.environ['HOME'] + "/.kivy/logs/"
	elif platform == 'android':
		return os.path.dirname(os.environ['ANDROID_APP_PATH'])
	elif paltform == 'ios' or platform == 'macosx': #not yet test~
		return os.environ['HOME'] + "/Documents/.kivy/logs/"
	else:
		return None
	"""

	
def get_log_files(log_folder):
	if os.path.isdir(log_folder):
		for log_file in os.listdir(log_folder):
			files[os.stat(log_folder+log_file).st_mtime] = log_folder+log_file


def get_previous_logfile():
	global timekeys
	global current_log

	path = get_log_path()
	if path ==None:
		return None

	if platform == 'android':
		dirs = os.listdir(path)
		for item in dirs:
			log_folder = path+"/"+item+"/.kivy/logs/"
			get_log_files(log_folder)
	#elif platform == 'linux' or platform == 'ios' or platform == 'macosx':
	else:
		get_log_files(path)

	timekeys = files.keys()
	nfiles = len(timekeys)
	if nfiles > 0:
		timekeys = sorted(timekeys)
		timekeys=list(timekeys)
		timekeys.reverse()
		file_to_dump = files[timekeys[1]] if nfiles > 1 else files[timekeys[0]]
		Logger.info("KvLog: dumping "  + file_to_dump)
		current_log = file_to_dump
		return file_to_dump
	else:
		return None


def log_from(source):
	dump_file= source
	if dump_file != None:
		f = open(dump_file)
		while True:
			text = f.readline()
			if text != '':
				yield text
			else:
				break
	else:
		yield None


def log_from_previous():
	return log_from(get_previous_logfile())


def log_from_choosed(choosed_file):
	return log_from(choosed_file)


def log_from_history():
	log_len = len(LoggerHistory.history)
	LoggerHistory.history.reverse()
	for i in range(log_len):
		yield str(LoggerHistory.history[i].lineno)+": " + \
				"[" + LoggerHistory.history[i].levelname + "] " + \
				LoggerHistory.history[i].getMessage()


def highlight_KvLog(msg):
	escape_msg = re.sub('\[', '&bl;', msg, 1)
	escape2_msg = re.sub('\]', '&br;', escape_msg, 1)
	if re.search('INFO', msg, 1) != None:
		h_msg = re.sub('INFO', '[color=00FF00]INFO[/color]', escape2_msg, 1)
		return h_msg
	elif re.search('WARNING', msg, 1) != None:
		h_msg = re.sub('WARNING', '[color=FFFF00]WARNING[/color]', escape2_msg, 1)
		return h_msg
	elif re.search('ERROR', msg, 1) != None:
		h_msg = re.sub('ERROR', '[color=FF0000]ERROR[/color]', escape2_msg, 1)
		return h_msg
	elif re.search('CRITICAL', msg, 1) != None:
		h_msg = re.sub('CRITICAL', '[color=FF0000]CRITICAL[/color]', escape2_msg, 1)
		return h_msg
	elif re.search('TRACE', msg, 1) != None:
		h_msg = re.sub('TRACE', '[color=0000FF]TRACE[/color]', escape2_msg, 1)
		return h_msg
	elif re.search('DEBUG', msg, 1) != None:
		h_msg = re.sub('DEBUG', '[color=0000FF]DEBUG[/color]', escape2_msg, 1)
		return h_msg
 
	else:
		return msg


def update_rect(instance, value):
	instance.rect.pos = instance.pos
	instance.rect.size = instance.size
	

def show_msg_label(self, msg, layout, color):
	h_msg = highlight_KvLog(msg)
	
	lbl = Label(text=h_msg, size_hint_y=None, width=Window.width, text_size=(Window.width, None), markup=True)
	lbl.texture_update()
	lbl.size = lbl.texture_size

	with lbl.canvas.before:
		Color(*color)
		lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
		lbl.bind(pos=update_rect, size=update_rect) # update position of label in layout.

	layout.add_widget(lbl)		


def show_msg_button(self, msg, layout, color, action_func):
	
	btn = Button(text=msg, size_hint_y=None, width=Window.width, line_height = 2.0 if Window.width > Window.height else 1, text_size=(Window.width, None), markup=True)
	btn.texture_update()
	btn.size = btn.texture_size
	btn.bind(on_release = action_func)
	
	with btn.canvas.before:
		Color(*color)
		btn.rect = Rectangle(pos=btn.pos, size=btn.size)
		btn.bind(pos=update_rect, size=update_rect)
	
	layout.add_widget(btn)		


class KvLogWidget(ScrollView):
	layout = ObjectProperty(None)

	def __init__(self, **kwargs):
		self.size_hint=(1, None)
		self.size=(Window.width, Window.height)
		super(KvLogWidget, self).__init__(**kwargs)

	def show_log_data(self, msg, layout):
		show_msg_label(self, msg, layout, [0.3,0.4,0.2])

	def show_logger(self, source):
		global current_log
		if self.layout:
			self.remove_widget(self.layout)
		self.layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		self.layout.bind(minimum_height=self.layout.setter('height'))
		for msg in source:
			if msg == None:
				Logger.warning("KvLog: previous log file not be found, using history log.")
				current_log = 'history'
				break

			self.show_log_data(msg, self.layout)

		if current_log == 'history':
			for msg in log_from_history():
				self.show_log_data(msg, self.layout)
			
		self.add_widget(self.layout)


class KvLogFileWidget(ScrollView):
	layout = ObjectProperty(None)

	def __init__(self, **kwargs):
		self.size_hint=(1, None)
		self.size=(Window.width, Window.height)
		super(KvLogFileWidget, self).__init__(**kwargs)

	def show_file_name(self, msg, layout):
		show_msg_button(self, msg, layout, (0.8,0.2,0.6), self.show_choosed_file)

	def show_files(self):
		if self.layout:
			self.remove_widget(self.layout)
		self.layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		self.layout.bind(minimum_height=self.layout.setter('height'))
		for t in range(len(timekeys)):
			self.show_file_name(files[timekeys[t]],self.layout)

		self.add_widget(self.layout)

	def show_choosed_file(self, choosed):
		global current_log
		current_log = choosed.text
		self.parent.parent.transition.direction = 'right'
		self.parent.parent.logscreen.log.show_logger(log_from_choosed(choosed.text))
		self.parent.parent.current = 'log'
		

class LogScreen(Screen):
	touch_pos = (0,0)
	def __init__(self, **kwargs):
		super(LogScreen, self).__init__(**kwargs)
		self.log = KvLogWidget()
		self.add_widget(self.log)
		self.size_hint=(1, None)

	def on_touch_down(self, touch):
		self.touch_pos = touch.pos
		super(LogScreen, self).on_touch_down(touch)

	def on_touch_up(self, touch):
		super(LogScreen, self).on_touch_up(touch)
		if (self.touch_pos[0] - 250) > touch.pos[0]:
			self.parent.transition.direction = 'left'
			self.parent.current = 'files'


class FilesScreen(Screen):
	touch_pos = (0,0)
	def __init__(self, **kwargs):
		super(FilesScreen, self).__init__(**kwargs)
		self.logfiles = KvLogFileWidget()
		self.add_widget(self.logfiles)
		self.size_hint=(1, None)

	def on_touch_down(self, touch):
		self.touch_pos = touch.pos
		super(FilesScreen, self).on_touch_down(touch)

	def on_touch_up(self, touch):
		super(FilesScreen, self).on_touch_up(touch)
		if self.touch_pos[0] < (touch.pos[0] - 250):
			self.parent.transition.direction = 'right'
			self.parent.current = 'log'


class KvLogScreenManager(ScreenManager):
	def __init__(self, **kwargs):
		super(KvLogScreenManager, self).__init__(**kwargs)
		self.logscreen = LogScreen(name='log')
		self.add_widget(self.logscreen)
		self.logscreen.log.show_logger(log_from_previous())
		self.filesscreen = FilesScreen(name='files')
		self.add_widget(self.filesscreen)
		self.current = 'log'
		self.filesscreen.logfiles.show_files()


class KvLogApp(App):
	rota = 0

	def build(self):
		self.sm = KvLogScreenManager()
		return self.sm

	def on_start(self):
		if platform == 'android' or platform == 'ios':
			accelerometer.enable()
			Clock.schedule_interval(self.check_rotation, 1 / 20.)

	def check_rotation(self, dt):
		global current_log
		val = accelerometer.acceleration
		new_rota = self.rota
		if val[0] is not None:
			if val[0] > 6 and abs(val[1]) < 2 :
				new_rota = 270
			elif val[0] < -6 and abs(val[1]) < 2 :
				new_rota = 90
			elif abs(val[0]) < 2 and val[1] > 6 :
				new_rota = 0
			elif abs(val[0]) < 2 and val[1] < -6 :
				new_rota = 180
			
			if new_rota is not self.rota:
				Clock.unschedule(self.check_rotation)
				old_current_screen = self.sm.current

				self.rota = new_rota
				Window.rotation = new_rota

				self.sm.remove_widget(self.sm.logscreen)
				self.sm.logscreen = LogScreen(name='log')
				self.sm.add_widget(self.sm.logscreen)
				self.sm.remove_widget(self.sm.filesscreen)
				self.sm.filesscreen = FilesScreen(name='files')
				self.sm.add_widget(self.sm.filesscreen)

				if current_log is 'history': 
					self.sm.logscreen.log.show_logger(log_from_history())
				elif current_log is not '':
					self.sm.logscreen.log.show_logger(log_from_choosed(current_log))

				self.sm.filesscreen.logfiles.show_files()

				self.sm.current = old_current_screen

				Clock.schedule_interval(self.check_rotation, 1 / 10.)
			
	
			


if __name__ == "__main__":
	#Window.fullscreen='auto'
	KvLogApp().run()
