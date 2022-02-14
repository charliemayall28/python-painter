from os import PathLike
from typing import Set
from imageProcess.processor import ContourFinder, Img
import random
import json
from tkinter.ttk import Style
from gcode import CommandBuffer, Move, SetupCNC, Pause
from pathlib import Path
import math
import copy
import numpy as np
import cv2

ROOT = Path(__file__).parent
MIN_BRUSH_WIDTH = (
    5  # (mm) threhold for brush width, above which strokes are added to widen the lines
)
LENGTH_SCALE = 0.12  # scale factor for line length
Z_HEIGHT = 40  # (mm) height of the z axis above the bed when instrument touches the bed
BACKOFF_HEIGHT = 30  # (mm) height to back off when moving to start a new stroke
MAX_STROKE_LENGTH = 460
CENTER_Y = 100  # (mm) center y coordinate of the bed
CENTER_X = 100  # (mm) center x coordinate of the bed
MAX_X = 200  # (mm) max x coordinate of the bed
MAX_Y = 200  # (mm) max y coordinate of the bed
MIN_Y = 60
MIN_X = 10
FEED_RATE = 1800  # (mm/min) feed rate for the machine


class Preparer:
    def __init__(self, input_item):
        """
        Class to manipulate the input to form an array in the format [[[x,y,z,f,e,rapid],[x,y,z,f,e,rapid]],[[x,y,z,f,e,rapid],[x,y,z,f,e,rapid]]]
        array_shape =

        Parameters
        ----------
        input_item: image_path|array|list
            The input item to be processed

        """
        self.input_item = input_item
        self.array = self.loadArray()
        self.moves = []

    def build(self):
        return self.make()

    def loadArray(self):
        if isinstance(self.input_item, (str, PathLike)):
            img = Img(self.input_item)
            # resize the image to fit the bed
            # img.array = cv2.resize(img.array, (MAX_X, MAX_Y))
            # cv2.imshow("image", img.array)
            # cv2.waitKey(0)

            arr = ContourFinder(img).find()
            arr = self.formatContourList(arr)
            #
            return arr

        elif isinstance(self.input_item, np.array):
            if len(self.input_item[0][0][0].tolist()) > 2:
                print(
                    "Warning: array points have more than 2 dimensions, taking first two dimensions"
                )
                return self.input_item[:, :, 0:2]
            elif len(self.input_item.shape) == 3:
                return self.input_item
            else:
                raise ValueError("Input array is not 2D")

        elif isinstance(self.input_item, list):
            # check if the list is a list of lists of lists
            try:
                if isinstance(self.input_item[0], list):
                    if isinstance(self.input_item[0][0], list):
                        return np.array(self.input_item)

            except IndexError:
                raise TypeError(
                    "Input must be a list of lists\ne.g. [ [ [ x,y ],[ x,y ] ] , [ [ x,y ],[ x,y ] ] ]"
                )

        else:
            raise TypeError("Input does not have a valid type")

    def formatContourList(self, contourList):
        new = []
        for contour in contourList:
            new_conts = []
            contour = contour.flatten()
            for i in range(0, len(contour) - 1, 2):
                new_conts.append([contour[i], contour[i + 1]])

            new.append(new_conts)
        return np.array(new)

    def make(self):
        xVals = set()
        yVals = set()

        # print(self.array.shape)
        self.resetStroke(self.array[0][0][0], self.array[0][0][0])
        strokes = Optomise.sortStrokes(self.array)
        travelLength = 0

        self.moves.append(Pause(x=MIN_X + 10, y=MIN_Y + 30, z=Z_HEIGHT))
        for stroke in strokes:

            if len(stroke) >= 2:
                self.leadIn(stroke[0], stroke[1])
                firstAfterLeadIn = True
            else:
                self.moves.append(
                    Move(
                        x=stroke[0][0],
                        y=stroke[0][1],
                        z=Z_HEIGHT + BACKOFF_HEIGHT,
                        f=FEED_RATE,
                        e=0,
                    )
                )
            for i, point in enumerate(stroke):
                if (
                    travelLength >= MAX_STROKE_LENGTH
                    and len(stroke) > 1
                    and 1 < i < len(stroke) - 1
                ):
                    self.addPause(stroke[i], stroke[i + 1])
                    travelLength = 0
                    firstAfterLeadIn = True
                move = Move(point[0], point[1], Z_HEIGHT, 0, FEED_RATE, False)
                xVals.add(point[0])
                yVals.add(point[1])
                if not firstAfterLeadIn:
                    travelLength += math.sqrt(
                        (move.x - self.moves[-1].x) ** 2
                        + (move.y - self.moves[-1].y) ** 2
                    )
                    self.moves.append(move)
                firstAfterLeadIn = False

        maxX = max(xVals)
        maxY = max(yVals)
        minX = min(xVals)
        minY = min(yVals)

        return self._manipulate(maxX, maxY, minX, minY)

    def _manipulate(self, maxX, maxY, minX, minY):
        # scale the x and y coordinates to fit the bed
        x_scale = (MAX_X - MIN_X) / (maxX - minX)
        y_scale = (MAX_Y - MIN_Y) / (maxY - minY)
        scale = min(x_scale, y_scale)
        centerX = sum([c.x for c in self.moves if isinstance(c, Move)]) / len(
            self.moves
        )
        centerY = sum([c.y for c in self.moves if isinstance(c, Move)]) / len(
            self.moves
        )
        offsetX = CENTER_X - centerX * scale
        offsetY = CENTER_Y - centerY * scale
        newMoves = []

        # scale each value, and add the center offset
        for move in self.moves:
            if not isinstance(move, Move):
                newMoves.append(move)
                continue
            newX = (move.x * scale) + offsetX
            newY = (move.y * scale) + offsetY
            move.x = newX
            move.y = newY
            newMoves.append(move)

        return newMoves

    def resetStroke(self, next_x, next_y):
        if not self.moves == []:
            prevMove = self.moves[-1]
            if isinstance(prevMove, Pause):
                pass
            else:
                x, y, z = prevMove.x, prevMove.y, prevMove.z
                self.moves.append(
                    Move(x, y, Z_HEIGHT + BACKOFF_HEIGHT, 0, FEED_RATE, False)
                )
        self.moves.append(
            Move(
                x=next_x,
                y=next_y,
                z=Z_HEIGHT + BACKOFF_HEIGHT,
                f=FEED_RATE,
                e=0,
                rapid=True,
            )
        )

    def leadIn(self, first_next, second_next):

        x1, y1 = first_next
        x2, y2 = second_next
        gradient = (y2 - y1) / (x2 - x1)

        # find the start point 20mm away from the last move in the opposite direction of the angle
        # so the line between start and first_next will lead into the first_next to second_next line
        x_start = x1 + 20 * math.cos(math.atan(gradient))
        y_start = y1 + 20 * math.sin(math.atan(gradient))
        if x_start < MIN_X:
            x_start = MIN_X + 2
        if y_start < MIN_Y:
            y_start = MIN_Y + 2
        if x_start > MAX_X:
            x_start = MAX_X - 2
        if y_start > MAX_Y:
            y_start = MAX_Y - 2

        self.moves.append(
            Move(
                x=x_start,
                y=y_start,
                z=Z_HEIGHT + BACKOFF_HEIGHT * 0.6,
                f=FEED_RATE,
                e=0,
                rapid=True,
            )
        )

    def addPause(self, first_next, second_next):
        x1, y1 = first_next
        x2, y2 = second_next
        self.moves.append(
            Move(
                x=x1,
                y=y1,
                z=Z_HEIGHT + BACKOFF_HEIGHT,
                f=FEED_RATE,
                e=0,
            )
        )
        self.moves.append(
            Pause(
                x=x1,
                y=y1,
                z=Z_HEIGHT + BACKOFF_HEIGHT,
                f=FEED_RATE,
            )
        )
        self.leadIn(first_next=first_next, second_next=second_next)


