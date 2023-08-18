# generated by datamodel-codegen:
#   filename:  windfile.schema.json
#   timestamp: 2023-08-18T18:55:28+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, constr


class Api(RootModel):
    root: str = Field(
        ...,
        description='The API version of the windfile.',
        examples=['v0.0.1'],
        title='API Version',
    )


class Target(Enum):
    """
    The CI platforms that are able to run this windfile.
    """

    cli = 'cli'
    jenkins = 'jenkins'
    bamboo = 'bamboo'


class ContactData(BaseModel):
    """
    Contact data of the author.
    """

    name: str = Field(
        ..., description='The name of the author.', examples=['Andreas Resch']
    )
    email: Optional[str] = Field(
        None, description='The email of the author.', examples=['aeolus@resch.io']
    )


class ListOrDict(RootModel):
    root: Union[Dict[str, Any], List[str]] = Field(..., title='List or Dictionary')


class Lifecycle(Enum):
    """
    Defines a part of the lifecycle of a job.
    """

    preparation = 'preparation'
    working_time = 'working_time'
    post_deadline = 'post_deadline'
    evaluation = 'evaluation'
    always = 'always'


class Author(RootModel):
    root: Union[str, ContactData] = Field(
        ..., description='The author of the windfile.', title='Author'
    )


class Environment(RootModel):
    root: ListOrDict = Field(
        ..., description='Environment variables for actions.', title='Environment'
    )


class ExternalAction(BaseModel):
    """
    External action that can be executed with or without parameters.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    use: str = Field(
        ...,
        description='The name of the external action.',
        title='Name of the external action.',
    )
    parameters: Optional[ListOrDict] = Field(
        None,
        description='The parameters of the external action.',
        title='Parameters of the external action.',
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )
    environment: Optional[Environment] = Field(
        None, description='Environment variables for this external action.'
    )


class FileAction(BaseModel):
    """
    Action that is defined in a file.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    file: Optional[str] = Field(None, description='The file that contains the action.')
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )
    environment: Optional[Environment] = Field(
        None, description='Environment variables for this file action.'
    )


class InternalAction(BaseModel):
    """
    Internally defined action that can be executed.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    script: str = Field(
        ..., description='The script of the internal action. Written in aeolus DSL'
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )
    environment: Optional[Environment] = Field(
        None, description='Environment variables for this internal action.'
    )


class PlatformAction(BaseModel):
    """
    Action that is defined for a specific platform.
    """

    model_config = ConfigDict(
        extra='forbid',
    )
    platform: Target = Field(
        ..., description='The platform that this action is defined for.'
    )
    file: str = Field(
        ..., description='The file of the platform action. Written in Python'
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )
    environment: Optional[Environment] = Field(
        None, description='Environment variables for this platform action.'
    )


class Metadata(BaseModel):
    """
    Metadata of the windfile.
    """

    name: str = Field(
        ..., description='The name of the windfile.', examples=['rust-exercise-jobs']
    )
    description: str = Field(
        ...,
        description='Description of what this list of actions is supposed to achieve',
        examples=[
            'This windfile contains the jobs that are executed during the CI of the rust-exercise.'
        ],
    )
    author: Author = Field(..., description='The author of the windfile.')
    targets: Optional[List[Target]] = Field(
        None, description='The targets of the windfile.'
    )


class Action(RootModel):
    root: Union[FileAction, InternalAction, PlatformAction, ExternalAction] = Field(
        ..., description='Action that can be executed.', title='Action'
    )


class Windfile(BaseModel):
    """
    Defines the actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the windfile.
    """

    api: Api
    metadata: Metadata
    environment: Optional[Environment] = None
    jobs: Dict[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Action] = Field(
        ...,
        description='The actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the windfile.',
        title='Jobs',
    )
