import re
from typing import (
    Optional,
)
from pydantic import (
    BaseModel,
    EmailStr,
    constr,
    validator,
)
from ...stepone.schemas.form import SteponeForm
from ...question.schemas.form import QuestionForm
from ...instant.schemas.form import InstantForm
from ...review.schemas.form import ReviewForm
from ...request_quote.schemas.form import RequestQuoteForm
from ...default_contact_form.schemas.form import DefaultContactForm


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
    def validate_url(cls, url):
        url_pattern = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')
        if not url_pattern.match(url):
            raise ValueError('Incorrect URL')
        return url


class LeadSteponeFormSchema(BaseModel):
    lead: Lead
    form: SteponeForm


class LeadQuestionFormSchema(BaseModel):
    lead: Lead
    form: QuestionForm


class LeadInstantFormSchema(BaseModel):
    lead: Lead
    form: InstantForm


class LeadReviewFormSchema(BaseModel):
    lead: Lead
    form: ReviewForm


class LeadRequestQuoteFormSchema(BaseModel):
    lead: Lead
    form: RequestQuoteForm


class LeadDefaultContactFormSchema(BaseModel):
    lead: Lead
    form: DefaultContactForm
