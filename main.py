from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger, LoggerHistory, LOG_LEVELS

def log_dump():
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

		layout = GridLayout(cols=1, spacing=2, size_hint_y=None)
		layout.bind(minimum_height=layout.setter('height'))
		for msg in log_dump():
			lbl = Label(text=msg, size_hint_y=None, width=Window.width, text_size=(Window.width, None))
			if len(msg) > 300:
				lbl.shorten = True

			with lbl.canvas.before:
				Color(0.3,0.4,0.2)
				lbl.rect = Rectangle(pos=lbl.pos, size=lbl.size)
				lbl.bind(pos=self.update_rect, size=self.update_rect) # update position of label in layout.

			layout.add_widget(lbl)		

		self.add_widget(layout)

	def update_rect(self, instance, value):
		instance.rect.pos = instance.pos
		instance.rect.size = instance.size


class LogApp(App):
	def build(self):
		return LogWidget()

	def on_start(self):
		pass
		

if __name__ == "__main__":
	LogApp().run()
