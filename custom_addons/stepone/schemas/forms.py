from enum import Enum
from typing import ClassVar
from pydantic import (
    BaseModel,
    HttpUrl,
    constr,
    validator,
)


class SteponeForm(BaseModel):
    linkedIn: HttpUrl = ...
    file: str = ...
    introduction: str = ...


class DefaultContactForm(BaseModel):
    message: str


class TransportCarType(str, Enum):
    car = 'Car'
    suv = 'SUV'
    pickup = 'Pickup'
    van = 'Van'
    moto = 'Moto'
    rv = 'RV'
    heavy_equipment = 'Heavy Equipment'
    general_freight = 'General Freight'


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


class TransportationType(str, Enum):
    D2D = 'Door-to-door'
    T2T = 'Terminal-to-terminal'


class EquipmentType(str, Enum):
    open_car_hauler = 'Open Car Hauler'
    enclosed_car_hauler = 'Enclosed Car Hauler'
    general_or_large_freight = 'General or Large Freight'


class VehicleType(str, Enum):
    car = 'Car'
    suv = 'SUV'
    pickup = 'Pickup'
    van = 'Van'
    moto = 'Moto'
    atv = 'ATV'
    rv = 'RV'
    heavy_equipment = 'Heavy Equipment'
    large_yacht = 'Large Yacht'
    travel_trailer = 'Travel Trailer'


class RequestQuoteForm(BaseModel):
    transportation_type: TransportationType
    equipment_type: EquipmentType
    vehicle_type: VehicleType
    note: str

    class Config:
       use_enum_values = True


class ReviewForm(BaseModel):
    RATE_CHOICES: ClassVar[list] = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    ]

    rate: constr(min_length=1, max_length=2)

    class Config:
        use_enum_values = True

    @validator('rate')
    def validate_rate(cls, rate):
        if rate not in [choice[0] for choice in cls.RATE_CHOICES]:
            raise ValueError('Invalid rate value. Must be between 1 and 10.')
        return rate
