from typing import (
    Optional,
)
from pydantic import (
    BaseModel,
    HttpUrl,
    EmailStr,
    constr,
)
from ...stepone.schemas.form import SteponeForm


class Lead(BaseModel):
    name: str
    website: str
    email_from: EmailStr
    phone: constr(min_length=10, max_length=15)
    company_id: Optional[int]
    user_id: Optional[int]
    country_id: Optional[int]
    team_id: Optional[int]
    city: str


class LeadFormSchema(BaseModel):
    lead: Lead
    form: SteponeForm
