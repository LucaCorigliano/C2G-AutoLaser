import argparse

class ArgumentParser():
	processed = None
	@staticmethod
	def get(args=None):
		if not ArgumentParser.processed:		
			parser = argparse.ArgumentParser(description="C2G-AutoMicroscope")
			parser.add_argument("--verbose",  action="store_true", help="Display more stuff")
			parser.add_argument("--webcamIndex", "-W", type=int, metavar=0, default=0, help="OpenCV webcam index.")
			parser.add_argument("--topFolder", metavar=".", default=".", help="By default the program saves in .")
			parser.add_argument("--viewFinder", "-V",  action="store_true", help="Manually control the microscope and snap pictures")
			parser.add_argument("--calibrate", "-K",  action="store_true", help="Set up manual calibration")
			parser.add_argument("--corners", "-C",  action="store_true", help="Do corner cut")
			parser.add_argument("--difficultCalibration", "-D",  action="store_true", help="Set up manual parameters for automatic calibration")
			ArgumentParser.processed = parser.parse_args()
		return ArgumentParser.processed