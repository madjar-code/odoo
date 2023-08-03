from pydantic import (
    BaseModel,
)


class DefaultContactForm(BaseModel):
    message: str
