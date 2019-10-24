import time
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import cv2  
import pickle
from PyQt5 import uic
from threading import Timer, Thread

class VideoBox(QtWidgets.QWidget):
    VIDEO_TYPE_OFFLINE = 0
    VIDEO_TYPE_REAL_TIME = 1
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2
    video_url = ""
    
    def __init__(self, video_url="", video_type=VIDEO_TYPE_OFFLINE, auto_play=False):
        QtWidgets.QWidget.__init__(self)
        self.setGeometry(0, 0, 1500, 1000)
        self.display = QtWidgets.QLabel()
        self.display.setStyleSheet("font: 36pt \"Sans Serif\"; qproperty-alignment: AlignCenter;")
        self.video_url = video_url
        self.video_type = video_type  # 0: offline  1: realTime
        self.auto_play = auto_play
        self.status = self.STATUS_INIT  # 0: init 1:playing 2: pause
        self.greenLight = 100
        self.redLight =250
        self.pictureLabel = QtWidgets.QLabel()
        init_image = QtGui.QPixmap("./main.PNG").scaled(1300, 750)
        self.pictureLabel.setPixmap(init_image)
        #self.position = 0

        self.playButton = QtWidgets.QPushButton()
        self.playButton.setEnabled(True)
        self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.switch_video)

        self.Vtimer = VideoTimer()
        self.old_counter = QtWidgets.QTextBrowser()
        self.old_counter.setStyleSheet('font: 36pt "Sans Serif";')
        self.Vtimer.signalFor_dataFor_normal.connect(self._print_dataFor_normal)
        self.Vtimer.signalFor_dataFor_old.connect(self._print_dataFor_old)

        self.verticalLayoutWidget = QtWidgets.QWidget()
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.red_light = QtWidgets.QFrame(self.verticalLayoutWidget)
        self.red_light.setStyleSheet("background-color: rgb({}, 0, 0);".format(self.redLight))
        self.Vtimer.signalFor_light.connect(self._light)
        self.red_light.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.red_light.setFrameShadow(QtWidgets.QFrame.Raised)
        self.red_light.setObjectName("red_light")

        self.verticalLayout.addWidget(self.red_light)

        self.green_light = QtWidgets.QFrame(self.verticalLayoutWidget)
        self.green_light.setStyleSheet("background-color: rgb(0, {}, 0);".format(self.greenLight))
        self.green_light.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.green_light.setFrameShadow(QtWidgets.QFrame.Raised)
        self.green_light.setObjectName("green_light")

        self.verticalLayout.addWidget(self.green_light)
        
        ###lcd for countdown
        self.lcdNumber = QtWidgets.QLCDNumber(self.verticalLayoutWidget)
        self.lcdNumber.setObjectName("lcdNumber")
        self.lcdNumber.setDigitCount(2)
        self.lcdNumber.display(0)
        self.Vtimer.signalFor_countdown.connect(self._count_down)
        self.verticalLayout.addWidget(self.lcdNumber)

        self._slider = QtWidgets.QSlider(self)
        self.Vtimer.SignalFor_totalFrame.connect(self._get_totalFrame)
        self._slider.setContentsMargins(0, 0, 0, 0)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self.label = QtWidgets.QLabel('00:00')
       
        self._slider.valueChanged.connect(self.slider_moved) 
        self._slider.setObjectName("slider")
        #self.Vtimer.SignalFor_frame.connect(self.slider_moved)
        self._slider.sliderReleased.connect(self.changed_slider)

        _trafficSign_layout = QtWidgets.QHBoxLayout()
        _trafficSign_layout.setContentsMargins(0, 0, 0, 0)
        _trafficSign_layout.addWidget(self.verticalLayoutWidget)
        _trafficSign_layout.setStretch(0, 2)
        _trafficSign_layout.setStretch(1, 2)
        _trafficSign_layout.setStretch(2, 1)
        _oldCounter = QtWidgets.QHBoxLayout()
        _oldCounter.setContentsMargins(0,0,0,0)
        _oldCounter.addWidget(self.display)

        _videoFrame_layout = QtWidgets.QVBoxLayout()
        _controller_layout = QtWidgets.QHBoxLayout()
        _controller_layout.setContentsMargins(0,0,0,0)
        _controller_layout.addWidget(self.playButton)
        _controller_layout.addWidget(self._slider)
        _controller_layout.addWidget(self.label)

        _buttonForVideo = QtWidgets.QHBoxLayout()
        self._buttonForNormal = QtWidgets.QPushButton("Normal")
        self._buttonForOld = QtWidgets.QPushButton("Old")
        self._buttonForNormal.clicked.connect(self.openNormal)
        self._buttonForOld.clicked.connect(self.openOld)    
        _buttonForVideo.addWidget(self._buttonForNormal)
        _buttonForVideo.addWidget(self._buttonForOld)
        _videoFrame_layout.setContentsMargins(0, 0, 0, 0)
        _videoFrame_layout.addWidget(self.pictureLabel)
        _videoFrame_layout.addLayout(_controller_layout)
        _videoFrame_layout.addWidget(self.display)
        _videoFrame_layout.addLayout(_buttonForVideo)
        _videoFrame_layout.setStretch(0, 15)
        _videoFrame_layout.setStretch(1, 1)
        _videoFrame_layout.setStretch(2, 5)
        _videoFrame_layout.setStretch(3,1)
        
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(_trafficSign_layout)
        layout.addLayout(_videoFrame_layout)
        
        self.setLayout(layout)

        # timer 
        #self.timer = VideoTimer()
        self.Vtimer.timeSignal.signal[str].connect(self.show_video_images)

        # video
        self.playCapture = cv2.VideoCapture()
        if self.video_url != "":
            self.set_timer_fps()
            if self.auto_play:
                self.switch_video()
            # self.videoWriter = VideoWriter('*.mp4', VideoWriter_fourcc('M', 'J', 'P', 'G'), self.fps, size)
            
    #@QtCore.pyqtSlot(int)
    @QtCore.pyqtSlot(int)
    def slider_moved(self ,position):
        _min = 0
        _sec = int(position/30)
        if _sec >61:
            _sec = 0
            _min +=1
        self.label.setText('%02d:%02d' %(_min ,_sec))
    def openNormal(self):
        self.set_video("/home/bit205/Desktop/models/research/object_detection/output/20191016_131747.avi", VideoBox.VIDEO_TYPE_OFFLINE, False)
        self.Vtimer.i =0
        self.Vtimer.frame =0

    def openOld(self):
        self.set_video("/home/bit205/Desktop/models/research/object_detection/output/20191016_132747.avi", VideoBox.VIDEO_TYPE_OFFLINE, False)
        self.Vtimer.i =0
        self.Vtimer.frame =0

    @QtCore.pyqtSlot(int)
    def _print_dataFor_normal(self,number):
        self.number = number
        self.display.setText('The number of the elderly : {}'.format(self.number))

    @QtCore.pyqtSlot(int)
    def _print_dataFor_old(self,number):
        self.number = number
        self.display.setText('The number of the elderly : {}'.format(self.number))
    '''
    @QtCore.pyqtSlot(int)
    def _count_down(self,count):
        if self.greenLight != 255:
            self.lcdNumber.display(0)
        else :
            self.lcdNumber.display(count)   
    '''
    @QtCore.pyqtSlot(int,int)
    def _light(self,frame,result):  
        change_light = 2297
        #if result > 0:
        self.frame = frame
        green_time = (30*40) +change_light
        if  change_light< frame < green_time:
            self.red_light.setStyleSheet("background-color: rgb({}, 0, 0);".format(100))
            self.green_light.setStyleSheet("background-color: rgb(0, {}, 0);".format(255))
            self.greenLight =255

        else :
            self.red_light.setStyleSheet("background-color: rgb({}, 0, 0);".format(255))
            self.green_light.setStyleSheet("background-color: rgb(0, {}, 0);".format(100))

    @QtCore.pyqtSlot(int)
    def _get_totalFrame(self,totalFrame):
        totalFrame=int(totalFrame)
        self._slider.setRange(0, totalFrame)
        
    def moveFrame(self, moveFrame):
        self.playCapture.set(cv2.CAP_PROP_POS_FRAMES,moveFrame)   

    def reset(self):
        self.Vtimer.stop()
        self.playCapture.release()
        self.status = VideoBox.STATUS_INIT
        self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
    
    def changed_slider(self):
        if self.Vtimer.stopped ==False:
            self.Vtimer.stop
            self.moveFrame(self._slider.value())
            self.Vtimer.frame =self._slider.value()
            self.Vtimer.start
        else:
            self.moveFrame(self._slider.value())


    def set_timer_fps(self):
        self.playCapture.open(self.video_url)
        fps = self.playCapture.get(cv2.CAP_PROP_FPS)
        totalFrame = self.playCapture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.Vtimer.set_fps(fps)
        self.Vtimer.set_frame(totalFrame)
        self.playCapture.release()

    def set_video(self, url, video_type=VIDEO_TYPE_OFFLINE, auto_play=False):
        self.reset()
        self.video_url = url
        self.video_type = video_type
        self.auto_play = auto_play
        self.set_timer_fps()
        if self.auto_play:
            self.switch_video()

    def play(self):
        if self.video_url == "" or self.video_url is None:
            return
        if not self.playCapture.isOpened():
            self.playCapture.open(self.video_url)
        self.Vtimer.start()
        self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.status = VideoBox.STATUS_PLAYING
        # self.Vtimer.stopped=False

    def stop(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.playCapture.isOpened():
            self.Vtimer.stop()
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.status = VideoBox.STATUS_PAUSE

    def re_play(self):
        if self.video_url == "" or self.video_url is None:
            return
        self.playCapture.release()
        self.playCapture.open(self.video_url)
        self.Vtimer.start()
        self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.status = VideoBox.STATUS_PLAYING

    def show_video_images(self):
        if self.playCapture.isOpened():
            success, frame = self.playCapture.read()
            if success:
                height, width = frame.shape[:2]
                if frame.ndim == 3:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                elif frame.ndim == 2:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

                temp_image = QtGui.QImage(rgb.flatten(), width, height, QtGui.QImage.Format_RGB888)
                temp_pixmap = QtGui.QPixmap.fromImage(temp_image)
                self.pictureLabel.setPixmap(temp_pixmap)
            else:
                print("read failed, no frame data")
                success, frame = self.playCapture.read()
                if not success and self.video_type is VideoBox.VIDEO_TYPE_OFFLINE:
                    print("play finished")  
                    self.reset()
                    self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
                return
        else:
            print("open file or capturing device error, init again")
            self.reset()
    def switch_video(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.status is VideoBox.STATUS_INIT:
            self.playCapture.open(self.video_url)
            self.Vtimer.start()
            self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        elif self.status is VideoBox.STATUS_PLAYING:
            self.Vtimer.stop()
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.release()
            self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        elif self.status is VideoBox.STATUS_PAUSE:  
            if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
                self.playCapture.open(self.video_url)
            self.Vtimer.start()
            self.playButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))

        self.status = (VideoBox.STATUS_PLAYING,
                       VideoBox.STATUS_PAUSE,
                       VideoBox.STATUS_PLAYING)[self.status]
