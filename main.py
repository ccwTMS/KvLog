from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger, LoggerHistory, LOG_LEVELS

import re
import subprocess


def get_log_path():
	log_len = len(LoggerHistory.history)
	LoggerHistory.history.reverse()
	for i in range(log_len):
		msg = LoggerHistory.history[i].getMessage()
		ret = re.search('Record log in', msg)
		print ret
		if ret == None:
			continue
		else:
			path = msg.split(' ')[-1].split('kivy_')[0]
			return path
	return None
	

def get_previous_logfile():
	path = get_log_path()
	if path != None:
		cmd = "ls -t " + path
		try:
			ret = subprocess.Popen(cmd , stdout=subprocess.PIPE, shell=True)
			(output, error) = ret.communicate()
			if error == None:
				files = output.split("\n")
				print(error)
				return (path, files[1])
		except OSError:
			Logger.error("KivyLogger: run %s failed\n" % cmd)
			return (None, None)
	return (None, None)
	

def log_from_previous():
	(path, target) = get_previous_logfile()
	if target != None:
		f = open(path + target)
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


class LogApp(App):
	log_from = 'privious'

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
		layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		layout.bind(minimum_height=layout.setter('height'))
		for msg in log_from_previous():
			if msg == None:
				self.log_from = 'history'
				break

			self.show_msg(msg, layout)


		if self.log_from == 'history':
			for msg in log_from_history():
				self.show_msg(msg, layout)
			

		self.root.add_widget(layout)


if __name__ == "__main__":
	LogApp().run()
