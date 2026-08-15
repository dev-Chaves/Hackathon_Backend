"""Popula uma montadora ficticia com dados de demonstracao.

Revision ID: 20260815_0002
Revises: 20260814_0001
Create Date: 2026-08-15

Os registros sao deterministas, claramente identificados como mock e gerados em lote pelo
PostgreSQL. Nenhum dado pessoal real e utilizado.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0002"
down_revision: str | None = "20260814_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    script = """
            INSERT INTO areas (id, nome, descricao)
            SELECT
                md5('nissa-mock-area-' || ordinalidade)::uuid,
                nome,
                'Area industrial ficticia da Nissa Motors para demonstracao.'
            FROM (
                VALUES
                    (1, 'Nissa - Estamparia'),
                    (2, 'Nissa - Carroceria e Solda'),
                    (3, 'Nissa - Pintura'),
                    (4, 'Nissa - Montagem Final'),
                    (5, 'Nissa - Powertrain'),
                    (6, 'Nissa - Qualidade'),
                    (7, 'Nissa - Logistica Interna'),
                    (8, 'Nissa - Manutencao Industrial')
            ) AS dados(ordinalidade, nome);

            INSERT INTO equipes (id, nome, descricao)
            SELECT
                md5('nissa-mock-equipe-' || n)::uuid,
                'Nissa - Equipe ' || lpad(n::text, 2, '0'),
                'Equipe operacional ficticia da Nissa Motors.'
            FROM generate_series(1, 30) AS serie(n);

            INSERT INTO habilidades (id, nome, categoria, criticidade)
            SELECT
                md5('nissa-mock-habilidade-' || ordinalidade)::uuid,
                nome,
                categoria,
                criticidade
            FROM (
                VALUES
                    (1, 'Solda MIG/MAG', 'Soldagem', 5),
                    (2, 'Solda por Ponto Robotizada', 'Soldagem', 5),
                    (3, 'Operacao de Prensa', 'Estamparia', 5),
                    (4, 'Troca de Ferramental', 'Setup', 4),
                    (5, 'Programacao de Robo Industrial', 'Automacao', 5),
                    (6, 'Operacao de Cabine de Pintura', 'Pintura', 5),
                    (7, 'Preparacao de Superficie', 'Pintura', 4),
                    (8, 'Montagem de Chassi', 'Montagem', 4),
                    (9, 'Montagem de Interior', 'Montagem', 3),
                    (10, 'Instalacao Eletrica Veicular', 'Eletrica', 5),
                    (11, 'Montagem de Motor', 'Powertrain', 5),
                    (12, 'Teste de Estanqueidade', 'Qualidade', 4),
                    (13, 'Inspecao Visual', 'Qualidade', 3),
                    (14, 'Metrologia Dimensional', 'Qualidade', 5),
                    (15, 'Operacao de Empilhadeira', 'Logistica', 4),
                    (16, 'Abastecimento de Linha', 'Logistica', 3),
                    (17, 'Manutencao Mecanica', 'Manutencao', 5),
                    (18, 'Manutencao Eletrica', 'Manutencao', 5),
                    (19, 'Bloqueio e Etiquetagem LOTO', 'Seguranca', 5),
                    (20, 'Trabalho Padronizado', 'Producao', 3)
            ) AS dados(ordinalidade, nome, categoria, criticidade);

            INSERT INTO linhas (id, nome, area_id, meta_diaria)
            SELECT
                md5('nissa-mock-linha-' || n)::uuid,
                'Nissa - Linha ' || lpad(n::text, 2, '0'),
                md5('nissa-mock-area-' || (((n - 1) % 8) + 1))::uuid,
                180 + ((n * 17) % 220)
            FROM generate_series(1, 24) AS serie(n);

            INSERT INTO postos (id, codigo, nome, linha_id, criticidade)
            SELECT
                md5('nissa-mock-posto-' || n)::uuid,
                'NIS-P' || lpad(n::text, 4, '0'),
                'Posto Operacional ' || lpad(n::text, 4, '0'),
                md5('nissa-mock-linha-' || (((n - 1) / 50) + 1))::uuid,
                1 + ((n * 7) % 5)
            FROM generate_series(1, 1200) AS serie(n);

            INSERT INTO funcionarios (
                id,
                matricula,
                nome,
                cpf,
                sexo,
                data_nascimento,
                data_admissao,
                area_id,
                equipe_id,
                turno,
                status,
                distancia_trabalho_km,
                tempo_deslocamento_min,
                possui_veiculo,
                tipo_transporte,
                criticidade_funcionario
            )
            SELECT
                md5('nissa-mock-funcionario-' || n)::uuid,
                'NISSA-MOCK-' || lpad(n::text, 5, '0'),
                'Colaborador Ficticio ' || lpad(n::text, 5, '0'),
                lpad((90000000000::bigint + n)::text, 11, '0'),
                CASE WHEN n % 2 = 0 THEN 'F' ELSE 'M' END,
                DATE '1970-01-01' + ((n * 37) % 10950),
                DATE '2006-01-01' + ((n * 29) % 7300),
                md5('nissa-mock-area-' || (((n - 1) % 8) + 1))::uuid,
                md5('nissa-mock-equipe-' || (((n - 1) % 30) + 1))::uuid,
                (ARRAY['TURNO_1', 'TURNO_2', 'TURNO_3'])[((n - 1) % 3) + 1],
                CASE
                    WHEN n % 100 < 93 THEN 'ATIVO'
                    WHEN n % 100 < 96 THEN 'FERIAS'
                    WHEN n % 100 < 98 THEN 'AFASTADO'
                    WHEN n % 100 < 99 THEN 'TREINAMENTO'
                    ELSE 'DESLIGADO'
                END::status_funcionario,
                (((n * 17) % 8000)::numeric / 100),
                10 + ((n * 13) % 111),
                n % 3 <> 0,
                (ARRAY['CARRO', 'MOTO', 'ONIBUS', 'FRETADO', 'UBER', 'BICICLETA', 'A_PE'])[
                    ((n - 1) % 7) + 1
                ]::tipo_transporte,
                1 + ((n * 11) % 5)
            FROM generate_series(1, 3000) AS serie(n);

            INSERT INTO postos_habilidades (id, posto_id, habilidade_id, nivel_minimo)
            SELECT
                md5('nissa-mock-posto-habilidade-' || posto_n || '-' || requisito_n)::uuid,
                md5('nissa-mock-posto-' || posto_n)::uuid,
                md5(
                    'nissa-mock-habilidade-' || (((posto_n + requisito_n * 7 - 2) % 20) + 1)
                )::uuid,
                CASE WHEN requisito_n = 1 THEN 3 + (posto_n % 2) ELSE 2 + (posto_n % 2) END
            FROM generate_series(1, 1200) AS postos(posto_n)
            CROSS JOIN generate_series(1, 2) AS requisitos(requisito_n);

            INSERT INTO funcionarios_habilidades (
                id,
                funcionario_id,
                habilidade_id,
                nivel,
                ultima_avaliacao,
                validade
            )
            SELECT
                md5('nissa-mock-funcionario-habilidade-' || funcionario_n || '-' || habilidade_n)::uuid,
                md5('nissa-mock-funcionario-' || funcionario_n)::uuid,
                md5(
                    'nissa-mock-habilidade-' || (((funcionario_n + habilidade_n * 3 - 2) % 20) + 1)
                )::uuid,
                1 + ((funcionario_n + habilidade_n * 2) % 5),
                DATE '2024-01-01' + ((funcionario_n * 11 + habilidade_n * 31) % 730),
                CASE
                    WHEN (funcionario_n + habilidade_n) % 10 = 0 THEN DATE '2025-12-31'
                    WHEN (funcionario_n + habilidade_n) % 10 = 1 THEN DATE '2026-09-30'
                    ELSE DATE '2027-12-31'
                END
            FROM generate_series(1, 3000) AS funcionarios(funcionario_n)
            CROSS JOIN generate_series(1, 5) AS habilidades(habilidade_n);

            INSERT INTO historicos_ausencia (
                id,
                funcionario_id,
                data_ausencia,
                tipo,
                motivo,
                justificada
            )
            SELECT
                md5('nissa-mock-ausencia-' || funcionario_n || '-' || ausencia_n)::uuid,
                md5('nissa-mock-funcionario-' || funcionario_n)::uuid,
                DATE '2025-01-01' + ((funcionario_n * 19 + ausencia_n * 43) % 590),
                (ARRAY['FALTA', 'ATESTADO', 'ACIDENTE', 'FERIAS', 'LICENCA', 'TREINAMENTO'])[
                    ((funcionario_n + ausencia_n - 2) % 6) + 1
                ]::tipo_ausencia,
                'Evento ficticio gerado para simulacao operacional.',
                (funcionario_n + ausencia_n) % 4 <> 0
            FROM generate_series(1, 3000) AS funcionarios(funcionario_n)
            CROSS JOIN LATERAL generate_series(1, funcionario_n % 4) AS ausencias(ausencia_n);

            INSERT INTO alocacoes (
                id,
                funcionario_id,
                posto_id,
                data_inicio,
                data_fim,
                ativo
            )
            SELECT
                md5('nissa-mock-alocacao-' || n)::uuid,
                md5('nissa-mock-funcionario-' || n)::uuid,
                md5('nissa-mock-posto-' || (((n - 1) % 1200) + 1))::uuid,
                DATE '2026-01-01' + ((n * 7) % 180),
                NULL,
                true
            FROM generate_series(1, 3000) AS serie(n)
            WHERE n % 100 < 93;
            """
    _execute_script(script)


def downgrade() -> None:
    script = """
            DELETE FROM alocacoes
            WHERE id IN (
                SELECT md5('nissa-mock-alocacao-' || n)::uuid
                FROM generate_series(1, 3000) AS serie(n)
            );

            DELETE FROM historicos_ausencia
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-MOCK-%'
            );

            DELETE FROM funcionarios_habilidades
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-MOCK-%'
            );

            DELETE FROM postos_habilidades
            WHERE posto_id IN (SELECT id FROM postos WHERE codigo LIKE 'NIS-P%');

            DELETE FROM funcionarios WHERE matricula LIKE 'NISSA-MOCK-%';
            DELETE FROM postos WHERE codigo LIKE 'NIS-P%';
            DELETE FROM linhas WHERE nome LIKE 'Nissa - Linha %';
            DELETE FROM habilidades
            WHERE id IN (
                SELECT md5('nissa-mock-habilidade-' || n)::uuid
                FROM generate_series(1, 20) AS serie(n)
            );
            DELETE FROM equipes WHERE nome LIKE 'Nissa - Equipe %';
            DELETE FROM areas WHERE nome LIKE 'Nissa - %';
            """
    _execute_script(script)


def _execute_script(script: str) -> None:
    """Executa cada comando separadamente para funcionar com o driver psycopg."""
    for statement in script.split(";"):
        if statement := statement.strip():
            op.execute(sa.text(statement))
