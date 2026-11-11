from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TradeBase(BaseModel):
    symbol: str = Field(min_length=1)
    direction: Literal["long", "short"]
    entry: float
    stop: float | None = None
    exit: float
    pnl: float
    entry_datetime: datetime
    exit_datetime: datetime

    @model_validator(mode="after")
    def validate_trade(self):
        if self.exit_datetime < self.entry_datetime:
            raise ValueError("Exit datetime cannot be before entry datetime")

        if self.stop is not None and self.entry == self.stop:
            raise ValueError("Entry and stop cannot be the same")

        return self


class TradeCreate(TradeBase):
    account_id: int


class TradeUpdate(TradeBase):
    pass


class TradeResponse(BaseModel):
    id: int
    account_id: int
    symbol: str
    direction: Literal["long", "short"]
    entry: float
    stop: float | None = None
    exit: float
    result: float | None = None
    pnl: float
    entry_datetime: datetime
    exit_datetime: datetime


class PaginatedTradesResponse(BaseModel):
    items: list[TradeResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
