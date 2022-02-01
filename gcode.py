class CommandBuffer:
    def __init__(self):
        self.commands = []

    def dump(self):
        return "\n".join([comObj.command for comObj in self.commands])

    def add(self, commandObj):
        if isinstance(commandObj, list):
            self.commands.extend([commandObj for commandObj in commandObj])
            return
        self.commands.append(commandObj)


class Move:
    def __init__(self, x=None, y=None, z=None, e=None, f=None):
        self.x = x
        self.y = y
        self.z = z
        self.e = e
        self.f = f
        self.__command = ""
        self.command = self._setCommand()

    def _setAxes(self):
        if self.x != None:
            self.__command += "X" + str(self.x) + " "
        if self.y != None:
            self.__command += "Y" + str(self.y) + " "
        if self.z != None:
            self.__command += "Z" + str(self.z) + " "
        if self.e != None:
            self.__command += "E" + str(self.e) + " "

    def _setSpeed(self):

        if self.f != None:
            self.__command += "F" + str(self.f) + " "

    def _setCommand(self):
        self.__command = "G1 "
        self._setAxes()
        self._setSpeed()
        return self.__command

    def _setCommand_G0(self):
        self.__command = "G0 "
        self._setAxes()
        self._setSpeed()


class SetupCNC:
    """
    THIS IS A DEMO SETUP INSTRUCTION CREATOR FOR USE ON https://ncviewer.com/

    """

    def __init__(self) -> None:
        commands = [
            "N10 G90 G94 G17 G69",
            "N15 G20",
            "N20 G53 G0 Z0.",
            "N30 T1 M6",
            "N35 S7640 M3",
            "N40 G54",
            "N45 M8",
        ]
        self.commands = commands

    def dump(self):
        return "\n".join(self.commands)
