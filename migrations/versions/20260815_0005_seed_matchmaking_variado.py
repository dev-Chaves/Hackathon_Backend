"""Cria cenario variado e isolado para demonstracao do Motor 2.

Revision ID: 20260815_0005
Revises: 20260815_0004
Create Date: 2026-08-15

O turno TURNO_MMS_DEMO isola este conjunto dos seeds anteriores. O alvo possui candidatos
excelentes, bons e aceitaveis, alem de bloqueios por regras distintas do matchmaking.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0005"
down_revision: str | None = "20260815_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    script = """
        INSERT INTO areas (id, nome, descricao)
        VALUES (
            md5('nissa-mms-div-area')::uuid,
            'Nissa - Laboratorio MMS Variado',
            'Cenario isolado para demonstrar scores e bloqueios variados do Motor 2.'
        );

        INSERT INTO equipes (id, nome, descricao)
        VALUES
            (
                md5('nissa-mms-div-equipe-alvo')::uuid,
                'Nissa MMS - Equipe Alvo',
                'Equipe do colaborador ausente.'
            ),
            (
                md5('nissa-mms-div-equipe-robusta')::uuid,
                'Nissa MMS - Equipe Robusta',
                'Dez pessoas para cobertura pos-movimentacao de 80 a 90 por cento.'
            ),
            (
                md5('nissa-mms-div-equipe-enxuta')::uuid,
                'Nissa MMS - Equipe Enxuta',
                'Cinco pessoas para cobertura pos-movimentacao de 80 por cento.'
            ),
            (
                md5('nissa-mms-div-equipe-fragil')::uuid,
                'Nissa MMS - Equipe Fragil',
                'Quatro pessoas para simular cobertura abaixo do limite.'
            );

        INSERT INTO linhas (id, nome, area_id, meta_diaria)
        VALUES (
            md5('nissa-mms-div-linha')::uuid,
            'Nissa - Linha MMS Demonstracao Variada',
            md5('nissa-mms-div-area')::uuid,
            240
        );

        INSERT INTO postos (id, codigo, nome, linha_id, criticidade)
        VALUES
            (
                md5('nissa-mms-div-posto-destino')::uuid,
                'NIS-MMS-DEST',
                'Solda Robotizada Critica',
                md5('nissa-mms-div-linha')::uuid,
                4
            ),
            (
                md5('nissa-mms-div-posto-seguro')::uuid,
                'NIS-MMS-ORIG-SEG',
                'Origem com Muitos Backups',
                md5('nissa-mms-div-linha')::uuid,
                1
            ),
            (
                md5('nissa-mms-div-posto-impacto')::uuid,
                'NIS-MMS-ORIG-IMP',
                'Origem com Impacto Alto',
                md5('nissa-mms-div-linha')::uuid,
                4
            ),
            (
                md5('nissa-mms-div-posto-aceitavel')::uuid,
                'NIS-MMS-ORIG-ACE',
                'Origem sem Backup na Equipe Enxuta',
                md5('nissa-mms-div-linha')::uuid,
                4
            ),
            (
                md5('nissa-mms-div-posto-sem-backup')::uuid,
                'NIS-MMS-ORIG-NBK',
                'Origem Critica sem Backup',
                md5('nissa-mms-div-linha')::uuid,
                3
            ),
            (
                md5('nissa-mms-div-posto-mais-critico')::uuid,
                'NIS-MMS-ORIG-MCR',
                'Origem Mais Critica que o Destino',
                md5('nissa-mms-div-linha')::uuid,
                5
            ),
            (
                md5('nissa-mms-div-posto-cobertura')::uuid,
                'NIS-MMS-ORIG-COB',
                'Origem em Equipe com Baixa Cobertura',
                md5('nissa-mms-div-linha')::uuid,
                2
            );

        INSERT INTO postos_habilidades (id, posto_id, habilidade_id, nivel_minimo)
        VALUES
            (
                md5('nissa-mms-div-req-dest-solda')::uuid,
                md5('nissa-mms-div-posto-destino')::uuid,
                md5('nissa-mock-habilidade-2')::uuid,
                4
            ),
            (
                md5('nissa-mms-div-req-dest-loto')::uuid,
                md5('nissa-mms-div-posto-destino')::uuid,
                md5('nissa-mock-habilidade-19')::uuid,
                3
            ),
            (
                md5('nissa-mms-div-req-seguro')::uuid,
                md5('nissa-mms-div-posto-seguro')::uuid,
                md5('nissa-mock-habilidade-20')::uuid,
                3
            ),
            (
                md5('nissa-mms-div-req-impacto')::uuid,
                md5('nissa-mms-div-posto-impacto')::uuid,
                md5('nissa-mock-habilidade-18')::uuid,
                5
            ),
            (
                md5('nissa-mms-div-req-aceitavel')::uuid,
                md5('nissa-mms-div-posto-aceitavel')::uuid,
                md5('nissa-mock-habilidade-16')::uuid,
                5
            ),
            (
                md5('nissa-mms-div-req-sem-backup')::uuid,
                md5('nissa-mms-div-posto-sem-backup')::uuid,
                md5('nissa-mock-habilidade-17')::uuid,
                5
            ),
            (
                md5('nissa-mms-div-req-mais-critico')::uuid,
                md5('nissa-mms-div-posto-mais-critico')::uuid,
                md5('nissa-mock-habilidade-15')::uuid,
                5
            ),
            (
                md5('nissa-mms-div-req-cobertura')::uuid,
                md5('nissa-mms-div-posto-cobertura')::uuid,
                md5('nissa-mock-habilidade-14')::uuid,
                5
            );

        INSERT INTO funcionarios (
            id, matricula, nome, cpf, sexo, data_nascimento, data_admissao,
            area_id, equipe_id, turno, status, distancia_trabalho_km,
            tempo_deslocamento_min, possui_veiculo, tipo_transporte,
            criticidade_funcionario, presenca_diaria
        )
        SELECT
            md5('nissa-mms-div-func-' || n)::uuid,
            'NISSA-MMS-DIV-' || lpad(n::text, 3, '0'),
            (ARRAY[
                'Alex Martins - Ausente Alvo',
                'Mariana Costa - Excelente Livre',
                'Rafael Souza - Excelente Baixo Impacto',
                'Bianca Lima - Bom Impacto Alto',
                'Clara Mendes - Capacitacao Vencida',
                'Fabio Rocha - Nivel Insuficiente',
                'Gabriela Alves - Habilidade Ausente',
                'Henrique Dias - Ausente Hoje',
                'Isabela Nunes - Critico Sem Backup',
                'Joao Freitas - Origem Mais Critica',
                'Kelly Ramos - Apoio Seguro 01',
                'Leandro Silva - Apoio Seguro 02',
                'Diego Santos - Match Aceitavel',
                'Monica Reis - Apoio Enxuto 01',
                'Nelson Luz - Apoio Enxuto 02',
                'Olivia Moraes - Apoio Enxuto 03',
                'Paulo Melo - Apoio Enxuto 04',
                'Renata Araujo - Cobertura Insuficiente',
                'Sergio Lopes - Apoio Fragil 01',
                'Talita Gomes - Apoio Fragil 02',
                'Vitor Barros - Apoio Fragil 03'
            ])[n],
            lpad((94000000000::bigint + n)::text, 11, '0'),
            CASE WHEN n % 2 = 0 THEN 'F' ELSE 'M' END,
            DATE '1980-01-01' + (n * 173),
            DATE '2015-01-01' + (n * 101),
            md5('nissa-mms-div-area')::uuid,
            CASE
                WHEN n = 1 THEN md5('nissa-mms-div-equipe-alvo')::uuid
                WHEN n BETWEEN 2 AND 12 THEN md5('nissa-mms-div-equipe-robusta')::uuid
                WHEN n BETWEEN 13 AND 17 THEN md5('nissa-mms-div-equipe-enxuta')::uuid
                ELSE md5('nissa-mms-div-equipe-fragil')::uuid
            END,
            'TURNO_MMS_DEMO',
            'ATIVO'::status_funcionario,
            3 + (n * 1.7),
            12 + (n * 3),
            n % 3 <> 0,
            (ARRAY['CARRO', 'MOTO', 'ONIBUS', 'FRETADO'])[((n - 1) % 4) + 1]::tipo_transporte,
            CASE WHEN n = 9 THEN 4 ELSE 2 END,
            CASE WHEN n IN (1, 8) THEN false ELSE true END
        FROM generate_series(1, 21) AS serie(n);

        INSERT INTO funcionarios_habilidades (
            id, funcionario_id, habilidade_id, nivel, ultima_avaliacao, validade
        )
        SELECT
            md5('nissa-mms-div-skill-solda-' || n)::uuid,
            md5('nissa-mms-div-func-' || n)::uuid,
            md5('nissa-mock-habilidade-2')::uuid,
            CASE
                WHEN n IN (1, 2, 3) THEN 5
                WHEN n IN (4, 5, 8, 9, 10, 13, 18) THEN 4
                WHEN n = 6 THEN 3
                ELSE 1
            END,
            DATE '2026-01-15',
            CASE WHEN n = 5 THEN DATE '2025-12-31' ELSE DATE '2030-12-31' END
        FROM generate_series(1, 21) AS serie(n)
        WHERE n IN (1, 2, 3, 4, 5, 6, 8, 9, 10, 13, 18);

        INSERT INTO funcionarios_habilidades (
            id, funcionario_id, habilidade_id, nivel, ultima_avaliacao, validade
        )
        SELECT
            md5('nissa-mms-div-skill-loto-' || n)::uuid,
            md5('nissa-mms-div-func-' || n)::uuid,
            md5('nissa-mock-habilidade-19')::uuid,
            CASE WHEN n IN (1, 2, 3) THEN 5 WHEN n = 4 THEN 4 ELSE 3 END,
            DATE '2026-01-15',
            DATE '2030-12-31'
        FROM generate_series(1, 21) AS serie(n)
        WHERE n IN (1, 2, 3, 4, 5, 6, 8, 9, 10, 13, 18);

        INSERT INTO funcionarios_habilidades (
            id, funcionario_id, habilidade_id, nivel, ultima_avaliacao, validade
        )
        VALUES
            (
                md5('nissa-mms-div-skill-seguro-3')::uuid,
                md5('nissa-mms-div-func-3')::uuid,
                md5('nissa-mock-habilidade-20')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            ),
            (
                md5('nissa-mms-div-skill-impacto-4')::uuid,
                md5('nissa-mms-div-func-4')::uuid,
                md5('nissa-mock-habilidade-18')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            ),
            (
                md5('nissa-mms-div-skill-sem-backup-9')::uuid,
                md5('nissa-mms-div-func-9')::uuid,
                md5('nissa-mock-habilidade-17')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            ),
            (
                md5('nissa-mms-div-skill-mais-critico-10')::uuid,
                md5('nissa-mms-div-func-10')::uuid,
                md5('nissa-mock-habilidade-15')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            ),
            (
                md5('nissa-mms-div-skill-aceitavel-13')::uuid,
                md5('nissa-mms-div-func-13')::uuid,
                md5('nissa-mock-habilidade-16')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            ),
            (
                md5('nissa-mms-div-skill-cobertura-18')::uuid,
                md5('nissa-mms-div-func-18')::uuid,
                md5('nissa-mock-habilidade-14')::uuid,
                5, DATE '2026-01-15', DATE '2030-12-31'
            );

        INSERT INTO funcionarios_habilidades (
            id, funcionario_id, habilidade_id, nivel, ultima_avaliacao, validade
        )
        SELECT
            md5('nissa-mms-div-skill-backup-' || n)::uuid,
            md5('nissa-mms-div-func-' || n)::uuid,
            md5('nissa-mock-habilidade-20')::uuid,
            4,
            DATE '2026-01-15',
            DATE '2030-12-31'
        FROM generate_series(11, 12) AS serie(n);

        INSERT INTO alocacoes (id, funcionario_id, posto_id, data_inicio, data_fim, ativo)
        VALUES
            (
                md5('nissa-mms-div-aloc-1')::uuid,
                md5('nissa-mms-div-func-1')::uuid,
                md5('nissa-mms-div-posto-destino')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-3')::uuid,
                md5('nissa-mms-div-func-3')::uuid,
                md5('nissa-mms-div-posto-seguro')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-4')::uuid,
                md5('nissa-mms-div-func-4')::uuid,
                md5('nissa-mms-div-posto-impacto')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-9')::uuid,
                md5('nissa-mms-div-func-9')::uuid,
                md5('nissa-mms-div-posto-sem-backup')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-10')::uuid,
                md5('nissa-mms-div-func-10')::uuid,
                md5('nissa-mms-div-posto-mais-critico')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-13')::uuid,
                md5('nissa-mms-div-func-13')::uuid,
                md5('nissa-mms-div-posto-aceitavel')::uuid,
                DATE '2026-01-01', NULL, true
            ),
            (
                md5('nissa-mms-div-aloc-18')::uuid,
                md5('nissa-mms-div-func-18')::uuid,
                md5('nissa-mms-div-posto-cobertura')::uuid,
                DATE '2026-01-01', NULL, true
            );

        INSERT INTO historicos_ausencia (
            id, funcionario_id, data_ausencia, tipo, motivo, justificada
        )
        VALUES
            (
                md5('nissa-mms-div-ausencia-alvo')::uuid,
                md5('nissa-mms-div-func-1')::uuid,
                CURRENT_DATE,
                'FALTA'::tipo_ausencia,
                'Ausencia ficticia usada como gatilho do cenario variado.',
                false
            ),
            (
                md5('nissa-mms-div-ausencia-candidato')::uuid,
                md5('nissa-mms-div-func-8')::uuid,
                CURRENT_DATE,
                'ATESTADO'::tipo_ausencia,
                'Candidato tecnicamente apto, mas indisponivel na data.',
                true
            );
    """
    _execute_script(script)


def downgrade() -> None:
    script = """
        DELETE FROM alocacoes
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-MMS-DIV-%'
        );

        DELETE FROM historicos_ausencia
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-MMS-DIV-%'
        );

        DELETE FROM funcionarios_habilidades
        WHERE funcionario_id IN (
            SELECT id FROM funcionarios WHERE matricula LIKE 'NISSA-MMS-DIV-%'
        );

        DELETE FROM postos_habilidades
        WHERE posto_id IN (SELECT id FROM postos WHERE codigo LIKE 'NIS-MMS-%');

        DELETE FROM funcionarios WHERE matricula LIKE 'NISSA-MMS-DIV-%';
        DELETE FROM postos WHERE codigo LIKE 'NIS-MMS-%';
        DELETE FROM linhas WHERE nome = 'Nissa - Linha MMS Demonstracao Variada';
        DELETE FROM equipes WHERE nome LIKE 'Nissa MMS - Equipe %';
        DELETE FROM areas WHERE nome = 'Nissa - Laboratorio MMS Variado';
    """
    _execute_script(script)


def _execute_script(script: str) -> None:
    for statement in script.split(";"):
        if statement := statement.strip():
            op.execute(sa.text(statement))
