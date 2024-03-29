#!/usr/bin/env python
from __future__ import print_function
import roslib
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from std_msgs.msg import Float32, Int8
import numpy as np
from std_msgs.msg import Float32MultiArray


class detect_marker:
    def __init__(self):
        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/image_raw", Image, self.callback)
        self.position_pub = rospy.Publisher("~position", Float32MultiArray, queue_size=10)
        self.position = np.array([0.0, 0.0])
    
    def callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print(e)

        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV_FULL)
        h = hsv[:,:, 0]
        s = hsv[:,:, 1]
        v = hsv[:,:, 2]
        mask = np.zeros(h.shape, dtype=np.uint8)
        mask[((h < 20) | (h > 200)) & (s > 128) & (v > 128)] = 255
        image, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        for contour in contours:
            approx = cv2.convexHull(contour)
            rect = cv2.boundingRect(approx)
            if ((rect[2] > 10) & (rect[3] > 10)):
                rects.append(np.array(rect))
        for rect in rects:
            cv2.rectangle(cv_image, tuple(rect[0:2]), tuple(rect[0:2] + rect[2:4]), (0, 0, 255), thickness=2)
        cv2.imshow("Image Object", cv_image)
        cv2.waitKey(1)
        if rects:
            rect = rects[0]
            x = rect[0] + rect[2] / 2.0
            y = rect[1] + rect[3] / 2.0
            height, width, channels = cv_image.shape
            self.position[0] =  (x - width  / 2.0) / (width  / 2.0)
            self.position[1] = -(y - height / 2.0) / (height / 2.0)
            print(str(self.position))
            array_for_publishing = Float32MultiArray(data=self.position)
            self.position_pub.publish(array_for_publishing)

if __name__ == '__main__':
    rospy.init_node('detect_marker', anonymous=True)
    dm = detect_marker()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting Down")
    cv2.destroyAllWindows()

