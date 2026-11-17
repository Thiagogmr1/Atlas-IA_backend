from app.tools.base import AgentTool
from app.tools.creative_studio_tools import (
    AdaptCreativeImageTool,
    AnalyzeUploadedMediaTool,
    GenerateAdvertisingImageTool,
    PublishInstagramPostTool,
)
from app.tools.instagram_agent_tools import (
    GenerateInstagramPostTool,
    GetInstagramAccountTool,
    GetInstagramConnectionTool,
    GetInstagramPublicationsTool,
)
from app.tools.marketing_tools import (
    AnalyzeMarketingGoalTool,
    CreateCreativeBriefTool,
    GenerateAdCopyTool,
    GenerateCampaignStrategyTool,
    GenerateHashtagsTool,
    GenerateInstagramCaptionTool,
    PrepareInstagramPostTool,
    register_marketing_tools,
)
from app.tools.registry import ToolRegistry, default_registry

# Registra as ferramentas no registro padrão
register_marketing_tools(default_registry)
default_registry.register(GenerateAdvertisingImageTool())
default_registry.register(AdaptCreativeImageTool())
default_registry.register(AnalyzeUploadedMediaTool())
default_registry.register(PublishInstagramPostTool())
default_registry.register(GetInstagramAccountTool())
default_registry.register(GetInstagramConnectionTool())
default_registry.register(GenerateInstagramPostTool())
default_registry.register(GetInstagramPublicationsTool())

__all__ = [
    "AgentTool",
    "ToolRegistry",
    "default_registry",
    "AnalyzeMarketingGoalTool",
    "GenerateCampaignStrategyTool",
    "GenerateAdCopyTool",
    "GenerateInstagramCaptionTool",
    "GenerateHashtagsTool",
    "CreateCreativeBriefTool",
    "PrepareInstagramPostTool",
    "GenerateAdvertisingImageTool",
    "AdaptCreativeImageTool",
    "AnalyzeUploadedMediaTool",
    "PublishInstagramPostTool",
    "GetInstagramAccountTool",
    "GetInstagramConnectionTool",
    "GenerateInstagramPostTool",
    "GetInstagramPublicationsTool",
    "register_marketing_tools",
]
