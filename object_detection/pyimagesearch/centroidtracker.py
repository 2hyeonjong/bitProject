# import the necessary packages
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np

class CentroidTracker:
	def __init__(self, maxDisappeared=100, maxDistance=50):
		self.nextObjectID = 0  
		self.objects = OrderedDict()  
		self.disappeared = OrderedDict()#손실된 프레임 수
		self.maxDisappeared = maxDisappeared#손실된 프레임의 수의 제한 수
		self.maxDistance = maxDistance#최대 떨어진 거리
		self.countDetectframe = OrderedDict()#객체 검출한 횟수
		self.countIDframe = OrderedDict()#트래킹 한 이후의 프레임

	#objectID 등록
	def register(self, centroid): 
		self.objects[self.nextObjectID] = centroid
		self.disappeared[self.nextObjectID] = 0
		self.countDetectframe[self.nextObjectID] = 1
		self.countIDframe[self.nextObjectID] = 0
		self.nextObjectID += 1
		
	#objectID 삭제
	def deregister(self, objectID):
		del self.objects[objectID]
		del self.disappeared[objectID]
		del self.countDetectframe[objectID]
		del self.countIDframe[objectID]

	#이전 objectID 초기화
	def reset(self):
		for objectID in list(self.objects.keys()):
			self.deregister(objectID)
		self.nextObjectID = 0

	#objectID생성 후 몇 프레임이나 존재하는지 카운트
	def CountIDframe(self,):
		for objectID in list(self.objects.keys()):
			self.countIDframe[objectID] += 1

	#신호등이 바뀔 때 객체의 검출률에 따라서 객체 삭제... 
	def Decision(self,objectID,countDET,countID):
		print("for!!!!!!!!!!!!!!!")
		print("삭제 할 후보 ",objectID,":",countDET,"<",countID/10,"하면 삭제합니다")
		if countDET<(countID/10):
			print("if!!!!!!!!!!!!!!!")
			print("track_object ",objectID)
			self.deregister(objectID)
	
	#objectID 새로 업데이트
	def update(self, rects):
		if len(rects) == 0:
			#객체가 아무것도 검출이 안됬으면
            #모든 객체의 손실 프레임의 수를 증가
			for objectID in list(self.disappeared.keys()):
				self.disappeared[objectID] += 1
                #손실 프레임의 수가 한계에 다다르고, 객체검출 한 프레임수가 33보다 적으면 아이디 삭제
				if (self.disappeared[objectID] > self.maxDisappeared): # and (self.countDetectframe[objectID] < self.maxDisappeared/3):
					self.deregister(objectID)

			return self.objects ,self.disappeared , self.countDetectframe , self.countIDframe

		#초기화
		inputCentroids = np.zeros((len(rects), 2), dtype="int")

        #각 객체의 중심점을 구함
		for (i, (startX, startY, endX, endY)) in enumerate(rects):
			cX = int((startX + endX) / 2.0)
			cY = int((startY + endY) / 2.0)
			inputCentroids[i] = (cX, cY)

        #지금 당장 트래킹할 대상이 없으면 새로 등록
		if len(self.objects) == 0:
			for i in range(0, len(inputCentroids)):
				self.register(inputCentroids[i])
		else:
			##아이디가 키,중심점이 값인 디렉토리 생성
			objectIDs = list(self.objects.keys())
			objectCentroids = list(self.objects.values())
            #기존 객체 중심과 새로운 입력 중심의 각 쌍 사이의 거리를 계산
			D = dist.cdist(np.array(objectCentroids), inputCentroids)
            #최소거리인 값을 구함
            #D의 (row,col)의 값이 objectCentroids에게서
            #가장 작은 값인 inputCentroids의 인덱스값            
			rows = D.min(axis=1).argsort() 
			cols = D.argmin(axis=1)[rows] 
            #usedRows,usedCols초기화
			usedRows = set()
			usedCols = set()
			for (row, col) in zip(rows, cols):
                #이미 사용하고 있는 점 무시
				if row in usedRows or col in usedCols:
					continue
                #두 점 사이의 거리값이 한계를 넘으면 무시
				if D[row, col] > self.maxDistance:
					continue
                #새로운 점으로 지정
				objectID = objectIDs[row]
				self.objects[objectID] = inputCentroids[col]
				self.disappeared[objectID] = 0
                #사용한 점이라고 추가
				usedRows.add(row)
				usedCols.add(col)
            #사용하지않은 점들은 따로 저장
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            #객체 중심의 수가 입력 중심의 수보다 크거나 같으면 
			if D.shape[0] >= D.shape[1]:
                #사용하지 않은 값에서 객체의 손실 프레임 증가
				for row in unusedRows:
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1
                    #손실 프레임의 수가 한계에 다다르고, 객체검출 한 프레임수가 33보다 적으면 아이디 삭제
					if (self.disappeared[objectID] > self.maxDisappeared): # and (self.countDetectframe[objectID] < self.maxDisappeared/3):
						self.deregister(objectID)
            # 입력 중심의 수가 기존 객체 중심의 수보다 많으므로 새 객체 등록
			else:
				for col in unusedCols:
					self.register(inputCentroids[col])

			print("usedRows : ",usedRows)
			print("unusedRows : ",unusedRows)

			#객체 검출한 횟수 카운트
			for row in usedRows:
				objectID = objectIDs[row]
				self.countDetectframe[objectID] += 1

		return self.objects ,self.disappeared , self.countDetectframe , self.countIDframe






