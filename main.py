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

import os
import re
import subprocess

files = {}
current_log = ''

def get_log_path():
	if platform == 'linux':
		return os.environ['HOME'] + "/.kivy/logs/"
	elif platform == 'android':
		return os.path.dirname(os.environ['ANDROID_APP_PATH'])
	elif paltform == 'ios' or platform == 'macosx':
		return os.environ['HOME'] + "/Documents/.kivy/logs/"
	else:
		return None
	
def get_log_files(log_folder):
	#Logger.info("K: " + log_folder)
	if os.path.isdir(log_folder):
		for log_file in os.listdir(log_folder):
			files[os.stat(log_folder+log_file).st_mtime] = log_folder+log_file
			#Logger.info("K: file= " + log_folder+log_file)

def get_previous_logfile():
	path = get_log_path()
	#Logger.info("K: path= " + path)
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
		Logger.info("KivyLogger: dumping "  + file_to_dump)
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


class LogWidget(ScrollView):
	def __init__(self, **kwargs):
		self.size_hint=(1, None)
		self.size=(Window.width, Window.height)
		super(LogWidget, self).__init__(**kwargs)


	def update_rect(self, instance, value):
		instance.rect.pos = instance.pos
		instance.rect.size = instance.size


class KivyLoggerApp(App):

	def build(self):
		return LogWidget()

	def on_start(self):
		self.show_logger()

	def show_msg(self, msg, layout):
		lbl = Label(text=msg, size_hint_y=None, width=Window.width, text_size=(Window.width, None))
		if len(msg) > 300:
			lbl.shorten = True

		with lbl.canvas.before:
			Color(0.3,0.4,0.2)
			lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
			lbl.bind(pos=self.root.update_rect, size=self.root.update_rect) # update position of label in layout.

		layout.add_widget(lbl)		

		
		
	def show_logger(self):
		global current_log
		layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		layout.bind(minimum_height=layout.setter('height'))
		for msg in log_from_previous():
			if msg == None:
				Logger.warning("KivyLogger: previous log file not be found, using history log.")
				current_log = 'history'
				break

			self.show_msg(msg, layout)


		if current_log == 'history':
			for msg in log_from_history():
				self.show_msg(msg, layout)
			

		self.root.add_widget(layout)


if __name__ == "__main__":
	KivyLoggerApp().run()
