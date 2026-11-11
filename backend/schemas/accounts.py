from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    name: str = Field(min_length=1)
    starting_balance: float
    currency: str = Field(min_length=1)
    broker: str | None = None
    account_type: str | None = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(AccountBase):
    pass
