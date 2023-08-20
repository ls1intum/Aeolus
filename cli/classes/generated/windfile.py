# generated by datamodel-codegen:
#   filename:  windfile.json

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field, constr

from . import definitions


class WindFile(BaseModel):
    """
    Defines the actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the windfile.
    """

    api: definitions.Api
    metadata: definitions.Metadata
    environment: Optional[definitions.Environment] = None
    jobs: Dict[constr(pattern=r'^[a-zA-Z0-9._-]+$'), definitions.Action] = Field(
        ...,
        description='The actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the windfile.',
        title='Jobs',
    )
