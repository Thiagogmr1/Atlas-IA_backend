import re
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.agent.context import AgentContext
from app.integrations.instagram import InstagramIntegration, InstagramPostPayload
from app.tools.base import AgentTool

# ==============================================================================
# 1. analyze_marketing_goal
# ==============================================================================
class AnalyzeMarketingGoalArgs(BaseModel):
    goal_description: str = Field(..., description="Descrição do objetivo de marketing do usuário")
    target_audience: Optional[str] = Field(default=None, description="Público-alvo pretendido")
    industry_or_niche: Optional[str] = Field(default=None, description="Segmento de mercado ou nicho")
    budget_range: Optional[str] = Field(default=None, description="Faixa orçamentária disponível")


class AnalyzeMarketingGoalTool(AgentTool):
    name = "analyze_marketing_goal"
    description = (
        "Analisa um objetivo de marketing (ex: gerar leads, vendas, reconhecimento, engajamento) "
        "e define estratégia de funil, KPIs recomendados e canais prioritários."
    )
    args_schema = AnalyzeMarketingGoalArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        goal = kwargs.get("goal_description", "").lower()
        niche = kwargs.get("industry_or_niche") or "Geral"
        audience = kwargs.get("target_audience") or "Consumidores qualificados"
        budget = kwargs.get("budget_range") or "Sob definição"

        # Identificação de fase do funil e KPIs
        if any(term in goal for term in ["venda", "comprar", "conversão", "receita", "faturamento"]):
            funnel_stage = "Fundo de Funil (Conversão / Vendas)"
            kpis = ["ROAS (Retorno sobre Gasto com Anúncios)", "CPA (Custo por Aquisição)", "Taxa de Conversão", "Ticket Médio"]
            recommended_channels = ["Meta Ads (Campanhas de Conversão)", "Google Ads (Search e Shopping)", "Instagram Direct"]
        elif any(term in goal for term in ["lead", "contato", "orçamento", "whatsapp", "cadastro"]):
            funnel_stage = "Meio de Funil (Geração de Leads / Qualificação)"
            kpis = ["CPL (Custo por Lead)", "Taxa de Resposta no WhatsApp", "Leads Qualificados (MQL)", "Taxa de Preenchimento"]
            recommended_channels = ["Meta Ads (Leads nativos e WhatsApp)", "Google Ads Search", "Landing Pages otimizadas"]
        elif any(term in goal for term in ["reconhecimento", "marca", "alcance", "visibilidade", "branding"]):
            funnel_stage = "Topo de Funil (Atração e Brand Awareness)"
            kpis = ["CPM (Custo por Mil Impressões)", "Alcance Único", "Taxa de Visualização de Vídeo", "Custo por Visualização"]
            recommended_channels = ["Instagram Reels", "TikTok Ads", "Meta Ads (Alcance e Vídeo Views)"]
        else:
            funnel_stage = "Engajamento e Comunidade (Topo/Meio de Funil)"
            kpis = ["Taxa de Engajamento", "Comentários e Compartilhamentos", "Crescimento de Seguidores", "Cliques no Link da Bio"]
            recommended_channels = ["Instagram Feed e Carrosséis", "Instagram Stories", "TikTok Orgânico"]

        return {
            "success": True,
            "analysis": {
                "objective": kwargs.get("goal_description"),
                "niche": niche,
                "target_audience": audience,
                "budget_range": budget,
                "funnel_stage": funnel_stage,
                "recommended_kpis": kpis,
                "primary_channels": recommended_channels,
                "strategic_summary": (
                    f"Estratégia focada em {funnel_stage} para o nicho de {niche}. "
                    f"Priorizar canais {', '.join(recommended_channels[:2])} com foco nos KPIs: {', '.join(kpis[:2])}."
                ),
            },
        }


