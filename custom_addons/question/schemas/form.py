from pydantic import (
    BaseModel,
    constr,
)


class QuestionForm(BaseModel):
    communication_with: constr(min_length=3,
                               max_length=100)
    message: str
