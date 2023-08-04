from enum import Enum


class TransportCarType(str, Enum):
    car = 'Car'
    suv = 'SUV'
    pickup = 'Pickup'
    van = 'Van'
    moto = 'Moto'
    rv = 'RV'
    heavy_equipment = 'Heavy Equipment'
    general_freight = 'General Freight'


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


class RateChoice(str, Enum):
    one = '1'
    two = '2'
    three = '3'
    four = '4'
    five = '5'
    six = '6'
    seven = '7'
    eight = '8'
    nine = '9'
    ten = '10'
