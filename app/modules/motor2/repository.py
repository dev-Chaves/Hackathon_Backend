from collections import Counter
from datetime import date
from uuid import UUID

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.entities import (
    Alocacao,
    Funcionario,
    FuncionarioHabilidade,
    HistoricoAusencia,
    Linha,
    Posto,
    PostoHabilidade,
)
from app.models.enums import StatusFuncionario
from app.modules.motor2.domain import (
    CandidateContext,
    MatchmakingSnapshot,
    SkillQualification,
    SkillRequirement,
    TargetContext,
)
from app.modules.motor2.exceptions import (
    ActiveAllocationNotFoundError,
    EmployeeNotFoundError,
)


class MatchmakingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_snapshot(
        self, funcionario_ausente_id: UUID, reference_date: date
    ) -> MatchmakingSnapshot:
        absent = await self._load_absent_employee(funcionario_ausente_id)
        allocation = next((item for item in absent.alocacoes if item.ativo), None)
        if allocation is None:
            raise ActiveAllocationNotFoundError(funcionario_ausente_id)

        employees = await self._load_active_employees({funcionario_ausente_id}, absent.turno)
        absent_ids = await self._load_absent_ids(reference_date)
        team_totals = await self._load_team_totals(absent.turno)
        available_by_team = Counter(
            employee.equipe_id
            for employee in employees
            if employee.id not in absent_ids
        )
        qualifications = {
            employee.id: self._qualification_map(employee.habilidades) for employee in employees
        }

        posto = allocation.posto
        linha = posto.linha
        target_requirements = self._requirements(posto)
        target = TargetContext(
            funcionario_ausente_id=absent.id,
            funcionario_ausente_nome=absent.nome,
            posto_id=posto.id,
            posto_codigo=posto.codigo,
            posto_nome=posto.nome,
            linha_id=linha.id,
            linha_nome=linha.nome,
            area_id=linha.area.id,
            area_nome=linha.area.nome,
            criticidade_destino=posto.criticidade,
            requisitos=tuple(target_requirements),
            equipe_id=absent.equipe.id,
            equipe_nome=absent.equipe.nome,
            tech_lead_nome=absent.equipe.tech_lead_nome,
            tech_lead_email=absent.equipe.tech_lead_email,
        )
        origin_backup_cache: dict[UUID, int] = {}

        contexts = tuple(
            self._build_candidate_context(
                employee=employee,
                all_employees=employees,
                qualifications=qualifications,
                absent_ids=absent_ids,
                team_totals=team_totals,
                available_by_team=available_by_team,
                reference_date=reference_date,
                target_requirements=target_requirements,
                origin_backup_cache=origin_backup_cache,
            )
            for employee in employees
        )
        return MatchmakingSnapshot(alvo=target, candidatos=contexts)

    async def build_batch_snapshots(
        self,
        reference_date: date,
        reserved_candidate_ids: set[UUID] | None = None,
    ) -> tuple[MatchmakingSnapshot, ...]:
        reserved_candidate_ids = reserved_candidate_ids or set()
        operational_absent_ids = await self._load_operational_absent_ids(reference_date)
        if not operational_absent_ids:
            return ()

        absent_employees = await self._load_absent_employees(operational_absent_ids)
        snapshots: list[MatchmakingSnapshot] = []
        for turno in sorted({employee.turno for employee in absent_employees}):
            turn_absents = [employee for employee in absent_employees if employee.turno == turno]
            excluded_ids = operational_absent_ids | reserved_candidate_ids
            employees = await self._load_active_employees(excluded_ids, turno)
            team_totals = await self._load_team_totals(turno)
            available_by_team = Counter(employee.equipe_id for employee in employees)
            qualifications = {
                employee.id: self._qualification_map(employee.habilidades)
                for employee in employees
            }
            origin_backup_cache: dict[UUID, int] = {}

            for absent in turn_absents:
                allocation = next((item for item in absent.alocacoes if item.ativo), None)
                if allocation is None:
                    continue
                posto = allocation.posto
                linha = posto.linha
                target_requirements = self._requirements(posto)
                target = TargetContext(
                    funcionario_ausente_id=absent.id,
                    funcionario_ausente_nome=absent.nome,
                    posto_id=posto.id,
                    posto_codigo=posto.codigo,
                    posto_nome=posto.nome,
                    linha_id=linha.id,
                    linha_nome=linha.nome,
                    area_id=linha.area.id,
                    area_nome=linha.area.nome,
                    criticidade_destino=posto.criticidade,
                    requisitos=tuple(target_requirements),
                    equipe_id=absent.equipe.id,
                    equipe_nome=absent.equipe.nome,
                    tech_lead_nome=absent.equipe.tech_lead_nome,
                    tech_lead_email=absent.equipe.tech_lead_email,
                )
                contexts = tuple(
                    self._build_candidate_context(
                        employee=employee,
                        all_employees=employees,
                        qualifications=qualifications,
                        absent_ids=operational_absent_ids,
                        team_totals=team_totals,
                        available_by_team=available_by_team,
                        reference_date=reference_date,
                        target_requirements=target_requirements,
                        origin_backup_cache=origin_backup_cache,
                    )
                    for employee in employees
                )
                snapshots.append(MatchmakingSnapshot(alvo=target, candidatos=contexts))
        return tuple(snapshots)

    async def _load_absent_employee(self, funcionario_id: UUID) -> Funcionario:
        statement = (
            select(Funcionario)
            .where(Funcionario.id == funcionario_id)
            .options(
                joinedload(Funcionario.equipe),
                joinedload(Funcionario.alocacoes)
                .joinedload(Alocacao.posto)
                .joinedload(Posto.habilidades)
                .joinedload(PostoHabilidade.habilidade),
                joinedload(Funcionario.alocacoes)
                .joinedload(Alocacao.posto)
                .joinedload(Posto.linha)
                .joinedload(Linha.area),
            )
        )
        employee = (await self.session.execute(statement)).unique().scalar_one_or_none()
        if employee is None:
            raise EmployeeNotFoundError(funcionario_id)
        return employee

    async def _load_absent_employees(self, funcionario_ids: set[UUID]) -> list[Funcionario]:
        statement = (
            select(Funcionario)
            .where(Funcionario.id.in_(funcionario_ids))
            .options(
                joinedload(Funcionario.equipe),
                joinedload(Funcionario.alocacoes)
                .joinedload(Alocacao.posto)
                .joinedload(Posto.habilidades)
                .joinedload(PostoHabilidade.habilidade),
                joinedload(Funcionario.alocacoes)
                .joinedload(Alocacao.posto)
                .joinedload(Posto.linha)
                .joinedload(Linha.area),
            )
        )
        return list((await self.session.execute(statement)).scalars().unique().all())

    async def _load_active_employees(
        self, excluded_ids: set[UUID], turno: str
    ) -> list[Funcionario]:
        statement = (
            select(Funcionario)
            .where(
                Funcionario.id.not_in(excluded_ids),
                Funcionario.status == StatusFuncionario.ATIVO,
                Funcionario.turno == turno,
            )
            .options(
                selectinload(Funcionario.habilidades),
                joinedload(Funcionario.alocacoes)
                .joinedload(Alocacao.posto)
                .joinedload(Posto.habilidades),
            )
        )
        return list((await self.session.execute(statement)).scalars().unique().all())

    async def _load_absent_ids(self, reference_date: date) -> set[UUID]:
        statement = select(HistoricoAusencia.funcionario_id).where(
            HistoricoAusencia.data_ausencia == reference_date
        )
        return set((await self.session.execute(statement)).scalars().all())

    async def _load_operational_absent_ids(self, reference_date: date) -> set[UUID]:
        absence_on_date = exists().where(
            HistoricoAusencia.funcionario_id == Funcionario.id,
            HistoricoAusencia.data_ausencia == reference_date,
        )
        statement = (
            select(Funcionario.id)
            .join(Alocacao, Alocacao.funcionario_id == Funcionario.id)
            .where(
                Alocacao.ativo.is_(True),
                or_(
                    Funcionario.presenca_diaria.is_(False),
                    Funcionario.status != StatusFuncionario.ATIVO,
                    absence_on_date,
                ),
            )
            .distinct()
        )
        return set((await self.session.execute(statement)).scalars().all())

    async def _load_team_totals(self, turno: str) -> dict[UUID, int]:
        statement = (
            select(Funcionario.equipe_id, func.count(Funcionario.id))
            .where(
                Funcionario.status != StatusFuncionario.DESLIGADO,
                Funcionario.turno == turno,
            )
            .group_by(Funcionario.equipe_id)
        )
        return dict((await self.session.execute(statement)).all())

    def _build_candidate_context(
        self,
        employee: Funcionario,
        all_employees: list[Funcionario],
        qualifications: dict[UUID, dict[UUID, SkillQualification]],
        absent_ids: set[UUID],
        team_totals: dict[UUID, int],
        available_by_team: Counter[UUID],
        reference_date: date,
        target_requirements: list[SkillRequirement],
        origin_backup_cache: dict[UUID, int],
    ) -> CandidateContext:
        origin_allocation = next((item for item in employee.alocacoes if item.ativo), None)
        origin_post = origin_allocation.posto if origin_allocation else None
        origin_requirements = (
            self._requirements(origin_post, include_names=False) if origin_post else []
        )
        backups = 0
        if (
            origin_post
            and employee.id not in absent_ids
            and self._meets_requirements(
                qualifications[employee.id], target_requirements, reference_date
            )
        ):
            if origin_post.id not in origin_backup_cache:
                origin_backup_cache[origin_post.id] = self._count_qualified_employees(
                    origin_requirements,
                    all_employees,
                    qualifications,
                    absent_ids,
                    reference_date,
                )
            employee_covers_origin = self._meets_requirements(
                qualifications[employee.id], origin_requirements, reference_date
            )
            backups = max(origin_backup_cache[origin_post.id] - int(employee_covers_origin), 0)
        planned = team_totals.get(employee.equipe_id, 0)
        available = available_by_team.get(employee.equipe_id, 0)
        current_coverage = available / planned * 100 if planned else 100.0
        post_coverage = max(available - 1, 0) / planned * 100 if planned else 100.0
        return CandidateContext(
            funcionario_id=employee.id,
            nome=employee.nome,
            status=employee.status.value,
            criticidade_funcionario=employee.criticidade_funcionario,
            habilidades=qualifications[employee.id],
            possui_ausencia_na_data=employee.id in absent_ids,
            criticidade_origem=origin_post.criticidade if origin_post else 0,
            quantidade_substitutos_origem=backups,
            cobertura_atual_origem=round(current_coverage, 2),
            cobertura_pos_movimentacao=round(post_coverage, 2),
            posto_origem_id=origin_post.id if origin_post else None,
            posto_origem_codigo=origin_post.codigo if origin_post else None,
        )

    @staticmethod
    def _qualification_map(
        skills: list[FuncionarioHabilidade],
    ) -> dict[UUID, SkillQualification]:
        return {
            skill.habilidade_id: SkillQualification(
                habilidade_id=skill.habilidade_id,
                nivel=skill.nivel,
                validade=skill.validade,
            )
            for skill in skills
        }

    @staticmethod
    def _requirements(
        posto: Posto | None, *, include_names: bool = True
    ) -> list[SkillRequirement]:
        if posto is None:
            return []
        return [
            SkillRequirement(
                habilidade_id=requirement.habilidade_id,
                nome=requirement.habilidade.nome
                if include_names
                else str(requirement.habilidade_id),
                nivel_minimo=requirement.nivel_minimo,
            )
            for requirement in posto.habilidades
        ]

    @staticmethod
    def _count_qualified_employees(
        requirements: list[SkillRequirement],
        all_employees: list[Funcionario],
        qualifications: dict[UUID, dict[UUID, SkillQualification]],
        absent_ids: set[UUID],
        reference_date: date,
    ) -> int:
        count = 0
        for other in all_employees:
            if other.id in absent_ids:
                continue
            skill_map = qualifications[other.id]
            if all(
                (qualification := skill_map.get(requirement.habilidade_id)) is not None
                and qualification.nivel >= requirement.nivel_minimo
                and (qualification.validade is None or qualification.validade >= reference_date)
                for requirement in requirements
            ):
                count += 1
        return count

    @staticmethod
    def _meets_requirements(
        qualifications: dict[UUID, SkillQualification],
        requirements: list[SkillRequirement],
        reference_date: date,
    ) -> bool:
        return all(
            (qualification := qualifications.get(requirement.habilidade_id)) is not None
            and qualification.nivel >= requirement.nivel_minimo
            and (qualification.validade is None or qualification.validade >= reference_date)
            for requirement in requirements
        )