# ==============================================================================
# 2. generate_campaign_strategy
# ==============================================================================
class GenerateCampaignStrategyArgs(BaseModel):
    campaign_name: str = Field(..., description="Nome de identificação da campanha")
    objective: str = Field(..., description="Objetivo principal (ex: vendas, leads, tráfego)")
    target_audience: str = Field(..., description="Descrição do público-alvo")
    product_or_service: str = Field(..., description="Produto ou serviço promovido")
    channels: List[str] = Field(..., description="Lista de canais selecionados (ex: instagram, meta_ads, google_ads)")
    duration_days: Optional[int] = Field(default=30, ge=1, le=180, description="Duração estimada da campanha em dias")
    budget: Optional[float] = Field(default=None, ge=0, description="Orçamento total previsto em reais")


class GenerateCampaignStrategyTool(AgentTool):
    name = "generate_campaign_strategy"
    description = (
        "Gera um planejamento estratégico completo para campanha de marketing com fases do funil, "
        "divisão de canais e marcos de sucesso."
    )
    args_schema = GenerateCampaignStrategyArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        channels = kwargs.get("channels", [])
        budget = kwargs.get("budget")
        duration = kwargs.get("duration_days", 30)

        # Distribuição de orçamento sugerida
        budget_split = {}
        if budget:
            if len(channels) == 1:
                budget_split[channels[0]] = budget
            else:
                primary_share = round(budget * 0.65, 2)
                secondary_share = round((budget - primary_share) / max(1, len(channels) - 1), 2)
                for idx, ch in enumerate(channels):
                    budget_split[ch] = primary_share if idx == 0 else secondary_share

        phases = [
            {
                "phase": "Fase 1: Aquecimento e Atração (Dias 1 a 7)",
                "focus": "Apresentação da dor/necessidade e posicionamento da oferta.",
                "creative_types": ["Reels de conscientização", "Carrosséis educativos", "Anúncios em vídeo curto"],
            },
            {
                "phase": f"Fase 2: Engajamento e Consideração (Dias 8 a {int(duration * 0.7)})",
                "focus": "Demonstração de benefícios, prova social e quebra de objeções.",
                "creative_types": ["Depoimentos", "Estudos de caso / Antes e Depois", "Carrossel de quebra de objeções"],
            },
            {
                "phase": f"Fase 3: Conversão e Remarketing (Dias {int(duration * 0.7) + 1} a {duration})",
                "focus": "Oferta direta, escassez, bônus e urgência para conversão final.",
                "creative_types": ["Anúncios de remarketing para quem interagiu", "Chamadas diretas com CTA urgente"],
            },
        ]

        return {
            "success": True,
            "campaign_strategy": {
                "campaign_name": kwargs.get("campaign_name"),
                "product_or_service": kwargs.get("product_or_service"),
                "target_audience": kwargs.get("target_audience"),
                "objective": kwargs.get("objective"),
                "duration_days": duration,
                "total_budget": budget,
                "budget_distribution": budget_split if budget else "Orçamento flexível por fase",
                "funnel_phases": phases,
                "next_steps": [
                    "Criar briefings criativos para as peças da Fase 1",
                    "Redigir copies para os primeiros anúncios",
                    "Configurar públicos-alvo e pixel de rastreamento",
                ],
            },
        }


# ==============================================================================
# 3. generate_ad_copy
# ==============================================================================
class GenerateAdCopyArgs(BaseModel):
    product_or_service: str = Field(..., description="Nome e descrição do produto ou serviço")
    offer: str = Field(..., description="Oferta ou proposta de valor principal")
    target_audience: str = Field(..., description="Público-alvo do anúncio")
    platform: str = Field(..., description="Plataforma de anúncio: instagram, facebook, meta_ads, google_ads ou tiktok")
    tone: Optional[str] = Field(default="persuasivo", description="Tom de voz: persuasivo, urgente, profissional, descontraído")
    format: Optional[str] = Field(default="feed", description="Formato do anúncio: feed, stories, reels, search")


