import cv2
from config import CameraConfig
class Camera(cv2.VideoCapture):
    @staticmethod
    def getCameras():
        # checks the first 10 indexes.
        index = 0
        dict = {}
        i = 20
        while i > 0:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                resolution = f"{cap.get(cv2.CAP_PROP_FRAME_HEIGHT )}p" # CAP_PROP_FRAME_HEIGHT 
                dict[index] = resolution
                cap.release()
            index += 1
            i -= 1
        return dict
    @staticmethod
    def connect(index):
        cap = Camera(index)
        cap.setConfig()
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return cap, w, h
    def __init__(self, index):
        cv2.VideoCapture.__init__(self, index,  cv2.CAP_DSHOW)
    def setConfig(self):
        self.set(cv2.CAP_PROP_FRAME_WIDTH , CameraConfig.width)
        self.set(cv2.CAP_PROP_FRAME_HEIGHT , CameraConfig.height)
    def capturePhoto(self):
        result, image = self.read()
        attempts_left = 10
        while not result:
            if attempts_left <= 0:
                raise(BaseException("Camera photo taking failed"))
            result, image = self.read()
            attempts_left = attempts_left - 1
        #image=cv2.transpose(image)
        #image=cv2.flip(image,flipCode=0)

        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    def capturePhotoSharpness(self, num_samples=2, crop_name="default"):
        #print(crop_name)
        best_image = None
        best_sharpness = -200
        for i in range(num_samples):
            image = self.capturePhoto()
            grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            #cropped = cv2.equalizeHist(cropped)
            sharpness = cv2.Laplacian(grayscale, cv2.CV_64F).var()
            if sharpness > best_sharpness:
                best_image = image
                best_sharpness = sharpness
        #cv2.imshow(crop_name, cropped)
        return best_sharpness, best_image
