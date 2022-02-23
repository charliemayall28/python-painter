import cv2
from pathlib import Path
import numpy as np
from scipy.interpolate import splprep, splev
import warnings

ROOT = Path(__file__).parent


class Img:
    def __init__(self, image_path):
        self.strpath = str(image_path)
        self.path = Path(image_path)
        self.image_name = str(self.path.stem)
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
        grayscale = cv2.cvtColor(self.img.array, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(grayscale, (7, 7), 1)
        edges = cv2.Canny(blur, 100, 150, apertureSize=3)
        contours, hierarchy = cv2.findContours(
            edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        contours_smooth = self.interpolateContours(contours)
        img_contours = np.zeros(self.img.array.shape, np.uint8)
        img_contours = cv2.drawContours(
            img_contours, contours_smooth, -1, (0, 255, 255), 1
        )
        cv2.imwrite(str(self.img.path.parent / "contours.png"), img_contours)
        return contours

    def interpolateContours(self, contours):
        smoothened = []
        warnings.filterwarnings("ignore")
        for contour in contours:
            try:
                x, y = contour.T
                x = x.tolist()[0]
                y = y.tolist()[0]
                tck, u = splprep([x, y], u=None, s=1.0, per=1, k=3)
                u_new = np.linspace(u.min(), u.max(), 25)
                x_new, y_new = splev(u_new, tck, der=0, ext=0)
                res_array = [[[int(i[0]), int(i[1])]] for i in zip(x_new, y_new)]
                smoothened.append(np.asarray(res_array, dtype=np.int32))
            except Exception:  # this indirectly ends up removing contours that are duplicates (i think :? )

                continue

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
