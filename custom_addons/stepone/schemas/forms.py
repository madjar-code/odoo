from pydantic import (
    BaseModel,
    HttpUrl,
    constr,
)


class SteponeForm(BaseModel):
    linkedIn: HttpUrl = ...
    file: str = ...
    introduction: str = ...


class DefaultContactForm(BaseModel):
    message: str


class InstantForm(BaseModel):
    transport_car_from: constr(min_length=3,
                               max_length=255)
    transport_car_to: constr(min_length=3,
                             max_length=255)
    transport_car_type: constr(min_length=3,
                               max_length=100)


class QuestionForm(BaseModel):
    communication_with: constr(min_length=3,
                               max_length=100)
    message: str


class RequestQuoteForm(BaseModel):
    transportation_type: constr(min_length=1,
                               max_length=100)
    equipment_type: constr(min_length=1,
                           max_length=100)
    vehicle_type: constr(min_length=1,
                         max_length=100)
    note_type: constr(min_length=1,
                      max_length=100)
    note_type: str


class ReviewForm(BaseModel):
    rate: str
