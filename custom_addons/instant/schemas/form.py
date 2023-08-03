from pydantic import (
    BaseModel,
    constr,
)


class InstantForm(BaseModel):
    transport_car_from: constr(min_length=3,
                               max_length=255)
    transport_car_to: constr(min_length=3,
                             max_length=255)
    transport_car_type: constr(min_length=3,
                               max_length=100)
