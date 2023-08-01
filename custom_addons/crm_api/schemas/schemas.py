from typing import (
    Dict,
    Optional,
)
from pydantic import (
    BaseModel,
    HttpUrl,
    EmailStr,
    constr,
)


class PropertyForm(BaseModel):
    name: str
    values: Dict[str, str]


class Lead(BaseModel):
    name: str
    website: HttpUrl
    email_from: EmailStr
    phone: constr(min_length=10, max_length=15)
    company_id: int
    user_id: int
    country_id: Optional[int]
    team_id: Optional[int]
    city: str
    form: PropertyForm

    class Config:
        from_attributes = True