class Maker:
    def __init__(self):
        self.setup = SetupCNC()
        self.posx = 0
        self.posy = 0
        self.posz = 0

    def dump(self, moves):
        Gcode = "\n".join(move.getCommand() for move in moves)

        return self.setup.dump("start") + "\n" + Gcode + "\n" + self.setup.dump("end")

    def makeArray(self):
        array = np.array(
            [
                [command.x, command.y, command.z, command.f, command.e, command.rapid]
                for command in self.buffer.commands
            ]
        )
        return array


class Optomise:
    def sortStrokes(strokes):
        """
        sort the strokes so that strokes[x][-1][0] is as close to strokes[x+1][-1][0] as possible

        """
        if isinstance(strokes, np.ndarray):
            strokes = strokes.tolist()
        first = strokes[0]
        sortedStrokes = [first]
        strokes.remove(first)
        while len(strokes) != 0:
            endX = sortedStrokes[-1][-1][0]
            endY = sortedStrokes[-1][-1][1]
            closestIdx = None
            closestDist = None

            for i, stroke in enumerate(strokes):
                startX = stroke[0][0]
                startY = stroke[0][1]
                dist = math.sqrt((startX - endX) ** 2 + (startY - endY) ** 2)
                if closestDist is None or dist < closestDist:
                    closestDist = dist
                    closestIdx = i
            sortedStrokes.append(strokes[closestIdx])
            strokes.remove(strokes[closestIdx])
        return sortedStrokes


# TODO:
# Add length finder for path
# styling for the pressure of brush
# listener for bluetooth connection
# brush changes
