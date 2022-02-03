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

    def _decimalPlaces(self):
        self.x = round(float(self.x, 4))
        self.y = round(float(self.y, 4))
        self.z = round(float(self.z, 4))

    def _setAxes(self):
        if self.x != None:
            self.__command += f"X{self.x:.2f} "
        if self.y != None:
            self.__command += f"Y{self.y:.2f} "
        if self.z != None:
            self.__command += f"Z{self.z:.2f} "
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
    THIS IS A DEMO SETUP INSTRUCTION CREATOR FOR USE ON THE CURA CR20

    """

    def __init__(self) -> None:
        self.start_commands = [
            "M201 X500.00 Y500.00 Z100.00 E5000.00 ;Setup machine max acceleration",
            "M203 X500.00 Y500.00 Z10.00 E50.00 ;Setup machine max feedrate",
            "M204 P500.00 R1000.00 T500.00 ;Setup Print/Retract/Travel acceleration",
            "M205 X8.00 Y8.00 Z0.40 E5.00 ;Setup Jerk",
            "M220 S100 ;Reset Feedrate",
            "M221 S100 ;Reset Flowrate",
            "G28 ;Home",
            "M420 S1 Z2 ;Enable ABL using saved Mesh and Fade Height",
            "G92 E0 ;Reset Extruder",
            "G1 Z2.0 F3000 ;Move Z Axis up",
            "G1 X10.1 Y20 Z40 F5000.0 ;Move to start position",
            "G92 E0 ;Reset Extruder",
            "G1 X40 Y40 Z40 F3000 ;Move Z Axis up",
            "M0; stop and wait for user input",
            "G1 X40 Y40 Z50 F3000 ;Move Z Axis up",
        ]
        self.end_commands = [
            "G1 Z50 F3000 ;Move Z Axis up",
            "G91 ;Relative positioning",
            "G1 E-2 F2700 ;Retract a bit",
            "G1 E-2 Z0.2 F2400 ;Retract and raise Z",
            "G1 X5 Y5 F3000 ;Wipe out",
            "G1 Z10 ;Raise Z more",
            "G90 ;Absolute positioning",
            "G1 X0 Y150 ;Present print",
            "M106 S0 ;Turn-off fan",
            "M104 S0 ;Turn-off hotend",
            "M140 S0 ;Turn-off bed",
            "M84 X Y E ;Disable all steppers but Z",
        ]

    def dump(self, type_):
        if type_ == "start":
            return "\n".join(self.start_commands)
        elif type_ == "end":
            return "\n".join(self.end_commands)
        else:
            raise ValueError("Invalid type")
