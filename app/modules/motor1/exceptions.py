"""Excecoes do Motor 1."""


class Motor1Error(Exception):
    """Erro base do Motor 1."""


class EquipeNaoEncontradaError(Motor1Error):
    """Equipe solicitada nao existe no banco."""
