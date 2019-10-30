# python people_counter.py 
# import the necessary packages
from pyimagesearch.centroidtracker import CentroidTracker
from pyimagesearch.trackableobject import TrackableObject
from object_detector_count import ObjectDetector
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import pickle

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", type=str,default="./videos/finalvideo/crosswalk03.mp4",
	help="path to optional input video file")
ap.add_argument("-c", "--confidence", type=float, default=0.4,
	help="minimum probability to filter weak detections")
ap.add_argument("-s", "--skip-frames", type=int, default=2,
	help="# of skip frames between detections")
ap.add_argument("-t", "--tracker", type=str, default="kcf",
	help="OpenCV object tracker type")
ap.add_argument("-o", "--output", type=str, default="./videos/output/finall_olddd.mp4",
	help="path to optional output video file")
args = vars(ap.parse_args())

#비디오 영상 불러올 때
print("[INFO] opening video file...")
vs = cv2.VideoCapture(args["input"])

writer = None

# initialize the video writer (we'll instantiate later if need be)
W = None
H = None

countID = 0

ct = CentroidTracker(maxDisappeared=100, maxDistance=50)
od= ObjectDetector()
trackers = []
trackableObjects = {}

# initialize the total number of frames processed thus far
totalFrames = 0

#pickle_list for UI
list_dot_count = []

# start the frames per second throughput estimator
fps = FPS().start()

