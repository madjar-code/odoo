import re
from typing import (
    Optional,
)
from pydantic import (
    BaseModel,
    EmailStr,
    constr,
    validator,
    create_model,
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


def create_lead_form_schema(form_schema: BaseModel):
    return create_model('LeadFormSchema', lead=(Lead, ...), form=(form_schema, ...))


LeadSteponeFormSchema = create_lead_form_schema(SteponeForm)
LeadQuestionFormSchema = create_lead_form_schema(QuestionForm)
LeadInstantFormSchema = create_lead_form_schema(InstantForm)
LeadReviewFormSchema = create_lead_form_schema(ReviewForm)
LeadRequestQuoteFormSchema = create_lead_form_schema(RequestQuoteForm)
LeadDefaultContactFormSchema = create_lead_form_schema(DefaultContactForm)
