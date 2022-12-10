import importlib
from configparser import ConfigParser


class FreqChangeResult:
    """Holds the result of a frequency change. Can represent success, an error, or False+None means an unknown result"""
    def __init__(self, success=False, error_msg=None):
        self.success = success
        self.error_msg = error_msg


class Rig:
    @classmethod
    def rig_factory(cls, config_location: str):
        rig_config_reader = RigConfigReader(config_location)
        try:
            rig_module, rig_class, params_dict = rig_config_reader.read_config()
        except Exception as e:
            print("Error parsing config file:", e)
            return None

        print("Creating instance of class:", rig_class, "from module:", rig_module)
        print("Parameters are", params_dict)
        try:
            module_ = importlib.import_module(rig_module)
            rig_instance = getattr(module_, rig_class)(**params_dict)
        except Exception as e:
            print("Problem creating instance:", e)
            return None
        print("Created Rig instance:", rig_instance.__class__.__name__)
        return rig_instance

    def set_vfo(self, freq_hz: int) -> FreqChangeResult:
        return FreqChangeResult(error_msg="Unspecified rig type")

    def cleanup_rig(self):
        pass


class DummyRig(Rig):
    def __init__(self):
        print("Dummy rig initialized")

    def set_vfo(self, freq_hz: int):
        return FreqChangeResult(error_msg="Rig control not configured")

    def cleanup_rig(self):
        pass


class RigConfigReader:
    RIG_CONTROL_METHOD_SECTION = "RIG_CONTROL_METHOD"
    RIG_CONTROL_KEY = "RIG_CONTROL"

    def __init__(self, config_location):
        self.config_location = config_location

    def read_config(self):
        config = ConfigParser()
        file_read = config.read(self.config_location)
        if not file_read:
            raise Exception("Missing rig config file: " + self.config_location)

        # first read which type of rig control will be used
        control_type = config.get(self.RIG_CONTROL_METHOD_SECTION, self.RIG_CONTROL_KEY)
        last_dot = control_type.rfind(".")
        if last_dot == -1:
            raise Exception(self.RIG_CONTROL_KEY + " should be in format: module.class")
        rig_control_module = control_type[0:last_dot]
        rig_control_class = control_type[last_dot+1:]

        # then read the constructor parameters for the class
        if not config.has_section(rig_control_class):
            raise Exception("No section matching selected type: {0} in config file: {1}"
                            .format(rig_control_class, self.config_location))
        section_options = config[rig_control_class]
        params_dict = {}
        for key, value in section_options.items():
            if value.isnumeric():
                value = int(value)
            params_dict[key] = value

        return rig_control_module, rig_control_class, params_dict
