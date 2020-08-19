from telepot import Bot
import os
from time import sleep
import json
from threading import Thread
from telepot.loop import MessageLoop
from telepot import Bot
from random import random
from cv2 import cv2
from tempfile import gettempdir

from MotionDetector import MotionDetector

class Main:
	def __init__(self):
		with open('config.json') as f:
			self.config = json.load(f)

		self.threads = []
		self.detectors = []
		self.bot = Bot(self.config['bot_token'])


	def start_monitoring(self):
		# create detectors and threads for all cameras
		for camera in self.config['cameras']:
			sm = MotionDetector(camera, self.send_video_to_recipients)
			self.detectors.append(sm)
			self.threads.append(Thread(target=sm.start))
		
		# start all threads
		for t in self.threads:
			t.start()

		self.set_state(True)
		
	def stop_monitoring(self):
		# stop all detectors
		for m in self.detectors:
			m.stop()


		# join all threads
		for t in self.threads:
			t.join()
		
		# discard objects
		self.detectors = []
		self.threads = []

		self.set_state(False)

	def send_video_to_recipients(self, frames):
		name = os.path.join(gettempdir(), f'{random()}.mp4')
		height, width, _ = frames[0].shape
		vid = cv2.VideoWriter(name, cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (width, height))
		for frame in frames:
			vid.write(frame)
		vid.release()
		self.bot.sendVideo(self.config['chat_id'], open(name, 'rb'))

	def set_state(self, state):
		self.config['started'] = state
		with open('config.json', 'w') as f:
			json.dump(self.config, f, indent=2)

	def is_started(self):
		return self.config['started']

	def reply(self, msg, text):
		self.bot.sendMessage(msg['chat']['id'], text, reply_to_message_id=msg['message_id'])

	def message_handler(self, msg):
		# check if from authorized user
		if msg['chat']['id'] != self.config['chat_id']:
			self.reply(msg, 'Unauthorized user!')
			return

		# preprocess message
		content = msg['text'].strip().lower()

		# start monitoring
		if content == '/start':
			if self.is_started():
				self.reply(msg, 'Already started!')
				return
			self.start_monitoring()
			self.set_state(True)
			self.reply(msg, 'Started!')
		# stop monitoring
		elif content == '/stop':
			if not self.is_started():
				self.reply(msg, 'Already stopped!')
				return
			self.stop_monitoring()
			self.set_state(False)
			self.reply(msg, 'Stopped!')
		elif content == '/status':
			self.reply(msg, 'Started!' if self.is_started() else 'Stopped!')
		# unrecognized
		else:
			self.reply(msg, 'Unrecognized command!')

	def run(self):
		# check if resuming from a started state
		if self.is_started():
			self.start_monitoring()

		# loop for messages
		MessageLoop(self.bot, self.message_handler).run_forever()
		


if __name__ == '__main__':
	Main().run()