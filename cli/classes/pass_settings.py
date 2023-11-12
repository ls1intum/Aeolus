"""
Settings for a pass, like input and output settings and the windfile.
"""
from typing import Optional

from classes.generated.actionfile import ActionFile
from classes.generated.windfile import WindFile
from classes.input_settings import InputSettings
from classes.pass_metadata import PassMetadata
from classes.output_settings import OutputSettings


class PassSettings:
    """
    Settings for a pass, like input and output settings and the windfile.
    """

    windfile: Optional[WindFile]
    actionfile: Optional[ActionFile]
    output_settings: OutputSettings
    input_settings: InputSettings
    metadata: PassMetadata

    def __init__(
        self,
        input_settings: InputSettings,
        output_settings: OutputSettings,
        metadata: PassMetadata = PassMetadata(),
        windfile: Optional[WindFile] = None,
        actionfile: Optional[ActionFile] = None,
    ):  # ignore pylint: disable=too-many-arguments
        self.windfile = windfile
        self.actionfile = actionfile
        self.metadata = metadata
        self.output_settings = output_settings
        self.input_settings = input_settings
