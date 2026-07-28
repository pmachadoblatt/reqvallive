"""Testes para o Vampire Detector (SchemaValidator)."""

import pytest

from simreqvalidator.schema import RequirementRecord, SchemaValidator
from simreqvalidator.schema.validator import IssueSeverity


class TestSchemaValidatorSingle:
    """Testes de validação individual de requisitos."""

    def test_valid_requirement_passes(self, valid_threshold_req):
        """Requisito válido deve passar sem erros."""
        validator = SchemaValidator()
        req, issues = validator.validate_single(valid_threshold_req)
        assert req is not None
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        assert len(errors) == 0

    def test_invalid_schema_returns_errors(self):
        """Dados inválidos devem retornar erros de schema."""
        validator = SchemaValidator()
        req, issues = validator.validate_single({"req_id": "X"})
        assert req is None
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        assert len(errors) > 0

    def test_vague_terms_detected(self, vampire_req):
        """Termos vagos devem ser detectados como warnings."""
        validator = SchemaValidator()
        req, issues = validator.validate_single(vampire_req)
        vague_issues = [i for i in issues if i.code == "VAGUE_TERM_DETECTED"]
        assert len(vague_issues) > 0
        assert vague_issues[0].severity == IssueSeverity.WARNING

    def test_shall_statement_missing(self):
        """Requisito sem 'deve'/'shall' deve gerar warning."""
        validator = SchemaValidator()
        data = {
            "req_id": "TEST-NOSHALL",
            "title": "No shall",
            "text": "O sistema mantém separação mínima de 20 metros entre aeronaves",
            "rationale": "Segurança",
            "level": "system",
            "vv_method": "analysis",
            "success_criteria": {
                "type": "threshold",
                "metric": "sep_m",
                "operator": ">=",
                "value": 20.0,
                "unit": "m",
            },
        }
        req, issues = validator.validate_single(data)
        shall_issues = [i for i in issues if i.code == "NO_SHALL_STATEMENT"]
        assert len(shall_issues) == 1

    def test_shall_statement_pt_accepted(self, valid_threshold_req):
        """Requisito com 'deve' (PT) deve passar."""
        validator = SchemaValidator()
        req, issues = validator.validate_single(valid_threshold_req)
        shall_issues = [i for i in issues if i.code == "NO_SHALL_STATEMENT"]
        assert len(shall_issues) == 0

    def test_strict_traceability_missing_conops(self):
        """Com strict_traceability, ausência de conops_ref gera warning."""
        validator = SchemaValidator(strict_traceability=True)
        data = {
            "req_id": "TEST-NOTRACE",
            "title": "No trace",
            "text": "O sistema deve manter separação mínima de 20 metros",
            "rationale": "Segurança",
            "level": "system",
            "vv_method": "analysis",
            "success_criteria": {
                "type": "threshold",
                "metric": "sep_m",
                "operator": ">=",
                "value": 20.0,
                "unit": "m",
            },
        }
        req, issues = validator.validate_single(data)
        conops_issues = [i for i in issues if i.code == "MISSING_CONOPS_REF"]
        assert len(conops_issues) == 1

    def test_non_automatable_method_info(self):
        """Método não-automável deve gerar info."""
        validator = SchemaValidator()
        data = {
            "req_id": "TEST-INSP",
            "title": "Inspeção visual",
            "text": "O sistema deve ter marcações visuais claras e conformes",
            "rationale": "Norma de marcação",
            "level": "component",
            "vv_method": "inspection",
            "success_criteria": {
                "type": "boolean",
                "metric": "marks_ok",
                "expected": True,
                "scope": "final_state",
            },
        }
        req, issues = validator.validate_single(data)
        auto_issues = [i for i in issues if i.code == "NOT_AUTOMATABLE"]
        assert len(auto_issues) == 1
        assert auto_issues[0].severity == IssueSeverity.INFO


class TestSchemaValidatorBatch:
    """Testes de validação em lote."""

    def test_batch_validates_all(self, example_requirements_data):
        """Validação em lote deve processar todos os requisitos."""
        validator = SchemaValidator()
        valid_reqs, report = validator.validate_batch(example_requirements_data)
        assert report.total_requirements == len(example_requirements_data)
        assert report.valid_count + report.invalid_count == report.total_requirements

    def test_batch_finds_vampires(self, example_requirements_data):
        """O banco de exemplo contém pelo menos 1 vampiro (VD-VAMPIRE-001)."""
        validator = SchemaValidator()
        valid_reqs, report = validator.validate_batch(example_requirements_data)
        assert report.vampire_count >= 1

        vampire_ids = [v.req_id for v in report.vampire_reports if v.is_vampire]
        assert "VD-VAMPIRE-001" in vampire_ids

    def test_batch_quality_score(self, example_requirements_data):
        """Score de qualidade deve estar entre 0 e 100."""
        validator = SchemaValidator()
        _, report = validator.validate_batch(example_requirements_data)
        assert 0.0 <= report.quality_score <= 100.0

    def test_batch_report_summary(self, example_requirements_data):
        """Relatório deve ter summary legível."""
        validator = SchemaValidator()
        _, report = validator.validate_batch(example_requirements_data)
        summary = report.summary
        assert "Relatório" in summary
        assert "Válidos" in summary


class TestVampireDetection:
    """Testes específicos para detecção de vampiros."""

    def test_good_requirement_not_vampire(self, valid_threshold_req):
        """Requisito bem formado NÃO deve ser vampiro."""
        validator = SchemaValidator()
        req = RequirementRecord.model_validate(valid_threshold_req)
        reports = validator.detect_vampires([req])
        assert len(reports) == 1
        assert reports[0].is_vampire is False
        assert reports[0].quality_score >= 50.0

    def test_vampire_detected(self, vampire_req):
        """Requisito com termos vagos + sem rastreabilidade deve ser vampiro."""
        validator = SchemaValidator()
        req = RequirementRecord.model_validate(vampire_req)
        reports = validator.detect_vampires([req])
        assert len(reports) == 1
        assert reports[0].is_vampire is True
        assert reports[0].quality_score <= 50.0
        assert len(reports[0].vague_terms_found) > 0
        assert len(reports[0].vampire_reasons) > 0

    def test_vampire_with_custom_terms(self):
        """Deve detectar termos vagos customizados."""
        validator = SchemaValidator(vague_terms=["xablau", "mágico"])
        data = {
            "req_id": "TEST-CUSTOM",
            "title": "Custom terms",
            "text": "O sistema deve ser xablau e mágico na operação de voo",
            "rationale": "Requisito genérico",
            "level": "system",
            "vv_method": "analysis",
            "success_criteria": {
                "type": "threshold",
                "metric": "x",
                "operator": ">=",
                "value": 1.0,
                "unit": "u",
            },
        }
        req = RequirementRecord.model_validate(data)
        reports = validator.detect_vampires([req])
        assert len(reports[0].vague_terms_found) >= 2

    def test_check_automatable(self, valid_threshold_req, vampire_req):
        """check_automatable deve retornar True para analysis, False para inspection."""
        validator = SchemaValidator()
        req_auto = RequirementRecord.model_validate(valid_threshold_req)
        req_manual = RequirementRecord.model_validate(vampire_req)
        assert validator.check_automatable(req_auto) is True
        assert validator.check_automatable(req_manual) is False
