# generated by datamodel-codegen:
#   filename:  windfile.schema.json
#   timestamp: 2023-08-17T19:53:29+00:00

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, RootModel, constr


class Target(Enum):
    cli = 'cli'
    jenkins = 'jenkins'
    bamboo = 'bamboo'


class ContactData(BaseModel):
    name: str = Field(
        ..., description='The name of the author.', examples=['Andreas Resch']
    )
    email: Optional[str] = Field(
        None, description='The email of the author.', examples=['aeolus@resch.io']
    )


class Lifecycle(Enum):
    preparation = 'preparation'
    working_time = 'working_time'
    post_deadline = 'post_deadline'
    evaluation = 'evaluation'
    always = 'always'


class Author(RootModel):
    root: Union[str, ContactData] = Field(
        ..., description='The author of the windfile.', title='Author'
    )


class FileAction(BaseModel):
    file: Optional[str] = Field(None, description='The file that contains the action.')
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )


class InternalAction(BaseModel):
    script: Optional[str] = Field(
        None, description='The script of the internal action. Written in aeolus DSL'
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )


class PlatformAction(BaseModel):
    platform: Optional[Target] = Field(
        None, description='The platform that this action is defined for.'
    )
    file: Optional[str] = Field(
        None, description='The file of the platform action. Written in Python'
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )


class Metadata(BaseModel):
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
    root: Union[FileAction, InternalAction, PlatformAction] = Field(
        ..., description='Action that can be executed.', title='Action'
    )


class Jobs(BaseModel):
    actions: Optional[Dict[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Action]] = Field(
        None,
        description='The actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the windfile.',
        title='Actions',
    )


class Windfile(BaseModel):
    api: str = Field(
        ...,
        description='The API version of the windfile.',
        examples=['v0.0.1'],
        title='API Version',
    )
    metadata: Metadata
    jobs: Dict[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Jobs]
