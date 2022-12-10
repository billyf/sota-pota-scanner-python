import time
import Hamlib
from rig.rig_control import Rig, FreqChangeResult


class HamlibRig(Rig):
    def __init__(self, device_id: str, rig_model: int):
        self.my_rig = None
        self.device_id = device_id
        self.rig_model = rig_model

    def set_vfo(self, freq_hz: int) -> FreqChangeResult:
        """Returns true if VFO was set to freq_hz"""
        if not self.my_rig:
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_ERR)
            self.my_rig = Hamlib.Rig(self.rig_model)
            self.my_rig.set_conf("rig_pathname", self.device_id)
            # self.my_rig.set_conf("retry", "2")
            self.my_rig.set_conf("dtr_state", "OFF")
            self.my_rig.set_conf("rts_state", "OFF")

            self.my_rig.open()
            if self.my_rig.error_status:
                print(Hamlib.rigerror(self.my_rig.error_status))
                self.cleanup_rig()
                return FreqChangeResult(error_msg="Problem opening Hamlib connection")

        self.my_rig.set_freq(Hamlib.RIG_VFO_CURR, freq_hz)

        time.sleep(.2)

        new_freq = self.my_rig.get_freq(Hamlib.RIG_VFO_CURR)
        print("get_freq result: " + str(new_freq))
        if int(new_freq) != freq_hz:
            self.cleanup_rig()
            return FreqChangeResult(error_msg="Problem changing freq")
        return FreqChangeResult(success=True)

    def cleanup_rig(self):
        if self.my_rig:
            self.my_rig.close()
        self.my_rig = None


if __name__ == '__main__':
    rig = HamlibRig("/dev/ttyUSBicom", Hamlib.RIG_MODEL_IC7300)
    rig.set_vfo(7012345)
