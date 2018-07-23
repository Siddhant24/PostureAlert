# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
import sys
import pickle
import argparse
import datetime

from GUI import Ui_AboutWindow

# import subprocess

from cv2 import (VideoCapture, waitKey, CascadeClassifier, cvtColor,
                 COLOR_BGR2GRAY)

from PyQt5.QtWidgets import (QPushButton, QApplication, QProgressBar, QLabel,
                             QInputDialog, qApp, QAction, QMenu,
                             QSystemTrayIcon, QMainWindow, QDialog)
from PyQt5.QtCore import (QThread, QTimer, QRect, QPropertyAnimation)
from PyQt5.QtGui import QIcon


def pyInstallerResourcePath(relativePath):
    basePath = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(basePath, relativePath)

# Delay between checking posture in miliseconds.
MONITOR_DELAY = 2000

# Notify when user is 1.2 times closer than the calibration distance.
SENSITIVITY = 1.2
CALIBRATION_SAMPLE_RATE = 100

USER_ID = None
SESSION_ID = None
TERMINAL_NOTIFIER_INSTALLED = None

CASCPATH = 'face.xml'
FACECASCADE = CascadeClassifier(pyInstallerResourcePath(CASCPATH))
print("path:", pyInstallerResourcePath(CASCPATH))



def trace(frame, event, arg):
    print(("%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno)))
    return trace


def getFaces(frame):
    gray = cvtColor(frame, COLOR_BGR2GRAY)
    faces = FACECASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=2,
        minSize=(100, 100),
        flags=0)
    if len(faces):
        print("Face found: ", faces[0])
    return faces


class Posture(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.capture = Capture(self)

        self.timer = QTimer(self, timeout=self.calibrate)
        self.mode = 0  # 0: Initial, 1: Calibrate, 2: Monitor
        self.instructions.setText('Sit upright and click \'Calibrate\'')

    def closeEvent(self, event): 
        qApp.quit()

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def initUI(self):

        menu = QMenu()
        self.trayIcon = QSystemTrayIcon(self)
        supported = self.trayIcon.supportsMessages()
        self.trayIcon.setContextMenu(menu)
        self.trayIcon.showMessage('a', 'b')
        self.trayIcon.show()
        self.postureIcon = QSystemTrayIcon(self)
        self.postureIcon.setContextMenu(menu)
        self.postureIcon.show()

        self.pbar = QProgressBar(self)
        self.pbar.setGeometry(30, 40, 200, 25)
        self.pbarValue = 0
        self.setGeometry(300, 300, 290, 150)
        self.setWindowTitle('Posture Monitor')

        self.startButton = QPushButton('Calibrate', self)
        self.startButton.move(30, 60)
        self.startButton.clicked.connect(self.calibrate)
        self.stopButton = QPushButton('Stop', self)
        self.stopButton.move(30, 60)
        self.stopButton.clicked.connect(self.endCalibration)
        self.stopButton.hide()
        self.settingsButton = QPushButton('Settings', self)
        self.settingsButton.move(140, 60)
        self.settingsButton.clicked.connect(self.settings)

        self.doneButton = QPushButton('Done', self)
        self.doneButton.move(30, 60)
        self.doneButton.hide()
        self.doneButton.clicked.connect(self.minimize)

        self.instructions = QLabel(self)
        self.instructions.move(40, 20)
        self.instructions.setText('Sit upright and click \'Calibrate\'')
        self.instructions.setGeometry(40, 20, 230, 25)

        if not supported:
            self.instructions.setText(
                'Error: Notification is not available on your system.')
        self.show()

    def minimize(self):
        self.reset()
        self.hide()

    def reset(self):
        pass

    def settings(self):
        global MONITOR_DELAY
        seconds, ok = QInputDialog.getInt(
            self, "Delay Settings",
            "Enter number of seconds to check posture\n(Default = 2)")
        if ok:
            seconds = seconds if seconds >= 1 else 0.5
            MONITOR_DELAY = seconds * 1000

    def endCalibration(self):
        self.mode = 2  # Monitor mode
        self.timer.stop()
        self.stopButton.hide()
        self.startButton.setText('Recalibrate')  # Keep hidden.
        self.instructions.setText('Sit upright and click \'Recalibrate\'')
        self.instructions.hide()
        self.pbar.hide()
        self.settingsButton.hide()
        self.animateClosing()

        # Begin monitoring posture.
        self.timer = QTimer(self, timeout=self.monitor)
        self.timer.start(MONITOR_DELAY)

    def animateClosing(self):
        self.doneButton.show()
        animation = QPropertyAnimation(self.doneButton, b"geometry")
        animation.setDuration(1000)
        animation.setStartValue(QRect(10, 60, 39, 20))
        animation.setEndValue(QRect(120, 60, 39, 20))
        animation.start()
        self.animation = animation

    def monitor(self):
        """
        Take the picture, find the face, and send notification
        if needed.
        """
        photo = self.capture.takePhoto()
        faces = getFaces(photo)
        while not len(faces):
            print("No faces detected.")
            time.sleep(2)
            photo = self.capture.takePhoto()
            faces = getFaces(photo)
     
        x, y, w, h = faces[0]
        if w > self.upright * SENSITIVITY:
            self.notify(
                title='PostureAlert 🙇👊',  
                subtitle='notice',
                message='Sit up straight 🙏⛩',)

    def notify(self, title, subtitle, message, sound=None, appIcon=None):
            self.trayIcon.showMessage("Notice 🙇👊", "Keep straight posture",
                                      QSystemTrayIcon.Information, 4000)

    def calibrate(self):
        if self.mode == 2:  
            self.mode = 1
            self.stopButton.show()
            self.startButton.hide()
            self.instructions.setText('Press \'stop\' when ready')
            self.timer.stop()
            self.timer = QTimer(self, timeout=self.calibrate)
            self.timer.start(CALIBRATION_SAMPLE_RATE)
        photo = self.capture.takePhoto()
        faces = getFaces(photo)
        while not len(faces):
            print("No faces detected.")
            time.sleep(2)
            photo = self.capture.takePhoto()
            faces = getFaces(photo)
       
        x, y, w, h = faces[0]
        self.upright = w
        if self.mode == 0:  # Initial mode
            self.timer.start(CALIBRATION_SAMPLE_RATE)
            self.startButton.hide()
            self.stopButton.show()
            self.instructions.setText('Press \'stop\' when ready')
            self.mode = 1  # Calibrate mode
        elif self.mode == 1:
            # Update posture monitor bar.
            self.pbar.setValue(self.upright / 4)
            time.sleep(0.05)


class Capture(QThread):
    def __init__(self, window):
        super(Capture, self).__init__(window)
        self.window = window
        self.capturing = False
        self.cam = VideoCapture(0)
        self.cam.set(3, 640)
        self.cam.set(4, 480)

    def takePhoto(self):
        if not self.cam.isOpened():
            self.cam.open(0)
            waitKey(5)
        _, frame = self.cam.read()
        waitKey(1)

        return frame

def main():
    TERMINAL_NOTIFIER_INSTALLED = True if os.path.exists(
        '/usr/local/bin/terminal-notifier') else False
    # QApplication expects the first argument to be the program name.
    qt_args = sys.argv[:1]
    app = QApplication(qt_args)
    posture = Posture()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
