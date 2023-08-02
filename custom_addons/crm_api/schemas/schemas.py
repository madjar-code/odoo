import re
from typing import (
    Optional,
)
from pydantic import (
    BaseModel,
    AnyUrl,
    EmailStr,
    constr,
    validator,
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

    @validator('website')
    def validate_url(cls, v):
        url_pattern = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')
        if not url_pattern.match(v):
            raise ValueError('Incorrect URL')
        return v


class LeadFormSchema(BaseModel):
    lead: Lead
    form: SteponeForm
