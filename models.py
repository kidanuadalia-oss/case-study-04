from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
import hashlib

class SurveySubmission(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=13, le=120)
    consent: bool = Field(..., description="Must be true to accept")
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(None, max_length=1000)
    user_agent: Optional[str] = Field(None, description="Browser or client identifier")
    submission_id: Optional[str] = Field(None, description="Idempotency key")
  

    @validator("comments")
    def _strip_comments(cls, v):
        return v.strip() if isinstance(v, str) else v

    @validator("consent")
    def _must_consent(cls, v):
        if v is not True:
            raise ValueError("consent must be true")
        return v
        
#Good example of inheritance
class StoredSurveyRecord(BaseModel):
    name: str
    consent: bool
    rating: int
    comments: Optional[str] = None
    user_agent: Optional[str] = None
    submission_id: Optional[str] = None
    received_at: datetime
    ip: str
    email_hash: str
    age_hash: str
    
    @classmethod
    def from_submission(cls, submission: SurveySubmission, received_at: datetime, ip: str, user_agent: Optional[str] = None):
        # Hash PII fields
        email_hash = hashlib.sha256(str(submission.email).encode()).hexdigest()
        age_hash = hashlib.sha256(str(submission.age).encode()).hexdigest()
        
        # Generate submission_id if not provided
        submission_id = submission.submission_id
        if not submission_id:
            # Create hash from email + current date-hour
            date_hour = received_at.strftime("%Y%m%d%H")
            submission_id = hashlib.sha256(f"{submission.email}{date_hour}".encode()).hexdigest()
        
        # Create dict with hashed PII
        data = submission.dict()
        data.update({
            'received_at': received_at,
            'ip': ip,
            'email_hash': email_hash,
            'age_hash': age_hash,
            'submission_id': submission_id,
            'user_agent': user_agent
        })
        
        # Remove original PII fields
        data.pop('email', None)
        data.pop('age', None)
        
        return cls(**data)
