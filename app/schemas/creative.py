from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import CreativeStatus, CreativeType


class CreativeCreate(BaseModel):
    type: CreativeType
    content_url: str = Field(min_length=1)


class CreativeReview(BaseModel):
    status: CreativeStatus

    @field_validator("status")
    @classmethod
    def must_be_a_decision(cls, value: CreativeStatus) -> CreativeStatus:
        if value == CreativeStatus.GENERATED:
            raise ValueError(
                "A avaliação deve ser approved, rejected ou adjustment_requested"
            )
        return value


class CreativeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    type: CreativeType
    content_url: str
    status: CreativeStatus
    generated_at: datetime