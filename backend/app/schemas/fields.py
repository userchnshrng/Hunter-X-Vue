from typing import Literal

from pydantic import Field, model_validator

from app.schemas import Input

Entity = Literal["candidate", "job"]


class FieldOption(Input):
    value: str = Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_-]+$")
    label: str = Field(min_length=1, max_length=100)


class FieldInput(Input):
    entity_type: Entity
    label: str = Field(min_length=1, max_length=100)
    value_type: Literal["text", "number", "date", "select"]
    options: list[FieldOption] = Field(default_factory=list, max_length=100)
    description: str = Field(default="", max_length=500)
    required: bool = False
    enabled: bool = True
    position: int = Field(default=0, ge=0, le=10000)

    @model_validator(mode="after")
    def valid_options(self):
        values = [item.value for item in self.options]
        if len(values) != len(set(values)):
            raise ValueError("单选项标识不能重复")
        if self.value_type == "select" and not values:
            raise ValueError("请至少添加一个单选项")
        if self.value_type != "select" and values:
            raise ValueError("只有单选字段可以设置选项")
        return self


class FieldUpdate(FieldInput):
    version: int = Field(ge=1)
