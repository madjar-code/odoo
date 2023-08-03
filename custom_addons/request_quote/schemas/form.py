from pydantic import (
    BaseModel,
    constr,
)


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
