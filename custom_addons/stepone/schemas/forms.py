from typing import (
    Optional,
    AnyStr,
    List,
)
from pydantic import (
    BaseModel,
    HttpUrl,
    AnyUrl,
    constr,
    EmailStr,
    Field,
)
from ..choices import *


class SteponeForm(BaseModel):
    linkedIn: Optional[HttpUrl] = None
    file: Optional[AnyUrl] = None
    introduction: str = 'Test Intro Text'
    job: str = 'Driver'


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


class SubscribeForm(BaseModel):
    news_interested: List[AnyStr]
    email: EmailStr


class BusinessForm(BaseModel):
    type_of_equipment: int
    number_of_trucks: int
    time_in_business: int
    message: str
    percent: int = Field(..., ge=0, le=100)