class GenerateAdCopyTool(AgentTool):
    name = "generate_ad_copy"
    description = (
        "Gera textos persuasivos de anúncios (headlines, corpo do texto, chamadas para ação CTA) "
        "com gatilhos mentais adaptados para Meta Ads, Google Ads ou TikTok Ads."
    )
    args_schema = GenerateAdCopyArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        product = kwargs.get("product_or_service")
        offer = kwargs.get("offer")
        audience = kwargs.get("target_audience")
        platform = kwargs.get("platform", "meta_ads").lower()
        tone = kwargs.get("tone", "persuasivo")

        headlines = [
            f"Descubra como transformar seus resultados com {product}",
            f"{offer}: a oportunidade ideal para {audience}",
            f"Chega de perder tempo: conheça {product}",
        ]

        primary_texts = [
            (
                f"Se você é {audience} e busca resultados reais, precisa conhecer {product}.\n\n"
                f"Com {offer}, você tem exatamente o que precisa para avançar com confiança. "
                f"Milhares de pessoas já comprovaram a diferença no dia a dia.\n\n"
                f"👉 Toque no botão abaixo e aproveite as condições especiais agora mesmo!"
            ),
            (
                f"Você ainda está enfrentando dificuldades para conseguir bons resultados?\n\n"
                f"Apresentamos {product}: desenvolvido especificamente para atender {audience}. "
                f"E por tempo limitado: {offer}.\n\n"
                f"Não deixe para depois. Clique em Saiba Mais e garanta o seu!"
            ),
        ]

        ctas = ["Saiba Mais", "Comprar Agora", "Garantir Oferta", "Fale Conosco no WhatsApp"]

        return {
            "success": True,
            "ad_copy": {
                "platform": platform,
                "tone": tone,
                "headlines": headlines,
                "primary_texts": primary_texts,
                "recommended_ctas": ctas,
                "psychological_triggers_applied": ["Autoridade", "Prova Social", "Urgência", "Benefício Direto"],
                "character_check": {
                    "headline_max_chars": 40 if "google" in platform else 125,
                    "primary_text_length": len(primary_texts[0]),
                },
            },
        }


# ==============================================================================
# 4. generate_instagram_caption
# ==============================================================================
class GenerateInstagramCaptionArgs(BaseModel):
    topic: str = Field(..., description="Tema ou assunto do post")
    post_format: str = Field(..., description="Formato: reels, feed_imagem, carrossel ou stories")
    target_audience: Optional[str] = Field(default=None, description="Público-alvo")
    tone: Optional[str] = Field(default="educativo", description="Tom de voz: educativo, inspiracional, divertido, vendedor")
    call_to_action: Optional[str] = Field(default=None, description="CTA desejada no final")


class GenerateInstagramCaptionTool(AgentTool):
    name = "generate_instagram_caption"
    description = (
        "Cria legendas envolventes para posts do Instagram (Feed, Reels, Carrossel) "
        "com gancho inicial, narrativa, quebras de linha e CTA."
    )
    args_schema = GenerateInstagramCaptionArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        topic = kwargs.get("topic")
        post_format = kwargs.get("post_format", "feed_imagem")
        tone = kwargs.get("tone", "educativo")
        cta = kwargs.get("call_to_action") or "Salve este post para consultar depois e compartilhe com um amigo!"

        hook = f"Você já percebeu o impacto de {topic} no seu dia a dia? 👇"
        body = (
            f"Muitas pessoas tentam resolver isso de forma complicada, mas a verdade é que dominar {topic} "
            f"exige consistência e a estratégia certa.\n\n"
            f"Aqui estão 3 pontos essenciais que você não pode ignorar:\n"
            f"1️⃣ Clareza nos objetivos iniciais;\n"
            f"2️⃣ Aplicação prática passo a passo;\n"
            f"3️⃣ Medição constante dos resultados para ajustar o rumo."
        )

        full_caption = f"{hook}\n\n{body}\n\n💬 {cta}"

        return {
            "success": True,
            "caption_data": {
                "post_format": post_format,
                "tone": tone,
                "hook": hook,
                "caption": full_caption,
                "character_count": len(full_caption),
                "is_within_limit": len(full_caption) <= 2200,
            },
        }


