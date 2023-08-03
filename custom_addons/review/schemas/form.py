from pydantic import (
    BaseModel,
)


class ReviewForm(BaseModel):
    rate: str
