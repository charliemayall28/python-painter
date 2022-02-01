import json
from gcode import CommandBuffer, Move, SetupCNC
from pathlib import Path
import math

ROOT = Path(__file__).parent
MIN_BRUSH_WIDTH = 5
LENGTH_SCALE = 0.01


class Maker:
    def __init__(self):
        self.buffer = CommandBuffer()
        self.setup = SetupCNC()
        self.posx = 0
        self.posy = 0
        self.posz = 0

    def loadArray(self, array):

        for xy in array:
            self.buffer.add(Move(x=xy[0], y=xy[1], f=100, e=0.1))

    def dump(self):
        return self.setup.dump() + "\n" + self.buffer.dump()

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
                y = -y
                if first:
                    self.resetStroke(x, y)
                    first = False
                self.buffer.add(Move(x=x, y=y, z=0, f=100, e=0.1))

    def addWidth(self, points, width):
        extraMoves = {
            1: [Move(x=self.posx, y=self.posy, z=5, f=100, e=0.1)],
            2: [Move(x=self.posx, y=self.posy, z=5, f=100, e=0.1)],
        }
        width = width * LENGTH_SCALE
        for point in points:
            y = int(point["point"]["y"]) * LENGTH_SCALE
            x = int(point["point"]["x"]) * LENGTH_SCALE
            y = -y
            extraMoves[1].append(Move(x=x - width / 2, y=y, z=0, f=100, e=0.1))
            extraMoves[2].append(Move(x=x + width / 2, y=y, z=0, f=100, e=0.1))

        self.buffer.add(extraMoves[1])
        self.buffer.add(extraMoves[2])

    def resetStroke(self, next_x, next_y):
        if not self.buffer.commands == []:
            prevMove = self.buffer.commands[-1]
            x, y, z = prevMove.x, prevMove.y, prevMove.z
            self.buffer.add(Move(x=x, y=y, z=5, f=100, e=0.1))
        self.buffer.add(Move(x=next_x, y=next_y, z=5, f=100, e=0.1))
