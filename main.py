from kivy.config import Config
#Config.set('graphics','width','400')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger, LoggerHistory, LOG_LEVELS
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen

import os
import re

files = {}
timekeys=[]
current_log = ''


def get_log_path():
	if platform == 'linux':
		return os.environ['HOME'] + "/.kivy/logs/"
	elif platform == 'android':
		return os.path.dirname(os.environ['ANDROID_APP_PATH'])
	elif paltform == 'ios' or platform == 'macosx': #not yet test~
		return os.environ['HOME'] + "/Documents/.kivy/logs/"
	else:
		return None

	
def get_log_files(log_folder):
	if os.path.isdir(log_folder):
		for log_file in os.listdir(log_folder):
			files[os.stat(log_folder+log_file).st_mtime] = log_folder+log_file


def get_previous_logfile():
	global timekeys
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
		timekeys.sort()
		timekeys.reverse()
		file_to_dump = files[timekeys[1]] if nfiles > 1 else files[timekeys[0]]
		Logger.info("KvLog: dumping "  + file_to_dump)
		current_log = file_to_dump
		return file_to_dump
	else:
		return None


def log_from_previous():
	dump_file= get_previous_logfile()
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
	

def show_msg(self, msg, layout, color):
	h_msg = highlight_KvLog(msg)
	
	lbl = Label(text=h_msg, size_hint_y=None, width=Window.width, text_size=(Window.width, None), markup=True)
	lbl.texture_update()
	lbl.size = lbl.texture_size
	#if len(msg) > 300:
	#	lbl.shorten = True

	with lbl.canvas.before:
		Color(*color)
		lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
		lbl.bind(pos=update_rect, size=update_rect) # update position of label in layout.

	layout.add_widget(lbl)		


class KvLogWidget(ScrollView):
	def __init__(self, **kwargs):
		self.size_hint=(1, None)
		self.size=(Window.width, Window.height)
		super(KvLogWidget, self).__init__(**kwargs)

	def show_log_data(self, msg, layout):
		show_msg(self, msg, layout, [0.3,0.4,0.2])

	def show_logger(self):
		global current_log
		layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		layout.bind(minimum_height=layout.setter('height'))
		for msg in log_from_previous():
			if msg == None:
				Logger.warning("KvLog: previous log file not be found, using history log.")
				current_log = 'history'
				break

			self.show_log_data(msg, layout)

		if current_log == 'history':
			for msg in log_from_history():
				self.show_log_data(msg, layout)
			
		self.add_widget(layout)


class KvLogFileWidget(ScrollView):
	def __init__(self, **kwargs):
		self.size_hint=(1, None)
		self.size=(Window.width, Window.height)
		super(KvLogFileWidget, self).__init__(**kwargs)

	def show_file_name(self, msg, layout):
		show_msg(self, msg, layout, (0.8,0.2,0.6))

	def show_files(self):
		layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		layout.bind(minimum_height=layout.setter('height'))
		for t in range(len(timekeys)):
			self.show_file_name(files[timekeys[t]],layout)

		self.add_widget(layout)
	



class LogScreen(Screen):
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
		if (self.touch_pos[0] - 20) > touch.pos[0]:
			self.parent.transition.direction = 'left'
			self.parent.current = 'files'


class FilesScreen(Screen):
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
		if self.touch_pos[0] < (touch.pos[0] - 20):
			self.parent.transition.direction = 'right'
			self.parent.current = 'log'


class KvLogScreenManager(ScreenManager):
	def __init__(self, **kwargs):
		super(KvLogScreenManager, self).__init__(**kwargs)
		self.logscreen = LogScreen(name='log')
		self.add_widget(self.logscreen)
		self.logscreen.log.show_logger()
		self.filesscreen = FilesScreen(name='files')
		self.add_widget(self.filesscreen)
		self.current = 'log'
		self.filesscreen.logfiles.show_files()


class KvLogApp(App):
	def build(self):
		return KvLogScreenManager()

	def on_start(self):
		pass


if __name__ == "__main__":
	KvLogApp().run()
