from pydantic import (
    BaseModel,
    HttpUrl,
)


class SteponeForm(BaseModel):
    linkedIn: HttpUrl = ...
    file: str = ...
    introduction: str = ...
