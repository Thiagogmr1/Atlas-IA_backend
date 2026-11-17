from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class InstagramConnectResponse(BaseModel):
    """Resposta com URL de autorização e state para início do fluxo OAuth."""
    auth_url: str
    state: str


class InstagramAccountRead(BaseModel):
    """Dados públicos e seguros da conta do Instagram conectada (NUNCA expõe tokens)."""
    model_config = ConfigDict(from_attributes=True)

    connected: bool
    instagram_user_id: Optional[str] = None
    username: Optional[str] = None
    profile_picture_url: Optional[str] = None
    connection_status: str = "disconnected"
    token_expires_at: Optional[datetime] = None
    scopes: Optional[str] = None
    created_at: Optional[datetime] = None


class InstagramPublishRequest(BaseModel):
    """Requisição para publicação de mídia no Instagram."""
    caption: str = Field(..., max_length=2200, description="Legenda da publicação")
    media_type: str = Field(..., description="Tipo de mídia: IMAGE, VIDEO, REELS ou CAROUSEL")
    media_urls: List[str] = Field(..., min_length=1, description="Lista de URLs de imagem ou vídeo")
    hashtags: Optional[List[str]] = Field(default=None, description="Hashtags opcionais")
    user_approval_confirmed: bool = Field(
        default=True,
        description="Confirmação explícita do usuário para publicação",
    )


class InstagramPublicationRead(BaseModel):
    """Detalhes da publicação registrada no banco de dados."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    integration_id: int
    instagram_media_id: Optional[str] = None
    media_type: str
    caption: str
    media_reference: str
    publication_status: str
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    @computed_field
    @property
    def instagram_post_url(self) -> Optional[str]:
        if self.instagram_media_id:
            return f"https://www.instagram.com/p/{self.instagram_media_id}/"
        return None
