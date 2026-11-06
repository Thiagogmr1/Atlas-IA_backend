import logging
from sqlalchemy import text
from app.core.database import engine, Base
from app import models
from app.models.enums import (
    AdAccountStatus,
    AdPlatform,
    AdStatus,
    AgentActionStatus,
    AgentActionType,
    AutonomyMode,
    CampaignStatus,
    CreativeStatus,
    CreativeType,
    MessageRole,
    RuleAction,
    RuleMetric,
    RuleOperator,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENUMS = [
    ("ad_platform", AdPlatform),
    ("ad_account_status", AdAccountStatus),
    ("campaign_status", CampaignStatus),
    ("autonomy_mode", AutonomyMode),
    ("rule_metric", RuleMetric),
    ("rule_operator", RuleOperator),
    ("rule_action", RuleAction),
    ("ad_status", AdStatus),
    ("creative_type", CreativeType),
    ("creative_status", CreativeStatus),
    ("agent_action_type", AgentActionType),
    ("agent_action_status", AgentActionStatus),
    ("message_role", MessageRole),
]


def init_database():
    with engine.connect() as conn:
        logger.info("Criando tipos ENUM se não existirem...")
        for enum_name, enum_cls in ENUMS:
            values = ", ".join(f"'{m.value}'" for m in enum_cls)
            check_sql = text(
                f"SELECT 1 FROM pg_type WHERE typname = '{enum_name}'"
            )
            exists = conn.execute(check_sql).first()
            if not exists:
                create_sql = text(f"CREATE TYPE {enum_name} AS ENUM ({values});")
                conn.execute(create_sql)
                logger.info(f"Tipo ENUM '{enum_name}' criado com sucesso.")
            else:
                logger.info(f"Tipo ENUM '{enum_name}' já existe.")
        conn.commit()

    logger.info("Criando tabelas do banco de dados...")
    Base.metadata.create_all(bind=engine)
    logger.info("Todas as tabelas foram criadas com sucesso!")


if __name__ == "__main__":
    init_database()
