"""Testes para o módulo schema — RequirementRecord, SuccessCriteria, VVMethod."""

import pytest
from pydantic import ValidationError

from simreqvalidator.schema import (
    Aggregation,
    BooleanCriteria,
    CountCriteria,
    Operator,
    RangeCriteria,
    RequirementLevel,
    RequirementRecord,
    Scope,
    StatisticalCriteria,
    TemporalCriteria,
    TemporalOperator,
    ThresholdCriteria,
    VerificationStatus,
    VVMethod,
)
from simreqvalidator.schema.success_criteria import TimeWindow


# =====================================================================
# VVMethod Tests
# =====================================================================


class TestVVMethod:
    """Testes para a enum VVMethod."""

    def test_fundamental_methods_exist(self):
        """Os 4 métodos IADT devem existir."""
        assert VVMethod.INSPECTION.value == "inspection"
        assert VVMethod.ANALYSIS.value == "analysis"
        assert VVMethod.DEMONSTRATION.value == "demonstration"
        assert VVMethod.TEST.value == "test"

    def test_additional_methods_exist(self):
        """Métodos adicionais (MSFC-HDBK-3173) devem existir."""
        assert VVMethod.SIMILARITY.value == "similarity"
        assert VVMethod.REVIEW_OF_DESIGN.value == "review_of_design"

    def test_automatability(self):
        """Analysis e Test são automáveis; Inspection e Similarity não."""
        assert VVMethod.ANALYSIS.is_automatable is True
        assert VVMethod.TEST.is_automatable is True
        assert VVMethod.INSPECTION.is_automatable is False
        assert VVMethod.SIMILARITY.is_automatable is False

    def test_partial_automatability(self):
        """Demonstration é parcialmente automável."""
        assert VVMethod.DEMONSTRATION.is_partially_automatable is True
        assert VVMethod.ANALYSIS.is_partially_automatable is False

    def test_descriptions_pt(self):
        """Todos os métodos devem ter descrição em português."""
        for method in VVMethod:
            assert len(method.description_pt) > 10

    def test_when_to_use_pt(self):
        """Todos os métodos devem ter orientação de uso."""
        for method in VVMethod:
            assert len(method.when_to_use_pt) > 10


class TestRequirementLevel:
    """Testes para RequirementLevel."""

    def test_hierarchy_order(self):
        """Mission é o mais alto (0), Component o mais baixo (3)."""
        assert RequirementLevel.MISSION.hierarchy_order == 0
        assert RequirementLevel.SYSTEM.hierarchy_order == 1
        assert RequirementLevel.SUBSYSTEM.hierarchy_order == 2
        assert RequirementLevel.COMPONENT.hierarchy_order == 3


class TestVerificationStatus:
    """Testes para VerificationStatus."""

    def test_terminal_statuses(self):
        """PASS, FAIL e NOT_APPLICABLE são terminais."""
        assert VerificationStatus.PASS.is_terminal is True
        assert VerificationStatus.FAIL.is_terminal is True
        assert VerificationStatus.NOT_APPLICABLE.is_terminal is True
        assert VerificationStatus.NOT_STARTED.is_terminal is False
        assert VerificationStatus.IN_WORK.is_terminal is False

    def test_symbols(self):
        """Todos os status devem ter símbolo."""
        for status in VerificationStatus:
            assert len(status.symbol) > 0


# =====================================================================
# Operator Tests
# =====================================================================


class TestOperator:
    """Testes para o enum Operator."""

    def test_evaluate_gte(self):
        assert Operator.GTE.evaluate(20.0, 20.0) is True
        assert Operator.GTE.evaluate(21.0, 20.0) is True
        assert Operator.GTE.evaluate(19.0, 20.0) is False

    def test_evaluate_lte(self):
        assert Operator.LTE.evaluate(120.0, 120.0) is True
        assert Operator.LTE.evaluate(100.0, 120.0) is True
        assert Operator.LTE.evaluate(121.0, 120.0) is False

    def test_evaluate_eq(self):
        assert Operator.EQ.evaluate(0.0, 0.0) is True
        assert Operator.EQ.evaluate(1.0, 0.0) is False

    def test_evaluate_neq(self):
        assert Operator.NEQ.evaluate(1.0, 0.0) is True
        assert Operator.NEQ.evaluate(0.0, 0.0) is False


# =====================================================================
# Success Criteria Tests
# =====================================================================


