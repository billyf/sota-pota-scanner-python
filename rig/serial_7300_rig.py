import serial
from serial import SerialException

from rig.rig_control import Rig, FreqChangeResult


def format_freq_set_cmd(hz_int: int) -> bytearray:
    """
    For a frequency like 7.123.456 we need to send "reversed" data like:
    ["0x00","0x56","0x34","0x12","0x07","0x00"]
    """
    hz = str(hz_int)
    while len(hz) < 8:
        hz = '0' + hz
    hex_str = "FE FE 94 E0 00 {0} {1} {2} {3} 00 FD".format(hz[6:8], hz[4:6], hz[2:4], hz[0:2])
    return bytearray.fromhex(hex_str)


class Serial7300Rig(Rig):
    def __init__(self, serial_port, baud_rate):
        self.ser = None
        self.serial_port = serial_port
        self.baud_rate = baud_rate

    def set_vfo(self, freq_hz: int) -> FreqChangeResult:
        # reconnecting every time so other apps can use the port
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate)
        except SerialException as se:
            print(se)
            return FreqChangeResult(error_msg=se.strerror)
        self.ser.setDTR(False)
        self.ser.setRTS(False)

        self.send_freq_set_cmd(freq_hz)
        self.ser.close()

        # returning unknown type; could read back the frequency to make sure it matches
        return FreqChangeResult()

    def send_freq_set_cmd(self, freq_hz: int) -> None:
        """Sends the command to set the frequency, and reads the reponse (echo or empty)"""
        freq_cmd = format_freq_set_cmd(freq_hz)

        print("setting freq to", freq_hz, "with freq_cmd", freq_cmd)
        self.ser.write(freq_cmd)
        self.ser.flush()

        set_response = self.ser.read(self.ser.in_waiting)
        print("set_response", set_response)
    
    def cleanup_rig(self):
        pass


if __name__ == '__main__':
    rig = Serial7300Rig("COM3", 115200)
    rig.set_vfo(7012345)
