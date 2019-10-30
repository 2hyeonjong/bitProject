import cv2
import os
import numpy as np
import tensorflow as tf
import tarfile
import six.moves.urllib as urllib
import time
import math
import sys
import pickle

from PyQt5 import QtCore, QtGui, QtWidgets
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from object_detection.utils import ops as utils_ops

debug = True
class ObjectDetector():

    def __init__(self, model_name, label_file='data/object-detection.pbtxt'):

        # Load a (frozen) Tensorflow model into memory.
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile('/home/bit205/Desktop/models/research/object_detection/freeze/training_inception_final_186686/frozen_inference_graph.pb', 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            graph = self.detection_graph

            ops = graph.get_operations()
            all_tensor_names = {output.name for op in ops  for output in op.outputs}
            tensor_dict = {}
            for key in [
                  'num_detections', 'detection_boxes', 'detection_scores',
                  'detection_classes', 'detection_masks'
              ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = graph.get_tensor_by_name(tensor_name)

            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, 480, 640)
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed, 0)

            self.tensor_dict = tensor_dict

        self.sess = tf.Session(graph=self.detection_graph)

        # Loading label map
        # Label maps map indices to category names,
        # so that when our convolution network predicts `5`,
        # we know that this corresponds to `airplane`.
        # Here we use internal utility functions,
        # but anything that returns a dictionary mapping integers to appropriate string labels would be fine
        label_map = label_map_util.load_labelmap(label_file)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=90, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)
        self.output_dict = None

        self.last_inference_time = 0

    def run_inference(self, image_np):
        sess = self.sess
        graph = self.detection_graph
        with graph.as_default():
            image_tensor = graph.get_tensor_by_name('image_tensor:0')

            # Run inference
            output_dict = sess.run(self.tensor_dict,
                                 feed_dict={image_tensor: np.expand_dims(image_np, 0)})

            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict['detection_classes'][0].astype(np.uint8)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]

        return output_dict

    def time_to_run_inference(self):
        unixtime = int(time.time())
        if self.last_inference_time != unixtime:
            self.last_inference_time = unixtime
            return True
        return False

    def detect_objects(self, frame):
        rgb_small_frame = frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if True:    
            self.output_dict = self.run_inference(rgb_small_frame)

        #time3 = time.time()

        vis_util.visualize_boxes_and_labels_on_image_array(
          frame,
          self.output_dict['detection_boxes'],
          self.output_dict['detection_classes'],
          self.output_dict['detection_scores'],
          self.category_index,
          instance_masks=self.output_dict.get('detection_masks'),
          use_normalized_coordinates=True,
          line_thickness=1)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.ymin=[]
        self.xmin=[]
        self.ymax=[]
        self.xmax=[]

        for _ in range(0,100):
            if self.output_dict['detection_scores'][_] != np.float32(0.0):
                if debug:
                    print(_," boxes : ",self.output_dict['detection_boxes'][_])               
                    print(_," class : ",self.output_dict['detection_classes'][_])
                    print(_," score : ",self.output_dict['detection_scores'][_]*100)
                self.ymin.append(int(self.output_dict['detection_boxes'][_][0]*height))
                self.xmin.append(int(self.output_dict['detection_boxes'][_][1]*width))
                self.ymax.append(int(self.output_dict['detection_boxes'][_][2]*height))
                self.xmax.append(int(self.output_dict['detection_boxes'][_][3]*width))
                self.ob_count=_
        return frame

    '''
    def object_boxdraw(self, frame):
        self.dot = [[0 for x in range(2)] for y in range(self.ob_count+1)]
        if self.ob_count != 0:            
            for i in range(0 , self.ob_count +1):
                print(self.ob_count,i)
                #frame = cv2.rectangle(frame,(self.xmin[i],self.ymin[i]),(self.xmax[i],self.ymax[i]),(255,0,0),3)
                self.dot[i]=[int(self.xmin[i]+(self.xmax[i]-self.xmin[i])/2),int(self.ymin[i]+(self.ymax[i]-self.ymin[i])/2)]
                #frame = cv2.line(frame,(self.dot[i][0],self.dot[i][1]),(self.dot[i][0],self.dot[i][1]),(255,0,0),5)
        return frame
    
    def count_inbox(self):
        dot_count = 0
        if self.ob_count != 0:
            for i in range(self.ob_count +1):
                #print("dotx",[i],"doty",[i]," : ",self.dot[i][0],self.dot[i][1])
                if 100<self.dot[i][0]<1500 and 0<self.dot[i][1]<1080 :
                    if self.output_dict['detection_classes'][i]==2:
                        dot_count = dot_count+1
        #print("Count old people inbox : ",dot_count)
        #cv2.putText(frame, "Count old people : ", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
        #cv2.putText(frame, str(dot_count), (750, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255),3)
        return dot_count
        '''
if __name__ == '__main__':
    detector = ObjectDetector('./freeze/training_inception_final_186686')
    cap = cv2.VideoCapture('/home/bit205/Desktop/models/research/object_detection/videos/inception.mp4')
    cap.set(cv2.CAP_PROP_FPS, 2)
    fps= cap.get(cv2.CAP_PROP_FPS)
    total=cap.get(cv2.CAP_PROP_FRAME_COUNT)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #if debug:
        #print('width {0}, height {1}, fps {2}'.format(width, height, fps))
        #print("press `q` to quit")

    if debug:
        file_name ='./output/testinception1123.avi'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer = cv2.VideoWriter(file_name, fourcc, fps, (1300, 750))
    
    # save
    list_dot_count = []
    

    while True:
        
        ret,frame =cap.read()
        frame = cv2.resize(frame, (1300,750))
        if frame is None:
            break
        frame = detector.detect_objects(frame)  
        #frame = detector.object_boxdraw(frame)
        #frame = cv2.rectangle(frame,(0,0),(1500,1080),(0,255,0),3)

        #var_dot_count = detector.count_inbox()
        #list_dot_count.append(var_dot_count)
        #print("list_dot_count : {}".format(list_dot_count))

        

        # show the frame
        cv2.imshow("Frame", frame)
        writer.write(frame)
        # if the `q` key was pressed, break from the loop
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
                break
        if key == ord("s"):
            for _ in range(0,60):
                cap.read()
        if key == ord("a"):
            for _ in range(60,0):
               cap.read()

    #with open('test.pickle', 'wb') as f:
    #    pickle.dump(list_dot_count, f, pickle.HIGHEST_PROTOCOL)

    # do a bit of cleanup
    cap.release()
    writer.release()
    cv2.destroyAllWindows()
    print('finish')

    