class TestThresholdCriteria:
    """Testes para ThresholdCriteria."""

    def test_basic_creation(self):
        criteria = ThresholdCriteria(
            metric="min_sep_m",
            operator=Operator.GTE,
            value=20.0,
            unit="meters",
        )
        assert criteria.type == "threshold"
        assert criteria.metric == "min_sep_m"
        assert criteria.tolerance == 0.0

    def test_tolerance_effective_value(self):
        criteria = ThresholdCriteria(
            metric="x", operator=Operator.GTE, value=20.0, unit="m", tolerance=0.5
        )
        assert criteria.effective_value == 19.5  # 20 - 0.5

    def test_tolerance_lte(self):
        criteria = ThresholdCriteria(
            metric="x", operator=Operator.LTE, value=120.0, unit="s", tolerance=5.0
        )
        assert criteria.effective_value == 125.0  # 120 + 5

    def test_human_readable(self):
        criteria = ThresholdCriteria(
            metric="min_sep", operator=Operator.GTE, value=20.0, unit="m"
        )
        assert "min_sep" in criteria.human_readable
        assert ">=" in criteria.human_readable
        assert "20.0" in criteria.human_readable

    def test_negative_tolerance_rejected(self):
        with pytest.raises(ValidationError):
            ThresholdCriteria(
                metric="x", operator=Operator.GTE, value=20.0, unit="m", tolerance=-1.0
            )


class TestRangeCriteria:
    """Testes para RangeCriteria."""

    def test_valid_range(self):
        criteria = RangeCriteria(
            metric="altitude_m",
            min_value=30.0,
            max_value=400.0,
            unit="meters",
        )
        assert criteria.type == "range"
        assert criteria.inclusive_min is True

    def test_invalid_range_min_gte_max(self):
        with pytest.raises(ValidationError, match="min_value"):
            RangeCriteria(
                metric="x", min_value=400.0, max_value=30.0, unit="m"
            )

    def test_human_readable(self):
        criteria = RangeCriteria(
            metric="alt", min_value=100.0, max_value=400.0, unit="m"
        )
        readable = criteria.human_readable
        assert "alt" in readable
        assert "100.0" in readable
        assert "400.0" in readable


class TestBooleanCriteria:
    """Testes para BooleanCriteria."""

    def test_creation(self):
        criteria = BooleanCriteria(
            metric="geofence_active", expected=True
        )
        assert criteria.type == "boolean"
        assert criteria.expected is True
        assert criteria.scope == Scope.ALL_TIMESTEPS

    def test_human_readable(self):
        criteria = BooleanCriteria(metric="active", expected=True)
        assert "active == True" in criteria.human_readable


class TestStatisticalCriteria:
    """Testes para StatisticalCriteria."""

    def test_mean(self):
        criteria = StatisticalCriteria(
            metric="delay_s",
            aggregation=Aggregation.MEAN,
            operator=Operator.LT,
            value=30.0,
            unit="seconds",
        )
        assert criteria.type == "statistical"

    def test_percentile_requires_value(self):
        with pytest.raises(ValidationError, match="percentile_value"):
            StatisticalCriteria(
                metric="x",
                aggregation=Aggregation.PERCENTILE,
                operator=Operator.LTE,
                value=3.0,
                unit="m",
                # percentile_value missing!
            )

    def test_percentile_value_without_percentile_aggregation(self):
        with pytest.raises(ValidationError, match="percentile_value"):
            StatisticalCriteria(
                metric="x",
                aggregation=Aggregation.MEAN,
                operator=Operator.LTE,
                value=3.0,
                unit="m",
                percentile_value=95.0,  # Should not be here
            )

    def test_valid_percentile(self):
        criteria = StatisticalCriteria(
            metric="error_m",
            aggregation=Aggregation.PERCENTILE,
            percentile_value=95.0,
            operator=Operator.LTE,
            value=3.0,
            unit="meters",
        )
        assert "P95" in criteria.human_readable


class TestTemporalCriteria:
    """Testes para TemporalCriteria."""

    def test_always(self):
        criteria = TemporalCriteria(
            metric="sep_m",
            temporal_operator=TemporalOperator.ALWAYS,
            condition=ThresholdCriteria(
                metric="sep_m", operator=Operator.GTE, value=20.0, unit="m"
            ),
        )
        assert criteria.type == "temporal"
        assert "□" in criteria.human_readable

    def test_with_time_window(self):
        criteria = TemporalCriteria(
            metric="sep_m",
            temporal_operator=TemporalOperator.ALWAYS,
            condition=ThresholdCriteria(
                metric="sep_m", operator=Operator.GTE, value=20.0, unit="m"
            ),
            time_window=TimeWindow(start=0.0, end=300.0, unit="s"),
        )
        assert "[0.0,300.0s]" in criteria.human_readable

    def test_invalid_time_window(self):
        with pytest.raises(ValidationError, match="start"):
            TimeWindow(start=300.0, end=100.0)


