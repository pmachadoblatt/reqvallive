"""Métodos de Verificação e Validação (V&V) e enumerações de apoio.

Definições baseadas nos 4 métodos fundamentais do MSFC-HDBK-3173 (NASA),
complementados pelos métodos adicionais reconhecidos pelo handbook
(Similarity e Review of Design) e pelo ECSS-E-ST-10-02C.

Referências:
    - MSFC-HDBK-3173, Section 4: "Methods of Verification"
    - IEEE 29148:2018, Section 6.6: "Verification methods"
    - ECSS-E-ST-10-02C, Section 5: "Verification methods"
    - SIS-08 Methods (Prof. Christopher), Slides 17-20
"""

from enum import Enum


class VVMethod(str, Enum):
    """Métodos de Verificação e Validação.

    Os 4 métodos fundamentais são universais em todos os standards
    (MSFC-HDBK-3173, IEEE 29148, ECSS-E-ST-10-02C):

    - INSPECTION: Exame visual/qualitativo do produto realizado
    - ANALYSIS: Avaliação por técnicas analíticas (simulação, modelagem, estatística)
    - DEMONSTRATION: Operação que demonstra resultado sem coleta detalhada de dados
    - TEST: Operação sob condições controladas com instrumentação

    Métodos adicionais (MSFC-HDBK-3173):
    - SIMILARITY: Comparação com sistema similar já verificado
    - REVIEW_OF_DESIGN: Revisão de documentos de design (ECSS)
    """

    # Métodos fundamentais (IADT)
    INSPECTION = "inspection"
    ANALYSIS = "analysis"
    DEMONSTRATION = "demonstration"
    TEST = "test"

    # Métodos adicionais
    SIMILARITY = "similarity"
    REVIEW_OF_DESIGN = "review_of_design"

    @property
    def is_automatable(self) -> bool:
        """Indica se o método é automável pela ferramenta.

        Apenas Analysis e Test são plenamente automáveis por simulação.
        Demonstration é parcialmente automável.
        Inspection, Similarity e Review of Design requerem ação humana.
        """
        return self in (VVMethod.ANALYSIS, VVMethod.TEST)

    @property
    def is_partially_automatable(self) -> bool:
        """Indica se o método é parcialmente automável."""
        return self == VVMethod.DEMONSTRATION

    @property
    def description_pt(self) -> str:
        """Descrição em português do método de V&V."""
        descriptions = {
            VVMethod.INSPECTION: (
                "Exame visual de desenhos, dados ou atributos físicos do produto "
                "(dimensões, peso, cor, marcações)"
            ),
            VVMethod.ANALYSIS: (
                "Avaliação por técnicas analíticas geralmente aceitas: modelagem "
                "matemática, simulação computacional, estatística, modelagem análoga"
            ),
            VVMethod.DEMONSTRATION: (
                "Demonstração de que o uso ou operação atinge os resultados, "
                "sem coleta detalhada de dados. Resultado tipicamente pass/fail"
            ),
            VVMethod.TEST: (
                "Operação do equipamento sob condições controladas ou ambientes "
                "operacionais especificados para avaliar desempenho, com instrumentação"
            ),
            VVMethod.SIMILARITY: (
                "Avaliação por revisão de dados de aceitação prévios de sistema "
                "similar ou idêntico em design e processo de fabricação"
            ),
            VVMethod.REVIEW_OF_DESIGN: (
                "Verificação por validação de registros, documentos de design "
                "aprovados, relatórios técnicos ou desenhos de engenharia"
            ),
        }
        return descriptions[self]

    @property
    def when_to_use_pt(self) -> str:
        """Orientação de quando usar este método (MSFC-HDBK-3173, slide 20)."""
        guidance = {
            VVMethod.INSPECTION: (
                "Quando desenhos, documentos ou dados podem ser verificados visualmente "
                "para confirmar que características físicas foram projetadas no produto"
            ),
            VVMethod.ANALYSIS: (
                "Quando técnicas analíticas precisas são possíveis; teste não é "
                "custo-efetivo; inspeção não é adequada; modelos foram validados"
            ),
            VVMethod.DEMONSTRATION: (
                "Quando funções projetadas podem ser verificadas por observação; "
                "resultados são pass/fail; requisitos são subjetivos (fatores humanos)"
            ),
            VVMethod.TEST: (
                "Quando técnicas analíticas não produzem resultados adequados; "
                "modos de falha comprometem segurança; interfaces críticas do sistema"
            ),
            VVMethod.SIMILARITY: (
                "Quando sistema similar já foi qualificado previamente e ambientes "
                "previstos são similares. NÃO usar para itens de criticidade 1/1R"
            ),
            VVMethod.REVIEW_OF_DESIGN: (
                "Quando verificação é alcançada por validação de registros, "
                "documentos de design aprovados ou relatórios técnicos"
            ),
        }
        return guidance[self]


class RequirementLevel(str, Enum):
    """Nível hierárquico do requisito no sistema.

    Baseado na hierarquia PBS (Product Breakdown Structure) do SIS-08:
    Mission > System > Subsystem > Component

    O nível determina em qual camada da arquitetura o requisito
    deve ser verificado (ECSS: bottom-up verification approach).
    """

    MISSION = "mission"
    SYSTEM = "system"
    SUBSYSTEM = "subsystem"
    COMPONENT = "component"

    @property
    def hierarchy_order(self) -> int:
        """Ordem hierárquica (0 = mais alto)."""
        order = {
            RequirementLevel.MISSION: 0,
            RequirementLevel.SYSTEM: 1,
            RequirementLevel.SUBSYSTEM: 2,
            RequirementLevel.COMPONENT: 3,
        }
        return order[self]


class VerificationStatus(str, Enum):
    """Status de verificação do requisito.

    Segue o fluxo de status do VCRM (MSFC-HDBK-3173):
    Not Started → In Work → Pass/Fail/Warning

    Warning indica que o requisito passou, mas com margem
    inferior ao desejável (conceito de 'design margin' do MTL).
    """

    NOT_STARTED = "not_started"
    IN_WORK = "in_work"
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"  # Passou, mas com margem pequena
    NOT_APPLICABLE = "not_applicable"  # Método não automável (e.g., Inspection)
    ERROR = "error"  # Erro na execução da verificação

    @property
    def is_terminal(self) -> bool:
        """Indica se é um status final (não muda mais)."""
        return self in (
            VerificationStatus.PASS,
            VerificationStatus.FAIL,
            VerificationStatus.NOT_APPLICABLE,
        )

    @property
    def symbol(self) -> str:
        """Símbolo para uso em relatórios."""
        symbols = {
            VerificationStatus.NOT_STARTED: "⬜",
            VerificationStatus.IN_WORK: "🔄",
            VerificationStatus.PASS: "✅",
            VerificationStatus.FAIL: "❌",
            VerificationStatus.WARNING: "⚠️",
            VerificationStatus.NOT_APPLICABLE: "➖",
            VerificationStatus.ERROR: "🔴",
        }
        return symbols[self]


class Priority(str, Enum):
    """Prioridade do requisito (IEEE 29148:2018)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
