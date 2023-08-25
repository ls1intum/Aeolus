from typing import Optional

from classes.generated.actionfile import ActionFile
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.output_settings import OutputSettings


class PassSettings:
    """
    Settings for a pass, like input and output settings and the windfile.
    """

    windfile: Optional[WindFile]
    actionfile: Optional[ActionFile]
    output_settings: OutputSettings
    input_settings: InputSettings


    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        windfile: WindFile = None,
        actionfile: ActionFile = None,
    ):
        self.windfile = windfile
        self.actionfile = actionfile
        self.output_settings = output_settings
        self.input_settings = input_settings
