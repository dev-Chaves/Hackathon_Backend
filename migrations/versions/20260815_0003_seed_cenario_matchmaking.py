"""Cenario estruturado de 2.000 colaboradores para o Motor 2.

Revision ID: 20260815_0003
Revises: 20260815_0002
Create Date: 2026-08-15

Gera 200 celulas operacionais de 10 pessoas (2.000 colaboradores) com perfis
complementares e substituiveis. Em cada celula, o titular (papel 01) faltou
hoje; os papeis 02 e 03 sao substitutos elegiveis; 04-07 sao complementares
(NAO cobrem o posto critico sozinhos); 08 e backup; 09-10 sao bloqueios.

Teste rapido (celula 001):
- Ausente: Carlos Ferreira / NISSA-CEN-00001 / posto NIS-CEN-0001-P001
- data_referencia: 2026-08-15
- Elegiveis na celula: Ana Souza (00002), Bruno Lima (00003), backup (00008)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0003"
down_revision: str | None = "20260815_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REFERENCE_ABSENCE_DATE = "2026-08-15"
TOTAL_EMPLOYEES = 2000
SQUAD_SIZE = 10
TOTAL_SQUADS = TOTAL_EMPLOYEES // SQUAD_SIZE


def upgrade() -> None:
    script = f"""
            INSERT INTO areas (id, nome, descricao)
            VALUES (
                md5('nissa-cenario-mms-area')::uuid,
                'Nissa - Cenario Matchmaking',
                'Area ficticia com 2.000 colaboradores em celulas complementares.'
            );

            INSERT INTO equipes (id, nome, descricao)
            SELECT
                md5('nissa-cenario-mms-equipe-' || n)::uuid,
                'Nissa - Equipe Cenario MMS ' || lpad(n::text, 3, '0'),
                'Celula de 10 colaboradores: titular, substitutos, complementares e bloqueios.'
            FROM generate_series(1, {TOTAL_SQUADS}) AS serie(n);

            INSERT INTO linhas (id, nome, area_id, meta_diaria)
            SELECT
                md5('nissa-cenario-mms-linha-' || n)::uuid,
                'Nissa - Linha Cenario MMS ' || lpad(n::text, 2, '0'),
                md5('nissa-cenario-mms-area')::uuid,
                220 + ((n * 13) % 80)
            FROM generate_series(1, 50) AS serie(n);

            INSERT INTO postos (id, codigo, nome, linha_id, criticidade)
            SELECT
                md5('nissa-cenario-mms-squad-' || squad || '-posto-' || tipo)::uuid,
                'NIS-CEN-' || lpad(squad::text, 4, '0') || '-' || tipo,
                CASE tipo
                    WHEN 'P001' THEN 'Posto Solda Critica'
                    WHEN 'P002' THEN 'Posto Suporte Solda'
                    WHEN 'P003' THEN 'Posto Estacao Solda'
                    ELSE 'Posto Estacao LOTO'
                END,
                md5('nissa-cenario-mms-linha-' || (((squad - 1) / 4) + 1))::uuid,
                CASE tipo
                    WHEN 'P001' THEN 4
                    WHEN 'P002' THEN 3
                    WHEN 'P003' THEN 3
                    ELSE 4
                END
            FROM generate_series(1, {TOTAL_SQUADS}) AS squads(squad)
            CROSS JOIN (
                VALUES ('P001'), ('P002'), ('P003'), ('P004')
            ) AS tipos(tipo);

            INSERT INTO postos_habilidades (id, posto_id, habilidade_id, nivel_minimo)
            SELECT
                md5(
                    'nissa-cenario-mms-posto-req-' || squad || '-' || tipo || '-' || hab_ord
                )::uuid,
                md5('nissa-cenario-mms-squad-' || squad || '-posto-' || tipo)::uuid,
                md5('nissa-mock-habilidade-' || hab_ord)::uuid,
                nivel_minimo
            FROM generate_series(1, {TOTAL_SQUADS}) AS squads(squad)
            CROSS JOIN (
                VALUES
                    ('P001', 1, 4),
                    ('P001', 19, 3),
                    ('P002', 1, 3),
                    ('P003', 1, 3),
                    ('P004', 19, 4)
            ) AS requisitos(tipo, hab_ord, nivel_minimo);

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
                md5('nissa-cenario-mms-func-' || n)::uuid,
                'NISSA-CEN-' || lpad(n::text, 5, '0'),
                CASE n
                    WHEN 1 THEN 'Carlos Ferreira'
                    WHEN 2 THEN 'Ana Souza'
                    WHEN 3 THEN 'Bruno Lima'
                    WHEN 4 THEN 'Helena Moura'
                    WHEN 5 THEN 'Igor Alves'
                    WHEN 6 THEN 'Eduardo Silva'
                    WHEN 7 THEN 'Fernanda Costa'
                    WHEN 8 THEN 'Laura Pinheiro'
                    WHEN 9 THEN 'Daniela Rocha'
                    WHEN 10 THEN 'Julia Martins'
                    ELSE
                        'Cenario MMS '
                        || lpad((((n - 1) / {SQUAD_SIZE}) + 1)::text, 3, '0')
                        || ' - Papel '
                        || lpad((((n - 1) % {SQUAD_SIZE}) + 1)::text, 2, '0')
                END,
                lpad((92000000000::bigint + n)::text, 11, '0'),
                CASE WHEN n % 2 = 0 THEN 'F' ELSE 'M' END,
                DATE '1975-01-01' + ((n * 17) % 12000),
                DATE '2008-01-01' + ((n * 23) % 6200),
                md5('nissa-cenario-mms-area')::uuid,
                md5(
                    'nissa-cenario-mms-equipe-' || (((n - 1) / {SQUAD_SIZE}) + 1)
                )::uuid,
                'TURNO_1',
                CASE
                    WHEN ((n - 1) % {SQUAD_SIZE}) + 1 = 10 THEN 'FERIAS'
                    ELSE 'ATIVO'
                END::status_funcionario,
                (((n * 11) % 4500)::numeric / 100),
                12 + ((n * 7) % 90),
                n % 4 <> 0,
                (ARRAY['CARRO', 'MOTO', 'ONIBUS', 'FRETADO', 'UBER', 'BICICLETA', 'A_PE'])[
                    ((n - 1) % 7) + 1
                ]::tipo_transporte,
                CASE ((n - 1) % {SQUAD_SIZE}) + 1
                    WHEN 1 THEN 4
                    WHEN 8 THEN 3
                    ELSE 2
                END
            FROM generate_series(1, {TOTAL_EMPLOYEES}) AS serie(n);

            INSERT INTO funcionarios_habilidades (
                id,
                funcionario_id,
                habilidade_id,
                nivel,
                ultima_avaliacao,
                validade
            )
            SELECT
                md5('nissa-cenario-mms-skill-solda-' || n)::uuid,
                md5('nissa-cenario-mms-func-' || n)::uuid,
                md5('nissa-mock-habilidade-1')::uuid,
                CASE ((n - 1) % {SQUAD_SIZE}) + 1
                    WHEN 1 THEN 5
                    WHEN 2 THEN 5
                    WHEN 3 THEN 4
                    WHEN 4 THEN 5
                    WHEN 5 THEN 5
                    WHEN 8 THEN 4
                    WHEN 9 THEN 5
                    WHEN 10 THEN 2
                    ELSE 0
                END,
                DATE '2025-06-01' + ((n * 3) % 180),
                CASE
                    WHEN ((n - 1) % {SQUAD_SIZE}) + 1 = 9 THEN DATE '2025-01-01'
                    ELSE DATE '2027-12-31'
                END
            FROM generate_series(1, {TOTAL_EMPLOYEES}) AS serie(n)
            WHERE ((n - 1) % {SQUAD_SIZE}) + 1 IN (1, 2, 3, 4, 5, 8, 9, 10);

            INSERT INTO funcionarios_habilidades (
                id,
                funcionario_id,
                habilidade_id,
                nivel,
                ultima_avaliacao,
                validade
            )
            SELECT
                md5('nissa-cenario-mms-skill-loto-' || n)::uuid,
                md5('nissa-cenario-mms-func-' || n)::uuid,
                md5('nissa-mock-habilidade-19')::uuid,
                CASE ((n - 1) % {SQUAD_SIZE}) + 1
                    WHEN 1 THEN 4
                    WHEN 2 THEN 5
                    WHEN 3 THEN 3
                    WHEN 6 THEN 5
                    WHEN 7 THEN 5
                    WHEN 8 THEN 4
                    WHEN 9 THEN 4
                    WHEN 10 THEN 2
                    ELSE 0
                END,
                DATE '2025-06-01' + ((n * 5) % 180),
                DATE '2027-12-31'
            FROM generate_series(1, {TOTAL_EMPLOYEES}) AS serie(n)
            WHERE ((n - 1) % {SQUAD_SIZE}) + 1 IN (1, 2, 3, 6, 7, 8, 9, 10);

            INSERT INTO alocacoes (
                id,
                funcionario_id,
                posto_id,
                data_inicio,
                data_fim,
                ativo
            )
            SELECT
                md5('nissa-cenario-mms-aloc-' || n)::uuid,
                md5('nissa-cenario-mms-func-' || n)::uuid,
                md5(
                    'nissa-cenario-mms-squad-'
                    || (((n - 1) / {SQUAD_SIZE}) + 1)
                    || '-posto-'
                    || CASE ((n - 1) % {SQUAD_SIZE}) + 1
                        WHEN 1 THEN 'P001'
                        WHEN 2 THEN 'P002'
                        WHEN 3 THEN 'P002'
                        WHEN 4 THEN 'P003'
                        WHEN 5 THEN 'P003'
                        WHEN 6 THEN 'P004'
                        WHEN 7 THEN 'P004'
                        WHEN 8 THEN 'P002'
                        WHEN 9 THEN 'P002'
                        ELSE 'P002'
                    END
                )::uuid,
                DATE '2026-01-01' + ((n * 2) % 120),
                NULL,
                true
            FROM generate_series(1, {TOTAL_EMPLOYEES}) AS serie(n);

            INSERT INTO historicos_ausencia (
                id,
                funcionario_id,
                data_ausencia,
                tipo,
                motivo,
                justificada
            )
            SELECT
                md5('nissa-cenario-mms-ausencia-' || n)::uuid,
                md5('nissa-cenario-mms-func-' || n)::uuid,
                DATE '{REFERENCE_ABSENCE_DATE}',
                (ARRAY['FALTA', 'ATESTADO', 'LICENCA'])[((n - 1) % 3) + 1]::tipo_ausencia,
                'Titular da celula ausente hoje para simular substituicao no posto critico.',
                ((n - 1) % 5) <> 0
            FROM generate_series(1, {TOTAL_EMPLOYEES}, {SQUAD_SIZE}) AS serie(n);
            """
    _execute_script(script)


def downgrade() -> None:
    script = """
            DELETE FROM alocacoes
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-CEN-%'
            );

            DELETE FROM historicos_ausencia
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-CEN-%'
            );

            DELETE FROM funcionarios_habilidades
            WHERE funcionario_id IN (
                SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-CEN-%'
            );

            DELETE FROM postos_habilidades
            WHERE posto_id IN (SELECT id FROM postos WHERE codigo LIKE 'NIS-CEN-%');

            DELETE FROM funcionarios WHERE matricula LIKE 'NISSA-CEN-%';
            DELETE FROM postos WHERE codigo LIKE 'NIS-CEN-%';
            DELETE FROM linhas WHERE nome LIKE 'Nissa - Linha Cenario MMS %';
            DELETE FROM equipes WHERE nome LIKE 'Nissa - Equipe Cenario MMS %';
            DELETE FROM areas WHERE nome = 'Nissa - Cenario Matchmaking';
            """
    _execute_script(script)


def _execute_script(script: str) -> None:
    for statement in script.split(";"):
        if statement := statement.strip():
            op.execute(sa.text(statement))
