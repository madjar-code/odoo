from ..choices import *
from pydantic import (
    BaseModel,
    HttpUrl,
    AnyUrl,
    constr,
)


class SteponeForm(BaseModel):
    linkedIn: HttpUrl
    file: AnyUrl
    introduction: str


class DefaultContactForm(BaseModel):
    message: str


class InstantForm(BaseModel):
    transport_car_from: constr(min_length=3,
                               max_length=255)
    transport_car_to: constr(min_length=3,
                             max_length=255)
    transport_car_type: TransportCarType


class QuestionForm(BaseModel):
    communication_with: constr(min_length=3,
                               max_length=100)
    message: str


class RequestQuoteForm(BaseModel):
    transportation_type: TransportationType
    equipment_type: EquipmentType
    vehicle_type: VehicleType
    note: str


class ReviewForm(BaseModel):
    rate: RateChoice
