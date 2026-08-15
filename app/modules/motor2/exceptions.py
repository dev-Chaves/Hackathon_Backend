from uuid import UUID


class MatchmakingError(Exception):
    """Erro de dominio do matchmaking."""


class EmployeeNotFoundError(MatchmakingError):
    def __init__(self, funcionario_id: UUID) -> None:
        super().__init__(f"Funcionario {funcionario_id} nao encontrado.")


class ActiveAllocationNotFoundError(MatchmakingError):
    def __init__(self, funcionario_id: UUID) -> None:
        super().__init__(f"Funcionario {funcionario_id} nao possui alocacao ativa.")