# loop over frames from the video stream
while True:
	frame = vs.read()
	frame = frame[1] if args.get("input", False) else frame
	frame = cv2.resize(frame, (1300,750))

	if args["input"] is not None and frame is None:
		break

	#frame = imutils.resize(frame, width=500)
	rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

	# (H, W) 초기화
	#if W is None or H is None:
	#	(H, W) = frame.shape[:2]

	# if we are supposed to be writing a video to disk, initialize
	# the writer
	if args["output"] is not None and writer is None:
		fourcc = cv2.VideoWriter_fourcc(*"mp4v")
		writer = cv2.VideoWriter(args["output"], fourcc, 30,(1300, 750), True)
	
	#영상에 영역박스치기
	#frame = cv2.rectangle(frame,(120,300),(1250,700),(0,255,0),3)


	#대기 상태
	status = "Waiting"
	rects = []

	# 102~250 프레임에서 사람들이 건너면서 trackingID 초기화 시켜주기
	if (2450<totalFrames<3930) or (totalFrames>7540):

		print("***************totalFrames:",totalFrames)
		print("reset!!!!!!!!!!!!!!!!")
		ct.reset()

		var_dot_count = 0
		list_dot_count.append(var_dot_count)	
		print("list_dot_count : {}".format(list_dot_count))

		with open('finall_olddd.pickle', 'wb') as f:
			pickle.dump(list_dot_count, f, pickle.HIGHEST_PROTOCOL)

	
		#cv2.putText(frame, "Count old people : ", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
		#cv2.putText(frame, str(countID), (750, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
			
		if writer is not None:
			writer.write(frame)

		# show the output frame
		cv2.imshow("Frame", frame)
		key = cv2.waitKey(1) & 0xFF

		# increment the total number of frames processed thus far and
		# then update the FPS counter
		totalFrames += 1
		fps.update()

		continue	
	
	#30프레임 당 물체 검출,totalFrames이 0,30,60,90...(skip_frames=30)
	if totalFrames % args["skip_frames"] == 0:
		status = "Detecting"
		trackers = []

		print("***************totalFrames:",totalFrames)
		print("Detecting")
		#박스치기
		frame = od.detect_objects(frame,1300,750)
		frame = od.object_boxdraw(frame)
		frame, old_people , dot_count = od.count_inbox(frame)

		
		for i in range(dot_count):
			box = old_people[i]*np.array([1,1,1,1])
			(startX, startY, endX, endY) = box.astype("int")
			#박스친객체tracker.....
			tracker = dlib.correlation_tracker()
			rect = dlib.rectangle(startX, startY, endX, endY)
			tracker.start_track(rgb, rect)
			# add the tracker to our list of trackers
			trackers.append(tracker)
			print(i,"번째 (startX, startY, endX, endY):",startX, startY, endX, endY)

	else:
		print("***************totalFrames:",totalFrames)
		print("Tracking")
		#rects에 좌표대입
		#trackers에 있는 객체들 트래킹..
		'''
		for tracker in trackers:
			
			status = "Tracking"

			#print("totalFrames : ",totalFrames)
			#print("tracker:",tracker)
			# update the tracker
			tracker.update(rgb)
			pos = tracker.get_position()

			startX = int(pos.left())
			startY = int(pos.top())
			endX = int(pos.right())
			endY = int(pos.bottom())
			print("(startX, startY, endX, endY) : ",startX, startY, endX, endY)
			#frame = cv2.rectangle(frame,(startX,startY),(endX,endY),(0,0,255),3)
			
			# 트래킹을 하는 프레임마다 객체의 죄표를 구함
			rects.append((startX, startY, endX, endY))
			'''
			##여기서부터
		trackers = []

		print("***************totalFrames:",totalFrames)
		print("Detecting")
		#박스치기
		frame = od.detect_objects(frame,1300,750)
		frame = od.object_boxdraw(frame)
		frame, old_people , dot_count = od.count_inbox(frame)

		
		for i in range(dot_count):
			box = old_people[i]*np.array([1,1,1,1])
			(startX, startY, endX, endY) = box.astype("int")
			#박스친객체tracker.....
			tracker = dlib.correlation_tracker()
			rect = dlib.rectangle(startX, startY, endX, endY)
			tracker.start_track(rgb, rect)
			# add the tracker to our list of trackers
			trackers.append(tracker)
			print(i,"번째 (startX, startY, endX, endY):",startX, startY, endX, endY)

		##여기꺼지 삭제

	var_dot_count = dot_count
	list_dot_count.append(var_dot_count)	
	print("list_dot_count : {}".format(list_dot_count))

	with open('finall_olddd.pickle', 'wb') as f:
		pickle.dump(list_dot_count, f, pickle.HIGHEST_PROTOCOL)

	#객체를 새로 등록하고 없애는 클래스임...
	objects , disappeared , countDetectframe ,countIDframe = ct.update(rects)
	#objectID생성 후 몇 프레임이나 존재하는지 카운트
	ct.CountIDframe()

	# loop over the tracked objects
	for (objectID, centroid) in objects.items():
		#현재 objectID에 대한 centroid가져옴
		to = trackableObjects.get(objectID, None)

		# TrackableObject에 ID가 저장이 안되어있으면 새로 만듬
		if to is None:
			to = TrackableObject(objectID, centroid)
		trackableObjects[objectID] = to
		print("track_object ",objectID," centroid[0],centroid[1] : " , centroid[0],centroid[1])
		#객체 표시
		text = "ID {}".format(objectID)

		cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
			cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
		cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

	for (objectID, cou) in disappeared.items():
		print("track_object ",objectID," disappearedFrame : " , cou)

	for (objectID, count) in countDetectframe.items():
		print("track_object ",objectID," countDetectframe : " , count)

	for (objectID, counttt) in countIDframe.items():
		print("track_object ",objectID," 몇 프레임이나 검출이 되었는지 카운트 : " , countIDframe[objectID])

	print("countID : ",dot_count)

	#cv2.putText(frame, "Count old people : ", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
	#cv2.putText(frame, str(dot_count), (750, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
	
	'''
	#신호등이 바뀔 때 객체의 검출률에 따라서 객체 삭제... 
	if totalFrames == 101:
		for (objectID, count) in list(countDetectframe.items()):			
			ct.Decision(objectID,count, countIDframe[objectID])
	'''
	if writer is not None:
		writer.write(frame)

	# show the output frame
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
	if key == ord("s"):
		for _ in range(0,60):
		   vs.read()

	# increment the total number of frames processed thus far and
	# then update the FPS counter
	totalFrames += 1
	fps.update()

# stop the timer and display FPS information
fps.stop()
print("finish!!!!!!!!!!!!!!!!!!!")
#print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
#print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

if writer is not None:
	writer.release()

if not args.get("input", False):
	vs.stop()
else:
	vs.release()

cv2.destroyAllWindows()