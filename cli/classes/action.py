# generated by datamodel-codegen:
#   filename:  action.schema.json
#   timestamp: 2023-08-17T17:43:40+00:00

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

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


class ListOrDict(RootModel):
    root: Union[Dict[str, Any], List[str]] = Field(..., title='List or Dictionary')


class Author(RootModel):
    root: Union[str, ContactData] = Field(
        ..., description='The author of the action.', title='Author'
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


class ExternalActionWithParameters(BaseModel):
    use: Optional[str] = Field(
        None,
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


class ExternalActionWithoutParameters(BaseModel):
    use: Optional[str] = Field(
        None,
        description='The name of the external action.',
        title='Name of the external action.',
    )
    exclude_during: Optional[List[Lifecycle]] = Field(
        None,
        alias='exclude-during',
        description='Exclude this action during the specified parts of the lifetime of an exercise.',
        title='Exclude during',
    )


class Metadata(BaseModel):
    name: str = Field(
        ..., description='The name of the action.', examples=['rust-exercise-jobs']
    )
    description: str = Field(
        ...,
        description='Description of what this list of actions is supposed to achieve',
        examples=[
            'This actionfile contains the jobs that are executed during the CI of the rust-exercise.'
        ],
    )
    author: Author = Field(..., description='The author of the action.')
    targets: Optional[List[Target]] = Field(
        None, description='The targets of the action.'
    )


class ExternalAction(RootModel):
    root: Union[ExternalActionWithoutParameters, ExternalActionWithParameters] = Field(
        ...,
        description='External action that can be executed without parameters or with parameters.',
        title='External Action',
    )


class Action(RootModel):
    root: Union[ExternalAction, InternalAction] = Field(
        ..., description='Action that can be executed.', title='Action'
    )


class Steps(BaseModel):
    actions: Optional[Dict[constr(pattern=r'^[a-zA-Z0-9._-]+$'), Action]] = Field(
        None,
        description='The actions that are executed during a CI job in a target system. When a job is executed, the actions are executed in the order they are defined in the action.',
        title='Actions',
    )


class Actionfile(BaseModel):
    api: str = Field(
        ...,
        description='The API version of the action.',
        examples=['v0.0.1'],
        title='API Version',
    )
    metadata: Metadata
    steps: Steps