class TestCountCriteria:
    """Testes para CountCriteria."""

    def test_zero_violations(self):
        criteria = CountCriteria(
            metric="violations",
            event_condition=ThresholdCriteria(
                metric="sep_m", operator=Operator.LT, value=20.0, unit="m"
            ),
            operator=Operator.EQ,
            value=0,
        )
        assert criteria.type == "count"
        assert "count(" in criteria.human_readable


# =====================================================================
# RequirementRecord Tests
# =====================================================================


class TestRequirementRecord:
    """Testes para o modelo RequirementRecord."""

    def test_valid_requirement(self, valid_threshold_req):
        """Requisito válido deve ser criado sem erros."""
        req = RequirementRecord.model_validate(valid_threshold_req)
        assert req.req_id == "TEST-001"
        assert req.vv_method == VVMethod.ANALYSIS
        assert req.verification_status == VerificationStatus.NOT_STARTED

    def test_missing_vv_method_rejected(self, valid_threshold_req):
        """Requisito sem V&V Method deve ser rejeitado."""
        del valid_threshold_req["vv_method"]
        with pytest.raises(ValidationError):
            RequirementRecord.model_validate(valid_threshold_req)

    def test_missing_success_criteria_rejected(self, valid_threshold_req):
        """Requisito sem Success Criteria deve ser rejeitado."""
        del valid_threshold_req["success_criteria"]
        with pytest.raises(ValidationError):
            RequirementRecord.model_validate(valid_threshold_req)

    def test_invalid_req_id_rejected(self, valid_threshold_req):
        """Req ID com caracteres inválidos deve ser rejeitado."""
        valid_threshold_req["req_id"] = "inválido com espaços!"
        with pytest.raises(ValidationError):
            RequirementRecord.model_validate(valid_threshold_req)

    def test_short_text_rejected(self, valid_threshold_req):
        """Texto muito curto (< 10 chars) deve ser rejeitado."""
        valid_threshold_req["text"] = "Curto"
        with pytest.raises(ValidationError):
            RequirementRecord.model_validate(valid_threshold_req)

    def test_non_automatable_gets_na_status(self):
        """Requisito com método não-automável recebe status NOT_APPLICABLE."""
        req = RequirementRecord.model_validate({
            "req_id": "TEST-INSP",
            "title": "Visual check",
            "text": "O sistema deve ter marcações visuais conformes ao padrão",
            "rationale": "Norma de marcações",
            "level": "component",
            "vv_method": "inspection",
            "success_criteria": {
                "type": "boolean",
                "metric": "markings_ok",
                "expected": True,
                "scope": "final_state",
            },
        })
        assert req.verification_status == VerificationStatus.NOT_APPLICABLE

    def test_to_dvm_row(self, valid_threshold_req):
        """to_dvm_row deve retornar dicionário com colunas da VCRM."""
        req = RequirementRecord.model_validate(valid_threshold_req)
        row = req.to_dvm_row()
        assert "req_id" in row
        assert "title" in row
        assert "level" in row
        assert "vv_method" in row
        assert "success_criteria" in row
        assert "status" in row
        assert "status_symbol" in row

    def test_load_from_file(self, example_requirements_path):
        """Deve carregar todos os requisitos do arquivo de exemplo."""
        requirements = RequirementRecord.load_from_file(example_requirements_path)
        assert len(requirements) == 10
        assert requirements[0].req_id == "VD-SYS-001"

    def test_load_from_nonexistent_file(self):
        """Deve levantar FileNotFoundError para arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            RequirementRecord.load_from_file("nonexistent.json")

    def test_export_json_schema(self, tmp_path):
        """Deve exportar JSON Schema válido."""
        output = tmp_path / "schema.json"
        schema = RequirementRecord.export_json_schema(path=output)
        assert output.exists()
        assert "properties" in schema
        assert "req_id" in schema["properties"]

    def test_discriminated_union_deserialization(self):
        """Pydantic deve escolher o tipo correto de criteria via 'type'."""
        data = {
            "req_id": "TEST-RANGE",
            "title": "Altitude range",
            "text": "O sistema deve manter altitude entre 30m e 400m",
            "rationale": "Envelope de voo",
            "level": "system",
            "vv_method": "analysis",
            "success_criteria": {
                "type": "range",
                "metric": "altitude_m",
                "min_value": 30.0,
                "max_value": 400.0,
                "unit": "meters",
            },
        }
        req = RequirementRecord.model_validate(data)
        assert isinstance(req.success_criteria, RangeCriteria)
