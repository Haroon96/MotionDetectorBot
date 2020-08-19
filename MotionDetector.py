
import imutils
from cv2 import cv2

class MotionDetector:
	def __init__(self, src, handler):
		self.src = src
		self.handler = handler
		self._stop = False

	def get_frame(self, video):
		_, frame = video.read()
		if frame is not None:
			frame = imutils.resize(frame, width=500)
		return frame

	def preprocess(self, frame):
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		return cv2.GaussianBlur(gray, (21, 21), 0)

	def detect_contours(self, frame, firstFrame):
		gray = self.preprocess(frame)
		frameDelta = cv2.absdiff(firstFrame, gray)
		thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
		thresh = cv2.dilate(thresh, None, iterations=2)
		cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		return imutils.grab_contours(cnts)

	def detect_motion(self, frame, firstFrame):
		# find contours in the frame (changes from the firstFrame)
		contours = self.detect_contours(frame, firstFrame)

		motion = False

		# for each contour, check if it is larger than specified
		for c in contours:
			# contour too small, discard
			if cv2.contourArea(c) < 15000:
				continue

			# motion detected!!!
			motion = True

			# draw boundingRectangle
			(x, y, w, h) = cv2.boundingRect(c)
			
			# skip jitters
			fh, fw, _ = frame.shape
			if w == fw and h == fh:
				print("Grey out")
				continue

			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

		return motion
		

	def stop(self):
		self._stop = True

	def start(self):
		# open video capture
		video = cv2.VideoCapture(self.src)
		firstFrame = None
		
		# discard first few frames
		for _ in range(25):
			self.get_frame(video)

		# while instructed to run
		while not self._stop:
			
			frame = self.get_frame(video)

			if frame is None:
				continue
			
			# save firstFrame for comparison
			if firstFrame is None:
				firstFrame = self.preprocess(frame)
				continue    
			
			# check for motion
			motion = self.detect_motion(frame, firstFrame)

			# if motion not detected, continue
			if not motion:
				continue

			# if motion detected, record the next frames and call handler
			recording = [frame]
			for _ in range(300):
				# get next frame
				frame = self.get_frame(video)
				if frame is not None:
					# mark motion
					self.detect_motion(frame, firstFrame)
					# add to recording
					recording.append(frame)
				
			# handle the recorded frames
			self.handler(recording)
