import enum

from sqlalchemy.dialects.postgresql import ENUM


def pg_enum(enum_cls: type[enum.Enum], name: str) -> ENUM:
    """Mapeia um enum Python para um tipo ENUM que já existe no PostgreSQL."""
    return ENUM(
        enum_cls,
        name=name,
        create_type=False,
        values_callable=lambda e: [m.value for m in e],
    )


class AdPlatform(str, enum.Enum):
    META_ADS = "meta_ads"
    GOOGLE_ADS = "google_ads"
    TIKTOK_ADS = "tiktok_ads"


class AdAccountStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class AutonomyMode(str, enum.Enum):
    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"


class RuleMetric(str, enum.Enum):
    CPA = "cpa"
    ROAS = "roas"
    CTR = "ctr"
    SPEND = "spend"


class RuleOperator(str, enum.Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"


class RuleAction(str, enum.Enum):
    PAUSE = "pause"
    SCALE = "scale"
    NOTIFY = "notify"
    ALERT = "alert"


class AdStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    REMOVED = "removed"


class CreativeType(str, enum.Enum):
    IMAGE = "image"
    COPY = "copy"


class CreativeStatus(str, enum.Enum):
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    ADJUSTMENT_REQUESTED = "adjustment_requested"


class AgentActionType(str, enum.Enum):
    PAUSE = "pause"
    SCALE = "scale"
    GENERATE_CREATIVE = "generate_creative"
    SUGGEST = "suggest"
    NOTIFY = "notify"


class AgentActionStatus(str, enum.Enum):
    EXECUTED = "executed"
    PENDING_APPROVAL = "pending_approval"
    RECOMMENDED = "recommended"