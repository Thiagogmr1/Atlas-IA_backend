from typing import Set


class SecurityPermissionError(PermissionError):
    """Exceção para violações de segurança e acesso não autorizado."""
    pass


class UserIsolationError(SecurityPermissionError):
    """Tentativa de acesso a recursos pertencentes a outro usuário."""
    pass


def validate_tool_allowed(tool_name: str, allowed_tools: Set[str]) -> None:
    """Garante que a ferramenta solicitada pelo modelo está devidamente registrada e autorizada."""
    if not tool_name or tool_name not in allowed_tools:
        raise SecurityPermissionError(
            f"A ferramenta '{tool_name}' não é autorizada ou não existe."
        )


def validate_user_isolation(resource_user_id: int, authenticated_user_id: int) -> None:
    """Verifica se o recurso pertence ao usuário autenticado atual.
    
    Impede que dados de um usuário sejam acessados ou manipulados por outro.
    """
    if resource_user_id != authenticated_user_id:
        raise UserIsolationError(
            "Acesso negado: operação não permitida em dados de outro usuário."
        )

