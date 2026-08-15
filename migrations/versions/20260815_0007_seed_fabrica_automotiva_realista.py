"""Popula uma fabrica automotiva com equipes de dez pessoas.

Revision ID: 20260815_0007
Revises: 20260815_0006
Create Date: 2026-08-15

Distribuicao:
- 8 areas;
- 100 linhas;
- 3 equipes por linha, uma para cada turno;
- 10 postos por linha;
- 10 colaboradores por equipe, totalizando 3.000 pessoas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0007"
down_revision: str | None = "20260815_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    script = """
        INSERT INTO areas (id, nome, descricao)
        SELECT
            md5('automotiva-real-area-' || ordinalidade)::uuid,
            nome,
            descricao
        FROM (
            VALUES
                (1, 'Estamparia', 'Conformacao de paineis e componentes metalicos.'),
                (2, 'Carroceria', 'Soldagem e uniao estrutural da carroceria.'),
                (3, 'Pintura', 'Tratamento de superficie e pintura automotiva.'),
                (4, 'Montagem Final', 'Montagem de acabamento e componentes finais.'),
                (5, 'Powertrain', 'Montagem de motores e conjuntos de tracao.'),
                (6, 'Qualidade', 'Inspecoes e testes de conformidade.'),
                (7, 'Logistica Interna', 'Abastecimento e movimentacao de materiais.'),
                (8, 'Manutencao', 'Manutencao dos ativos industriais.')
        ) AS dados(ordinalidade, nome, descricao);

        INSERT INTO linhas (id, nome, area_id, meta_diaria)
        SELECT
            md5('automotiva-real-linha-' || linha_n)::uuid,
            'Linha Automotiva L' || lpad(linha_n::text, 3, '0'),
            md5('automotiva-real-area-' || (((linha_n - 1) % 8) + 1))::uuid,
            180 + ((linha_n * 11) % 121)
        FROM generate_series(1, 100) AS linhas(linha_n);

        INSERT INTO equipes (id, nome, descricao, linha_id)
        SELECT
            md5('automotiva-real-equipe-' || equipe_n)::uuid,
            'Equipe L' || lpad(linha_n::text, 3, '0') || ' - Turno ' || turno_n,
            'Equipe fixa de 10 colaboradores vinculada a uma linha e turno.',
            md5('automotiva-real-linha-' || linha_n)::uuid
        FROM generate_series(1, 100) AS linhas(linha_n)
        CROSS JOIN generate_series(1, 3) AS turnos(turno_n)
        CROSS JOIN LATERAL (
            SELECT ((linha_n - 1) * 3) + turno_n AS equipe_n
        ) AS equipes;

        INSERT INTO postos (id, codigo, nome, linha_id, criticidade)
        SELECT
            md5('automotiva-real-posto-' || linha_n || '-' || posto_n)::uuid,
            'AUT-L' || lpad(linha_n::text, 3, '0') || '-P' || lpad(posto_n::text, 2, '0'),
            'Posto ' || lpad(posto_n::text, 2, '0') || ' da Linha '
                || lpad(linha_n::text, 3, '0'),
            md5('automotiva-real-linha-' || linha_n)::uuid,
            1 + ((linha_n * 3 + posto_n * 7) % 5)
        FROM generate_series(1, 100) AS linhas(linha_n)
        CROSS JOIN generate_series(1, 10) AS postos(posto_n);

        INSERT INTO postos_habilidades (id, posto_id, habilidade_id, nivel_minimo)
        SELECT
            md5(
                'automotiva-real-posto-habilidade-' || linha_n || '-' || posto_n || '-' || req_n
            )::uuid,
            md5('automotiva-real-posto-' || linha_n || '-' || posto_n)::uuid,
            md5(
                'nissa-mock-habilidade-'
                || CASE
                    WHEN req_n = 1 THEN (((area_n * 2 + posto_n - 2) % 20) + 1)
                    ELSE (((area_n * 2 + posto_n + 4) % 20) + 1)
                END
            )::uuid,
            CASE WHEN req_n = 1 THEN 3 + (posto_n % 2) ELSE 3 END
        FROM generate_series(1, 100) AS linhas(linha_n)
        CROSS JOIN generate_series(1, 10) AS postos(posto_n)
        CROSS JOIN generate_series(1, 2) AS requisitos(req_n)
        CROSS JOIN LATERAL (
            SELECT (((linha_n - 1) % 8) + 1) AS area_n
        ) AS areas;

        INSERT INTO funcionarios (
            id, matricula, nome, cpf, sexo, data_nascimento, data_admissao,
            area_id, equipe_id, turno, status, distancia_trabalho_km,
            tempo_deslocamento_min, possui_veiculo, tipo_transporte,
            criticidade_funcionario, presenca_diaria
        )
        SELECT
            md5('automotiva-real-funcionario-' || n)::uuid,
            'AUT-' || lpad(n::text, 5, '0'),
            'Operador L' || lpad(linha_n::text, 3, '0')
                || '-T' || turno_n || '-P' || lpad(posto_n::text, 2, '0'),
            lpad((95000000000::bigint + n)::text, 11, '0'),
            CASE WHEN n % 2 = 0 THEN 'F' ELSE 'M' END,
            DATE '1972-01-01' + ((n * 31) % 10950),
            DATE '2008-01-01' + ((n * 17) % 6500),
            md5('automotiva-real-area-' || area_n)::uuid,
            md5('automotiva-real-equipe-' || equipe_n)::uuid,
            'TURNO_' || turno_n,
            CASE
                WHEN n % 125 = 0 THEN 'AFASTADO'
                WHEN n % 100 = 0 THEN 'FERIAS'
                ELSE 'ATIVO'
            END::status_funcionario,
            ((2 + ((n * 19) % 6800))::numeric / 100),
            8 + ((n * 13) % 103),
            n % 3 <> 0,
            (ARRAY['CARRO', 'MOTO', 'ONIBUS', 'FRETADO', 'UBER', 'BICICLETA'])[
                ((n - 1) % 6) + 1
            ]::tipo_transporte,
            1 + ((linha_n + posto_n * 3) % 5),
            n % 40 <> 0
        FROM generate_series(1, 3000) AS funcionarios(n)
        CROSS JOIN LATERAL (
            SELECT
                (((n - 1) / 10) + 1) AS equipe_n,
                (((n - 1) % 10) + 1) AS posto_n
        ) AS base
        CROSS JOIN LATERAL (
            SELECT
                (((equipe_n - 1) / 3) + 1) AS linha_n,
                (((equipe_n - 1) % 3) + 1) AS turno_n
        ) AS operacao
        CROSS JOIN LATERAL (
            SELECT (((linha_n - 1) % 8) + 1) AS area_n
        ) AS areas;

        INSERT INTO funcionarios_habilidades (
            id, funcionario_id, habilidade_id, nivel, ultima_avaliacao, validade
        )
        SELECT
            md5(
                'automotiva-real-func-habilidade-' || n || '-' || habilidade.habilidade_id
            )::uuid,
            md5('automotiva-real-funcionario-' || n)::uuid,
            habilidade.habilidade_id,
            LEAST(
                5,
                MAX(requisito.nivel_minimo + CASE WHEN cobertura = 1 THEN 1 ELSE 0 END)
            ),
            DATE '2025-01-01' + ((n * 7 + habilidade.habilidade_ord * 13) % 550),
            CASE WHEN n % 20 = 0 THEN DATE '2026-07-31' ELSE DATE '2028-12-31' END
        FROM generate_series(1, 3000) AS funcionarios(n)
        CROSS JOIN LATERAL (
            SELECT
                (((n - 1) / 10) + 1) AS equipe_n,
                (((n - 1) % 10) + 1) AS posto_n
        ) AS base
        CROSS JOIN LATERAL (
            SELECT (((equipe_n - 1) / 3) + 1) AS linha_n
        ) AS operacao
        CROSS JOIN LATERAL (
            VALUES (1, posto_n), (2, (posto_n % 10) + 1)
        ) AS coberturas(cobertura, posto_coberto)
        JOIN postos_habilidades AS requisito
          ON requisito.posto_id = md5(
              'automotiva-real-posto-' || linha_n || '-' || posto_coberto
          )::uuid
        CROSS JOIN LATERAL (
            SELECT
                requisito.habilidade_id AS habilidade_id,
                (abs(hashtext(requisito.habilidade_id::text)) % 1000) AS habilidade_ord
        ) AS habilidade
        GROUP BY n, habilidade.habilidade_id, habilidade.habilidade_ord;

        INSERT INTO alocacoes (
            id, funcionario_id, posto_id, data_inicio, data_fim, ativo
        )
        SELECT
            md5('automotiva-real-alocacao-' || n)::uuid,
            md5('automotiva-real-funcionario-' || n)::uuid,
            md5('automotiva-real-posto-' || linha_n || '-' || posto_n)::uuid,
            DATE '2026-01-01' + ((n * 3) % 180),
            NULL,
            true
        FROM generate_series(1, 3000) AS funcionarios(n)
        CROSS JOIN LATERAL (
            SELECT
                (((n - 1) / 10) + 1) AS equipe_n,
                (((n - 1) % 10) + 1) AS posto_n
        ) AS base
        CROSS JOIN LATERAL (
            SELECT (((equipe_n - 1) / 3) + 1) AS linha_n
        ) AS operacao;

        INSERT INTO historicos_ausencia (
            id, funcionario_id, data_ausencia, tipo, motivo, justificada
        )
        SELECT
            md5('automotiva-real-ausencia-' || n)::uuid,
            md5('automotiva-real-funcionario-' || n)::uuid,
            CURRENT_DATE,
            (ARRAY['FALTA', 'ATESTADO', 'LICENCA'])[((n / 40) % 3) + 1]::tipo_ausencia,
            'Ausencia ficticia distribuida entre linhas e turnos.',
            n % 80 <> 0
        FROM generate_series(40, 3000, 40) AS funcionarios(n);
    """
    _execute_script(script)


def downgrade() -> None:
    script = """
        DELETE FROM alocacoes
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'AUT-%'
        );
        DELETE FROM historicos_ausencia
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'AUT-%'
        );
        DELETE FROM funcionarios_habilidades
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'AUT-%'
        );
        DELETE FROM postos_habilidades
        WHERE posto_id IN (SELECT id FROM postos WHERE codigo LIKE 'AUT-%');
        DELETE FROM funcionarios WHERE matricula LIKE 'AUT-%';
        DELETE FROM postos WHERE codigo LIKE 'AUT-%';
        DELETE FROM equipes WHERE nome LIKE 'Equipe L% - Turno %';
        DELETE FROM linhas WHERE nome LIKE 'Linha Automotiva L%';
        DELETE FROM areas
        WHERE id IN (
            SELECT md5('automotiva-real-area-' || n)::uuid
            FROM generate_series(1, 8) AS areas(n)
        );
    """
    _execute_script(script)


def _execute_script(script: str) -> None:
    for statement in script.split(";"):
        if statement := statement.strip():
            op.execute(sa.text(statement))
