from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=4, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)



class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=8)



class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: str = Field(min_length=4, max_length=100)