class Communicate(QtCore.QObject):

    signal = QtCore.pyqtSignal(str)

class VideoTimer(QtCore.QThread, QtCore.QObject):
    with open('../forNormal.pickle', 'rb') as f:
        dataFor_normal = pickle.load(f)
    with open('../forOld.pickle', 'rb') as f:
        dataFor_old = pickle.load(f)
    signalFor_controlLight =QtCore.pyqtSignal(int,int)
    signalFor_dataFor_normal =QtCore.pyqtSignal(int)
    signalFor_dataFor_old =QtCore.pyqtSignal(int)
    signalFor_countdown =QtCore.pyqtSignal(int)
    signalFor_light = QtCore.pyqtSignal(int,int)
    SignalFor_frame = QtCore.pyqtSignal(int)
    SignalFor_totalFrame = QtCore.pyqtSignal(int)

    def __init__(self, frequent=20):
        QtCore.QThread.__init__(self)
        self.stopped = False
        self.frequent = frequent
        self.timeSignal = Communicate()
        self.mutex = QtCore.QMutex()
        self.flag = True
        self.frame = 0
        self.frameFor_time=42
        self.frameFor_light= 0
        self.i =0
        self.j =0
    def run(self):
        #with QtCore.QMutexLocker(self.mutex):
        self.stopped = False
        self.frame -=1
        while True:
            self.frame +=1
            self.SignalFor_frame.emit(self.frame)  

            if self.stopped == True:
                return
            '''
            if self.frame%30== 0 and self.frame >= 2297:
                self.frameFor_time -= 1
                if self.frameFor_time < 0:
                    self.frameFor_time =0
                self.signalFor_countdown.emit(self.frameFor_time)
            '''            
            self.timeSignal.signal.emit("1")
            time.sleep(1 / self.frequent)

            self.SignalFor_totalFrame.emit(self.totalFrame)
            dataFor_normal = self.dataFor_normal
            dataFor_old = self.dataFor_old
            self.resultFor_normal = dataFor_normal[self.i]
            self.resultFor_old = dataFor_old[self.j]
            if self.i < len(self.dataFor_normal) -1:
                self.i = self.i+1
            if self.j < len(self.dataFor_old) -1:
                self.j = self.j+1
            self.signalFor_dataFor_normal.emit(self.resultFor_normal)
            self.signalFor_dataFor_old.emit(self.resultFor_old)

            self.signalFor_controlLight.emit(self.resultFor_normal, self.frameFor_time)  
            self.signalFor_light.emit(self.frameFor_light,self.resultFor_normal)
            self.frameFor_light +=1
            print(self.frame)
            #print(self.frame)          

    def stop(self):
        #with QtCore.QMutexLocker(self.mutex):
        self.stopped = True

    #def is_stopped(self):
        #with QtCore.QMutexLocker(self.mutex):
    #    return self.stopped

    def set_fps(self, fps):
        self.frequent = fps
    def set_frame(self, totalFrame):
        self.totalFrame = totalFrame
    #def set_movedFrame(self, movedFrame):
    #    self.movedFrame = movedFrame
          

if __name__ == "__main__":
    mapp = QtWidgets.QApplication(sys.argv)
    mw = VideoBox()
    mw.set_video("/home/bit205/Desktop/models/research/object_detection/output/20191016_131747.avi", VideoBox.VIDEO_TYPE_OFFLINE, False)
    mw.show()
    sys.exit(mapp.exec_())