import json
from gcode import CommandBuffer, Move, SetupCNC
from pathlib import Path
import math
import copy
import numpy as np

ROOT = Path(__file__).parent
MIN_BRUSH_WIDTH = 5
LENGTH_SCALE = 0.12
Z_HEIGHT = 40
BACKOFF_HEIGHT = 2
CENTER_Y = 117
CENTER_X = 117
MAX_X = 220
MAX_Y = 220
FEED_RATE = 1800


class Maker:
    def __init__(self):
        self.buffer = CommandBuffer()
        self.setup = SetupCNC()
        self.posx = 0
        self.posy = 0
        self.posz = 0

    def loadArray(self, array):

        for xy in array:
            self.buffer.add(Move(x=xy[0], y=xy[1], z=Z_HEIGHT, f=FEED_RATE, e=0))

    def dump(self):
        self.flipAboutZAxis()
        self.center()

        self.dontHurtTheMachine()
        return (
            self.setup.dump("start")
            + "\n"
            + self.buffer.dump()
            + "\n"
            + self.setup.dump("end")
        )

    def dontHurtTheMachine(self):
        # check if any of the commands have x> MAX_X or y> MAX_Y
        for command in self.buffer.commands:

            if command.x > MAX_X or command.y > MAX_Y:
                self.buffer.commands = []
                raise Exception(
                    "Command has x or y coordinate greater than MAX_X or MAX_Y"
                )

    def center(self):
        maxMovex = max([com.x for com in self.buffer.commands])
        maxMovey = max([com.y for com in self.buffer.commands])
        minMovex = min([com.x for com in self.buffer.commands])
        minMovey = min([com.y for com in self.buffer.commands])
        print(maxMovex, maxMovey, minMovex, minMovey)
        x_offset = CENTER_X - (maxMovex + minMovex) / 2
        y_offset = CENTER_Y - (maxMovey + minMovey) / 2
        for com in self.buffer.commands:
            com.x += x_offset
            com.y += y_offset

    def flipAboutZAxis(self):

        # make an array of x,y,z values for each command from self.buffer.commands
        def getXYZ(command):
            return [command.x, command.y, command.z, command.f, command.e]

        # make the array
        xyz = np.array([getXYZ(command) for command in self.buffer.commands])
        # find the center of the array
        center = np.mean(xyz, axis=0)
        # flip the array about the center in the y axis
        xyz[:, 1] = center[1] - (xyz[:, 1] - center[1])
        # center the array at CENTER_X, CENTER_Y
        xyz[:, 0] = xyz[:, 0] - center[0] + CENTER_X
        xyz[:, 1] = xyz[:, 1] - center[1] + CENTER_Y

        # make a new command buffer
        # xyz = self.fillBed(xyz)
        buffer = []
        for x, y, z, f, e in xyz:
            buffer.append(Move(x=x, y=y, z=z, f=f, e=e))
        # replace the old commands with the new ones
        self.buffer.commands = buffer

    def loadArrayJSON(self, arrayJSON):
        array = arrayJSON
        for stroke in array["strokes"]:
            weight = stroke["weight"]
            mode = stroke["mode"]
            if weight > MIN_BRUSH_WIDTH:
                self.addWidth(stroke["points"], weight)
            if mode != "draw":
                continue
            first = True
            for point in stroke["points"]:

                x = int(point["point"]["x"]) * LENGTH_SCALE
                y = int(point["point"]["y"]) * LENGTH_SCALE
                # y = -y
                if first:
                    self.resetStroke(x, y)
                    first = False
                self.buffer.add(Move(x=x, y=y, z=Z_HEIGHT, f=FEED_RATE, e=0))

    def addWidth(self, points, width):
        extraMoves = {
            1: [],
            2: [],
        }
        width = width * LENGTH_SCALE
        for point in points:
            y = int(point["point"]["y"]) * LENGTH_SCALE
            x = int(point["point"]["x"]) * LENGTH_SCALE
            # y = -y
            extraMoves[1].append(
                Move(x=x - width / 2, y=y, z=Z_HEIGHT, f=FEED_RATE, e=0)
            )
            extraMoves[2].append(
                Move(x=x + width / 2, y=y, z=Z_HEIGHT, f=FEED_RATE, e=0)
            )

        self.buffer.add(extraMoves[1])
        self.buffer.add(extraMoves[2])

    def fillBed(self, array: np.array):
        # find the max x and y values
        maxX = np.max(array[:, 0])
        maxY = np.max(array[:, 1])
        # find the min x and y values
        minX = np.min(array[:, 0])
        minY = np.min(array[:, 1])
        # find how much the array can be scaled by without maxX or maxY exceeding MAX_X or MAX_Y
        scale = min(MAX_X / maxX, MAX_Y / maxY)
        # scale the arrays x,y values by the scale factor
        array[:, 0] = array[:, 0] * scale
        array[:, 1] = array[:, 1] * scale
        return array

    def resetStroke(self, next_x, next_y):
        if not self.buffer.commands == []:
            prevMove = self.buffer.commands[-1]
            x, y, z = prevMove.x, prevMove.y, prevMove.z
            self.buffer.add(
                Move(x=x, y=y, z=Z_HEIGHT + BACKOFF_HEIGHT, f=FEED_RATE, e=0)
            )
        self.buffer.add(
            Move(x=next_x, y=next_y, z=Z_HEIGHT + BACKOFF_HEIGHT, f=FEED_RATE, e=0)
        )
