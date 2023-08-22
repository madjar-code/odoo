import re
from typing import (
    Optional,
)
from pydantic import (
    BaseModel,
    EmailStr,
    validator,
    constr,
    create_model,
)
from ...stepone.schemas.forms import (
    SteponeForm,
    DefaultContactForm,
    InstantForm,
    QuestionForm,
    RequestQuoteForm,
    ReviewForm,
)


class LeadSchema(BaseModel):
    name: str = 'Lead Name'
    website: str = 'https://example.com/'
    email_from: EmailStr = 'test@test.com'
    phone: constr(min_length=10,
                  max_length=18) = '88005553535'
    company_id: Optional[int] = 1
    user_id: Optional[int] = 1
    country_id: Optional[int] = None
    team_id: Optional[int] = None
    city: str = 'Chisinau'

    @validator('website')
    def validate_url(cls, url: str) -> str:
        url_pattern = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')
        if not url_pattern.match(url):
            raise ValueError('Incorrect URL')
        return url


def create_lead_form_schema(form_schema: BaseModel):
    return create_model('LeadFormSchema', lead=(LeadSchema, ...), form=(form_schema, ...))


LeadSteponeFormSchema = create_lead_form_schema(SteponeForm)
LeadQuestionFormSchema = create_lead_form_schema(QuestionForm)
LeadInstantFormSchema = create_lead_form_schema(InstantForm)
LeadReviewFormSchema = create_lead_form_schema(ReviewForm)
LeadRequestQuoteFormSchema = create_lead_form_schema(RequestQuoteForm)
LeadDefaultContactFormSchema = create_lead_form_schema(DefaultContactForm)
