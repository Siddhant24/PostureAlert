<h1> POSTURE ALERT </h2>

<p> Posture Alert is a python app that alerts you if you lean forward from a pre-calibrated position. </p>

<p> It uses OpenCV for face distance estimation. On starting the app asks the user to maintain a comfortable posture for 2s. If the user leans forward by more than 1.2 times(can be changed), the app alerts by sending a notification. </p>

<p> The app's GUI has been made using PyQT5.</p>

<h3> REQUIREMENTS </h3>
<ul>
	<li> Python3 </li>
	<li> OpenCV </li>
	<li> PyQT5 </li>
</ul>

<h3> INSTALLATION </h3>
<p>Run <code>pip3 install opencv-python pyqt5</code></p>

<h3> USAGE </h3>
<p> Run <code>python3 posture.py</code></p>
<p> Sit upright in a comfortable position and click calibrate. </p>
<p> The app will notify if you are too clos to the screen. </p>
