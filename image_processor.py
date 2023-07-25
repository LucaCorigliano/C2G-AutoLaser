import cv2
from subprocess import Popen
import numpy as np
from numpy.linalg import norm
class ImageProcessor:
    @staticmethod


    def brightness(img):
        if len(img.shape) == 3:
            # Colored RGB or BGR (*Do Not* use HSV images with this function)
            # create brightness with euclidean norm
            return np.mean(norm(img, axis=2)) / np.sqrt(3)
        else:
            # Grayscale
            return np.mean(img)
    @staticmethod
    def increase_contrast(image, clipLimit=1.5, tileGridSize=(8,8)):
        # converting to LAB color space
        lab= cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)

        # Applying CLAHE to L-channel
        # feel free to try different values for the limit and grid size:
        clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
        cl = clahe.apply(l_channel)

        # merge the CLAHE enhanced L-channel with the a and b channel
        limg = cv2.merge((cl,a,b))

        # Converting image from LAB Color model to BGR color spcae
        enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        # Stacking the original image with the enhanced image
        #result = np.hstack((image, enhanced_img))
        return enhanced_img
    @staticmethod
    def increase_saturation(image, saturation=1.4, brightness=1.0):
        # Convert to HSV
        hsvImg = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

        # Increase saturation
        hsvImg[...,1] = hsvImg[...,1]*saturation

        # Correct brightness 
        hsvImg[...,2] = hsvImg[...,2]*brightness

        # Back to RGB
        return cv2.cvtColor(hsvImg,cv2.COLOR_HSV2BGR)
    @staticmethod
    def stitch(path, out, x, y):
        
        slushy = Popen([".\\bin\\Slushy.exe", path, str(x), str(y), out])
        exit_code = slushy.wait()
        return exit_code 
    @staticmethod
    def draw_text(img, text, font = cv2.FONT_HERSHEY_SIMPLEX, x=50, y=50, fontScale=1, r=255, g=0, b=0, thickness=2):
        # org
        org = (x, y)
        # Blue color in BGR
        color = (b, g, r)
        # Using cv2.putText() method
        cv2.putText(img, text, org, font, 
                           fontScale, color, thickness, cv2.LINE_AA)
    @staticmethod
    def resize_aspect_ratio(image, width=None, height=None, inter=cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]

        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))
        return cv2.resize(image, dim, interpolation=inter)
    @staticmethod
    def resize_for_preview(image, size, inter=cv2.INTER_AREA):
        dim = None
        (h, w) = image.shape[:2]
        
        if h > w:
            r = size[1] / float(h)
            dim = (int(w * r), size[1])
        else:
            r = size[0] / float(w)
            dim = (size[0], int(h * r))
        return cv2.resize(image, dim, interpolation=inter)
    @staticmethod
    def draw_grid(img, line_color=(255, 255, 0), thickness=1, type_=cv2.LINE_AA, pxstep=50):
        x = pxstep
        y = pxstep
        while x < img.shape[1]:
            cv2.line(img, (x, 0), (x, img.shape[0]), color=line_color, lineType=type_, thickness=thickness)
            x += pxstep

        while y < img.shape[0]:
            cv2.line(img, (0, y), (img.shape[1], y), color=line_color, lineType=type_, thickness=thickness)
            y += pxstep
    @staticmethod
    def draw_center(img, line_color=(255, 255, 0), thickness=2, radius=5):
        (h, w) = img.shape[:2]
        cv2.circle(img, (int(w/2),int(h/2)), radius, line_color, thickness)  
    @staticmethod
    def save_image(image, path):
        cv2.imwrite(path, image)
    @staticmethod
    def combine_exposures(orig_a, orig_b):
        # Black Magic fuckery
        a_alpha=1.9211743057429187
        a_beta=-10
        b_alpha=1.7866337745304055
        b_beta=5
        blend_1=0.29903173623925716
        blend_2=0.5855179501120457
        gamma=1.6429516671875442
        a = cv2.convertScaleAbs(orig_a, alpha=a_alpha, beta=a_beta)
        b = cv2.convertScaleAbs(orig_b, alpha=b_alpha, beta=b_beta)
        return cv2.addWeighted(a, blend_1, b, blend_2, gamma)