# ==============================================================================
# 5. generate_hashtags
# ==============================================================================
class GenerateHashtagsArgs(BaseModel):
    niche_or_topic: str = Field(..., description="Nicho, tema ou palavra-chave")
    target_audience: Optional[str] = Field(default=None, description="Público-alvo para refinamento")
    quantity: Optional[int] = Field(default=10, ge=3, le=30, description="Quantidade de hashtags desejadas")
    category: Optional[str] = Field(default="geral", description="Categoria do nicho")


class GenerateHashtagsTool(AgentTool):
    name = "generate_hashtags"
    description = (
        "Pesquisa e organiza hashtags estratégicas para Instagram categorizadas por nicho, "
        "alcance e comunidade, filtrando tags banidas."
    )
    args_schema = GenerateHashtagsArgs

    # Conjunto de palavras que geram shadowban ou violação
    BANNED_KEYWORDS = {"followforfollow", "likeforlike", "f4f", "l4l", "tagsforlikes", "instafollow"}

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        topic = kwargs.get("niche_or_topic", "marketing").strip()
        clean_base = re.sub(r"[^a-zA-Z0-9_áéíóúãõçÁÉÍÓÚÃÕÇ]", "", topic).lower()
        qty = kwargs.get("quantity", 10)

        # Geração de hashtags por faixas de volume
        broad_tags = [f"#{clean_base}", f"#{clean_base}brasil", "#dicasdemarketing", "#empreendedorismo", "#negociosonline"]
        niche_tags = [f"#{clean_base}estrategico", f"#estrategiade{clean_base}", f"#conteudode{clean_base}", f"#gestaode{clean_base}"]
        community_tags = [f"#comunidade{clean_base}", "#vendasdiarias", "#marketingdeconteudo", "#crescimentoonline"]

        all_candidates = broad_tags + niche_tags + community_tags
        # Filtra tags banidas
        filtered = [tag for tag in all_candidates if not any(banned in tag.lower() for banned in self.BANNED_KEYWORDS)]
        
        selected = filtered[:qty]

        return {
            "success": True,
            "hashtag_data": {
                "topic": topic,
                "count": len(selected),
                "tags_list": selected,
                "formatted_block": " ".join(selected),
                "breakdown": {
                    "broad_reach": [t for t in selected if t in broad_tags],
                    "targeted_niche": [t for t in selected if t in niche_tags],
                    "community": [t for t in selected if t in community_tags],
                },
                "instagram_best_practice_note": "O Instagram recomenda entre 5 a 15 hashtags hiper-relevantes no corpo ou primeiro comentário.",
            },
        }


# ==============================================================================
# 6. create_creative_brief
# ==============================================================================
class CreateCreativeBriefArgs(BaseModel):
    campaign_or_project_name: str = Field(..., description="Nome da campanha ou projeto")
    asset_type: str = Field(..., description="Tipo de peça: imagem_estatica, carrossel, video_reels ou banner_google")
    objective: str = Field(..., description="Objetivo específico desta peça criativa")
    target_audience: str = Field(..., description="Público que deve ser impactado")
    key_message: str = Field(..., description="Mensagem principal ou gancho visual")
    brand_guidelines: Optional[str] = Field(default=None, description="Diretrizes da marca (cores, fontes, tom)")
    dimensions_or_specs: Optional[str] = Field(default=None, description="Dimensões (ex: 1080x1080, 1080x1920)")


