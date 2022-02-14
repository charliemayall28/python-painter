import cv2
from pathlib import Path
import numpy as np
from scipy.interpolate import splprep, splev

ROOT = Path(__file__).parent


class Img:
    def __init__(self, image_path):
        self.strpath = str(image_path)
        self.path = Path(image_path)
        self.image_name = str(self.path.stem)
        # self.image_pil = Image.open(self.image_path)
        self.array = cv2.imread(self.strpath)

    def show(self):
        cv2.imshow(self.image_name, self.image_cv)
        cv2.waitKey(0)

    def save(self, path):
        cv2.imwrite(str(path), self.image_cv)
        print("Saved: {}".format(path))


class ContourFinder:
    def __init__(self, img: Img):
        self.img = img

    def find(self):
        # use cv2 to find lines using hough transform
        # return a an array of black and white pixels, where white is a line
        grayscale = cv2.cvtColor(self.img.array, cv2.COLOR_BGR2GRAY)
        # apply gaussian blur to reduce noise
        blur = cv2.GaussianBlur(grayscale, (7, 7), 1)

        edges = cv2.Canny(blur, 100, 150, apertureSize=3)
        #

        # on the original image (self.img), make pixels red where there is an edge
        img_arr = np.array(self.img.array)
        # img_arr[edges == 255] = (0, 0, 255)
        # self.img.image_cv = edges
        # find the contours
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        # sort the contours by
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        contours_smooth = self.interpolateContours(contours)
        # draw the contours
        # create a blank image with black background
        img_contours = np.zeros(img_arr.shape, np.uint8)
        img_contours_smooth = np.zeros(img_arr.shape, np.uint8)
        # draw the contours on the blank image
        img_contours_smooth = cv2.drawContours(
            img_contours_smooth, contours_smooth, -1, (0, 255, 255), 1
        )
        img_contours = cv2.drawContours(img_contours, contours, -1, (0, 127, 255), 1)
        # cv2.drawContours(blur, contours, -1, (127, 255, 0), 1)
        # cv2.imshow("contours", img_contours)
        cv2.imwrite(str(self.img.path.parent / "contours.png"), img_contours)
        cv2.imwrite(str(self.img.path.parent / "contours_s.png"), img_contours_smooth)

        return contours

    def interpolateContours(self, contours):
        # interpolate the contours to smooth them out
        smoothened = []
        for contour in contours:
            x, y = contour.T
            # Convert from numpy arrays to normal arrays
            x = x.tolist()[0]
            y = y.tolist()[0]
            try:
                # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splprep.html
                tck, u = splprep([x, y], u=None, s=1.5, per=1, k=1)
            except Exception as e:
                print(e)
                continue
                # https://docs.scipy.org/doc/numpy-1.10.1/reference/generated/numpy.linspace.html
            u_new = np.linspace(u.min(), u.max(), 25)
            # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.interpolate.splev.html
            x_new, y_new = splev(u_new, tck, der=0, ext=0)
            # Convert it back to np format for opencv to be able to display it
            res_array = [[[int(i[0]), int(i[1])]] for i in zip(x_new, y_new)]
            smoothened.append(np.asarray(res_array, dtype=np.int32))
        return smoothened


class ShadeFinder:
    def __init__(self, img: Img):
        self.img = img

    def find(self):

        grayscale = cv2.cvtColor(self.img.array, cv2.COLOR_BGR2GRAY)
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(grayscale, kernel, iterations=1)
        blur = cv2.GaussianBlur(dilated, (7, 7), 1)
        edges = cv2.Canny(dilated, 100, 150, apertureSize=3)
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        img_contours = np.zeros(self.img.array.shape, np.uint8)
        cv2.drawContours(img_contours, contours, -1, (0, 255, 255), 1)
        cv2.imshow("contours", img_contours)
        cv2.waitKey(0)


ContourFinder(Img(ROOT / "mum.JPG")).find()
