from app.agent.context import AgentContext
from app.tools.marketing_tools import (
    AnalyzeMarketingGoalTool,
    CreateCreativeBriefTool,
    GenerateAdCopyTool,
    GenerateCampaignStrategyTool,
    GenerateHashtagsTool,
    GenerateInstagramCaptionTool,
    PrepareInstagramPostTool,
)

test_context = AgentContext(
    user_id=1,
    user_name="Gabriel",
    conversation_id=10,
)


def test_analyze_marketing_goal_sales():
    tool = AnalyzeMarketingGoalTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "goal_description": "Quero aumentar as vendas da minha loja de tênis",
            "target_audience": "Jovens de 18 a 30 anos",
            "industry_or_niche": "Calçados e Moda",
            "budget_range": "R$ 3.000 / mês",
        },
    )

    assert result["success"] is True
    analysis = result["analysis"]
    assert "Fundo de Funil" in analysis["funnel_stage"]
    assert any("ROAS" in kpi for kpi in analysis["recommended_kpis"])
    assert any("Meta Ads" in ch for ch in analysis["primary_channels"])


def test_analyze_marketing_goal_leads():
    tool = AnalyzeMarketingGoalTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "goal_description": "Preciso de mais contatos de leads no WhatsApp para minha consultoria",
        },
    )

    assert result["success"] is True
    assert "Leads" in result["analysis"]["funnel_stage"]
    assert any("CPL" in kpi for kpi in result["analysis"]["recommended_kpis"])


def test_generate_campaign_strategy():
    tool = GenerateCampaignStrategyTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "campaign_name": "Campanha Black Friday 2026",
            "objective": "Vendas diretas no e-commerce",
            "target_audience": "Clientes recorrentes e novos visitantes",
            "product_or_service": "Smartwatch Pro",
            "channels": ["meta_ads", "google_ads"],
            "duration_days": 30,
            "budget": 5000.0,
        },
    )

    assert result["success"] is True
    strategy = result["campaign_strategy"]
    assert strategy["campaign_name"] == "Campanha Black Friday 2026"
    assert len(strategy["funnel_phases"]) == 3
    assert "meta_ads" in strategy["budget_distribution"]
    assert strategy["total_budget"] == 5000.0


def test_generate_ad_copy():
    tool = GenerateAdCopyTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "product_or_service": "Curso de Inglês para Negócios",
            "offer": "Desconto de 40% na primeira mensalidade + mentoria",
            "target_audience": "Profissionais de tecnologia",
            "platform": "meta_ads",
            "tone": "profissional",
        },
    )

    assert result["success"] is True
    copy_data = result["ad_copy"]
    assert len(copy_data["headlines"]) >= 2
    assert len(copy_data["primary_texts"]) >= 2
    assert "Saiba Mais" in copy_data["recommended_ctas"]


def test_generate_instagram_caption():
    tool = GenerateInstagramCaptionTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "topic": "Como organizar as finanças da sua pequena empresa",
            "post_format": "carrossel",
            "target_audience": "Microempreendedores",
            "tone": "educativo",
            "call_to_action": "Salve este carrossel e comece a aplicar hoje!",
        },
    )

    assert result["success"] is True
    caption_data = result["caption_data"]
    assert caption_data["is_within_limit"] is True
    assert "Salve este carrossel" in caption_data["caption"]
    assert len(caption_data["caption"]) > 50


def test_generate_hashtags():
    tool = GenerateHashtagsTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "niche_or_topic": "fitness",
            "quantity": 8,
        },
    )

    assert result["success"] is True
    ht_data = result["hashtag_data"]
    assert ht_data["count"] == 8
    assert all(tag.startswith("#") for tag in ht_data["tags_list"])
    # Garante que tags banidas não entram
    assert not any("likeforlike" in tag for tag in ht_data["tags_list"])


def test_create_creative_brief():
    tool = CreateCreativeBriefTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "campaign_or_project_name": "Lançamento Coleção Outono",
            "asset_type": "video_reels",
            "objective": "Gerar curiosidade e tráfego para a bio",
            "target_audience": "Mulheres 25-45 anos",
            "key_message": "Elegância e conforto para todos os dias",
            "brand_guidelines": "Tons terrosos, fonte sem serifa",
        },
    )

    assert result["success"] is True
    brief = result["creative_brief"]
    assert brief["project_name"] == "Lançamento Coleção Outono"
    assert "9:16" in brief["technical_specs"]
    assert "hook_frame" in brief["visual_direction"]


def test_prepare_instagram_post_valid():
    tool = PrepareInstagramPostTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "caption": "Apresentamos nossa nova solução para gestão de equipes. Confira os benefícios!",
            "media_type": "IMAGE",
            "media_urls": ["https://cdn.exemplo.com/post1.png"],
            "hashtags": ["gestao", "produtividade", "negocios"],
            "scheduled_for": "2026-11-20T10:00:00",
        },
    )

    assert result["success"] is True
    preview = result["post_preview"]
    assert preview["valid"] is True
    assert "#gestao" in preview["final_caption"]
    assert preview["media_count"] == 1


def test_prepare_instagram_post_invalid_carousel():
    tool = PrepareInstagramPostTool()
    result = tool.validate_and_execute(
        test_context,
        {
            "caption": "Carrossel de teste",
            "media_type": "CAROUSEL",
            "media_urls": ["https://cdn.exemplo.com/only_one.png"],  # carrossel precisa de >= 2
        },
    )

    assert result["success"] is False
    assert any("mínimo 2" in issue for issue in result["post_preview"]["issues"])


def test_tool_parameter_validation_error():
    tool = GenerateCampaignStrategyTool()
    # Enviando payload sem campos obrigatórios
    result = tool.validate_and_execute(
        test_context,
        {"campaign_name": "Incompleta"},  # faltam objective, target_audience, channels...
    )

    assert result["success"] is False
    assert "Parâmetros inválidos" in result["error"]
    assert len(result["details"]) > 0

