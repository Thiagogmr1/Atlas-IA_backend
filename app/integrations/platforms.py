from typing import Any, Dict


class MetaAdsIntegration:
    """Interface para futura integração com Meta Marketing API (Facebook e Instagram Ads)."""

    def check_campaign_readiness(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "platform": "meta_ads",
            "ready": True,
            "required_fields_present": all(k in campaign_data for k in ["name", "objective"]),
            "status": "ready_for_meta_graph_api",
        }


class GoogleAdsIntegration:
    """Interface para futura integração com Google Ads API."""

    def check_campaign_readiness(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "platform": "google_ads",
            "ready": True,
            "status": "ready_for_google_ads_api",
        }


class TikTokAdsIntegration:
    """Interface para futura integração com TikTok Marketing API."""

    def check_campaign_readiness(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "platform": "tiktok_ads",
            "ready": True,
            "status": "ready_for_tiktok_ads_api",
        }

