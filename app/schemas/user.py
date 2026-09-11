from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

# Schema for user creation request
class UserCreate(UserBase):
    password: str

# Schema for API responses (returns user data without password)
class UserResponse(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)