class CreateCreativeBriefTool(AgentTool):
    name = "create_creative_brief"
    description = (
        "Gera um briefing criativo estruturado para designers ou editores de vídeo criarem "
        "peças visuais alinhadas à campanha."
    )
    args_schema = CreateCreativeBriefArgs

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        asset_type = kwargs.get("asset_type")
        specs = kwargs.get("dimensions_or_specs")

        if not specs:
            if "reels" in asset_type or "stories" in asset_type:
                specs = "1080x1920 pixels (Aspect Ratio 9:16 vertical)"
            elif "carrossel" in asset_type:
                specs = "1080x1350 pixels (Aspect Ratio 4:5 retrato) ou 1080x1080 (1:1)"
            else:
                specs = "1080x1080 pixels (Aspect Ratio 1:1 quadrado)"

        brief = {
            "project_name": kwargs.get("campaign_or_project_name"),
            "asset_type": asset_type,
            "technical_specs": specs,
            "objective": kwargs.get("objective"),
            "target_audience": kwargs.get("target_audience"),
            "key_message": kwargs.get("key_message"),
            "brand_guidelines": kwargs.get("brand_guidelines") or "Seguir paleta de cores institucional e tipografia limpa.",
            "visual_direction": {
                "hook_frame": "Os primeiros 3 segundos ou visual central devem capturar atenção imediata.",
                "text_on_screen": "Manter texto conciso, respeitando zona de segurança (sem sobrepor interface do Instagram).",
                "cta_placement": "Inserir CTA claro no fechamento da peça visual.",
            },
            "checklist_before_delivery": [
                "Verificar legibilidade do texto em telas de smartphone",
                "Garantir conformidade com paleta de cores",
                "Confirmar proporção e resolução corretas",
            ],
        }

        return {
            "success": True,
            "creative_brief": brief,
        }


# ==============================================================================
# 7. prepare_instagram_post
# ==============================================================================
class PrepareInstagramPostArgs(BaseModel):
    caption: str = Field(..., max_length=2200, description="Legenda do post (máx 2200 caracteres)")
    media_type: str = Field(..., description="IMAGE, VIDEO ou CAROUSEL")
    media_urls: List[str] = Field(..., min_length=1, description="Lista de URLs de imagens ou vídeos")
    hashtags: Optional[List[str]] = Field(default=None, description="Lista opcional de hashtags")
    scheduled_for: Optional[str] = Field(default=None, description="Data/hora de agendamento em formato ISO (YYYY-MM-DDTHH:MM:SS)")
    location_tag: Optional[str] = Field(default=None, description="Nome do local marcado")


class PrepareInstagramPostTool(AgentTool):
    name = "prepare_instagram_post"
    description = (
        "Valida e prepara a publicação de um post para Instagram, checando limites de legenda, "
        "formatação de mídia e hashtags antes de agendar."
    )
    args_schema = PrepareInstagramPostArgs

    def __init__(self, instagram_integration: InstagramIntegration | None = None):
        self.integration = instagram_integration or InstagramIntegration()

    def execute(self, context: AgentContext, **kwargs) -> dict[str, Any]:
        scheduled_dt = None
        raw_scheduled = kwargs.get("scheduled_for")
        if raw_scheduled:
            try:
                scheduled_dt = datetime.fromisoformat(raw_scheduled.replace("Z", "+00:00"))
            except ValueError:
                return {
                    "success": False,
                    "error": "Formato inválido de data em scheduled_for. Use o padrão ISO: YYYY-MM-DDTHH:MM:SS",
                }

        payload = InstagramPostPayload(
            caption=kwargs.get("caption", ""),
            media_type=kwargs.get("media_type", "IMAGE"),
            media_urls=kwargs.get("media_urls", []),
            hashtags=kwargs.get("hashtags"),
            scheduled_for=scheduled_dt,
            location_tag=kwargs.get("location_tag"),
        )

        result = self.integration.validate_post(payload)
        return {
            "success": result["valid"],
            "post_preview": result,
            "user_id": context.user_id,
            "conversation_id": context.conversation_id,
        }


def register_marketing_tools(registry: Any) -> None:
    """Registra as 7 ferramentas de marketing no registry."""
    registry.register(AnalyzeMarketingGoalTool())
    registry.register(GenerateCampaignStrategyTool())
    registry.register(GenerateAdCopyTool())
    registry.register(GenerateInstagramCaptionTool())
    registry.register(GenerateHashtagsTool())
    registry.register(CreateCreativeBriefTool())
    registry.register(PrepareInstagramPostTool())

