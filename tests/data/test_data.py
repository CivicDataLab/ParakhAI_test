"""
Centralised test data for the Parakh test framework.

Usage in tests:
    from tests.data.test_data import TestUsers, TestURLs, TestExpected, TestValidation

Keep *real* credentials out of this file — they live in .env and are loaded
by Config.  The classes below define structure and safe fallback values only.
"""

from utils.config import Config


class TestUsers:
    """
    Test account credentials loaded from environment variables.

    Two user slots (USER_1, USER_2) allow parallel test runs with different
    accounts so tests don't collide on shared state.
    """
    # Primary test account — use for most functional tests
    USER_1 = {
        "email": Config.TEST_EMAIL_1,
        "password": Config.TEST_PASSWORD_1,
        "label": "Primary test user",
    }
    # Secondary test account — used for parallel runs or multi-user scenarios
    USER_2 = {
        "email": Config.TEST_EMAIL_2,
        "password": Config.TEST_PASSWORD_2,
        "label": "Secondary test user",
    }

    # Dummy credentials — safe to commit; must never match a real account
    INVALID = {
        "email": "notareal@example.invalid",
        "password": "WrongPassword!999",
        "label": "Invalid / negative test credentials",
    }
    EMPTY = {
        "email": "",
        "password": "",
        "label": "Empty credentials (form validation tests)",
    }

    @classmethod
    def by_index(cls, index: int) -> dict:
        """Return USER_1 or USER_2 based on an integer index (1-based)."""
        return cls.USER_2 if index == 2 else cls.USER_1


class TestURLs:
    """Relative paths used in navigation and redirect assertions."""
    HOME = "/"
    DASHBOARD = "/dashboard"
    LOGIN = "/login"
    REGISTER = "/register"
    PROFILE = "/profile"
    EVALUATION_WORKSPACE = "/evaluation"

    @classmethod
    def absolute(cls, path: str) -> str:
        """Return an absolute URL for *path*."""
        return Config.url(path)


class TestExpected:
    """
    Expected strings, titles, and counts used in assertions.

    Update these when the UI copy changes — having them in one place prevents
    brittle duplication across dozens of test files.
    """
    # Page title fragments
    PAGE_TITLE_HOME = "Parakh"
    PAGE_TITLE_DASHBOARD = "Dashboard"
    PAGE_TITLE_LOGIN = "Sign in"

    # Footer
    FOOTER_COPYRIGHT_TEXT = "CivicDataLab"

    # Hero / marketing copy — partial match is fine
    HERO_HEADING_KEYWORDS = ["parakh", "evaluate", "ai", "model", "assessment"]

    # Error message keywords expected on failed login
    AUTH_ERROR_KEYWORDS = [
        "invalid", "incorrect", "wrong", "failed", "error",
        "credentials", "username", "password", "not found",
    ]

    # Minimum number of social links expected in the footer
    MIN_SOCIAL_LINKS = 1

    # Performance budgets (seconds)
    MAX_PAGE_LOAD_SECONDS = 5.0
    MAX_TTFB_MS = 800

    # Accessibility
    WCAG_CONTRAST_RATIO_AA = 4.5
    WCAG_CONTRAST_RATIO_AA_LARGE = 3.0


class TestValidation:
    """
    Parametrised data sets for form validation tests.

    These are lists/tuples suitable for use with @pytest.mark.parametrize.
    """
    # (email, password, expected_error_keyword)
    INVALID_CREDENTIALS = [
        ("bad@example.invalid", "wrongpassword", "invalid"),
        ("notanemail", "somepassword", "invalid"),
        ("", "somepassword", ""),     # empty email → HTML5 required or server error
        ("user@example.invalid", "", ""),  # empty password → HTML5 required or server error
    ]

    # Emails that should fail basic format validation
    MALFORMED_EMAILS = [
        "plainaddress",
        "@missingdomain.com",
        "missing@.com",
        "two@@at.com",
    ]


class TestGraphQL:
    """GraphQL query and mutation strings used in API contract tests."""

    # ── Public / health ───────────────────────────────────────────────────────
    QUERY_HELLO = "{ hello }"
    QUERY_HEALTH = "{ healthCheck }"

    # ── Public registry data (anonymous-allowed) ──────────────────────────────
    QUERY_AI_MODELS = """
        query AiModels($limit: Int) {
          aiModels(limit: $limit) { id name modelType provider isPublic }
        }
    """
    QUERY_PROMPT_DATASETS = """
        query PromptDatasets {
          promptDatasets { id }
        }
    """
    QUERY_PROMPT_DATASET = """
        query PromptDataset($datasetId: ID!) {
          promptDataset(datasetId: $datasetId) { id name }
        }
    """
    QUERY_TEST_CASES = """
        query TestCases($datasetId: ID!, $limit: Int) {
          testCases(datasetId: $datasetId, limit: $limit) { id input }
        }
    """
    QUERY_MODULES_BY_MODEL_TYPE = """
        query Modules($modelType: String!) {
          modulesByModelType(modelType: $modelType) { name displayName }
        }
    """
    QUERY_METRICS_BY_MODEL_TYPE = """
        query Metrics($modelType: String!) {
          metricsByModelType(modelType: $modelType) { name displayName }
        }
    """
    QUERY_SECTORS = """
        query Sectors($limit: Int) {
          sectors(limit: $limit) { id name }
        }
    """

    # ── Authenticated read queries ────────────────────────────────────────────
    QUERY_MY_ORGANIZATIONS = """
        query MyOrganizations { myOrganizations { id name slug } }
    """
    QUERY_MY_MODELS = "query MyModels { myModels { id name modelType } }"
    QUERY_MY_AUDITS = "query MyAudits { myAudits { id } }"
    QUERY_AUDITS = """
        query Audits($status: String, $modelId: ID) {
          audits(status: $status, modelId: $modelId) { id name status modelId }
        }
    """
    QUERY_AUDIT = """
        query Audit($auditId: ID!) {
          audit(auditId: $auditId) {
            id name status auditType progressPercentage
            totalTests passedTests failedTests
            createdAt completedAt
          }
        }
    """
    QUERY_AUDIT_METRICS = """
        query AuditMetrics {
          auditMetrics { evaluationRuns testCasesCount models issuesFlagged }
        }
    """
    QUERY_AUDIT_DOMAIN_OPTIONS = """
        query AuditDomainOptions($domain: String!) {
          auditDomainOptions(domain: $domain) { code displayName }
        }
    """
    QUERY_AUDIT_TESTS = """
        query AuditTests($auditId: ID!) {
          auditTests(auditId: $auditId) { id testInput }
        }
    """
    QUERY_AUDIT_TASKS = """
        query AuditTasks($auditId: ID!, $tool: String, $metric: String, $status: String) {
          auditTasks(auditId: $auditId, tool: $tool, metric: $metric, status: $status) { id status }
        }
    """
    QUERY_AUDIT_RESULTS = """
        query AuditResults($auditId: ID!, $tool: String, $metric: String) {
          auditResults(auditId: $auditId, tool: $tool, metric: $metric) { id }
        }
    """
    QUERY_AUDIT_SUMMARIES = """
        query AuditSummaries($auditId: ID!) {
          auditSummaries(auditId: $auditId) { id }
        }
    """
    QUERY_ORGANIZATION_AUDITORS = """
        query OrganizationAuditors($organizationId: ID!) {
          organizationAuditors(organizationId: $organizationId) { auditors { id } }
        }
    """
    QUERY_AUDITOR_ASSIGNMENTS = """
        query AuditorAssignments($status: String) {
          auditorAssignments(status: $status) {
            id status auditorEmail modelId modelName
          }
        }
    """
    QUERY_AUDITOR_ASSIGNMENT = """
        query AuditorAssignment($assignmentId: ID!) {
          auditorAssignment(assignmentId: $assignmentId) { id status }
        }
    """
    QUERY_MY_ASSIGNMENTS = """
        query MyAssignments($modelId: String, $status: String) {
          myAssignments(modelId: $modelId, status: $status) { id status }
        }
    """
    QUERY_MY_EVALUATIONS = """
        query MyEvaluations($modelId: String, $status: String) {
          myEvaluations(modelId: $modelId, status: $status) { id }
        }
    """
    QUERY_SEARCH_USER_BY_EMAIL = """
        query SearchUser($email: String!) {
          searchUserByEmail(email: $email) { user { id email } }
        }
    """

    # ── Audit lifecycle mutations ─────────────────────────────────────────────
    MUTATION_REQUEST_AUDIT = """
        mutation RequestAudit($input: RequestAuditInput!) {
          requestAudit(input: $input) { success message audit { id name status } }
        }
    """
    MUTATION_CREATE_BLANK_AUDIT = """
        mutation CreateBlankAudit($input: CreateBlankAuditInput!) {
          createBlankAudit(input: $input) { success message audit { id name status } }
        }
    """
    MUTATION_UPDATE_AUDIT = """
        mutation UpdateAudit($input: UpdateAuditInput!) {
          updateAudit(input: $input) { success message audit { id name status } }
        }
    """
    MUTATION_RUN_AUDIT = """
        mutation RunAudit($input: RunAuditInput!) {
          runAudit(input: $input) { success message audit { id status } }
        }
    """

    # ── Auditor mutations ─────────────────────────────────────────────────────
    MUTATION_ASSIGN_AUDITOR_TO_VERSION = """
        mutation AssignAuditor($input: AssignAuditorToVersionInput!) {
          assignAuditorToVersion(input: $input) {
            success message assignment { id status auditorEmail }
          }
        }
    """
    MUTATION_UPDATE_AUDITOR_ASSIGNMENT_STATUS = """
        mutation UpdateAssignmentStatus($assignmentId: ID!, $status: String!) {
          updateAuditorAssignmentStatus(assignmentId: $assignmentId, status: $status) {
            success message assignment { id status }
          }
        }
    """
    MUTATION_ADD_AUDITOR_TO_ORGANIZATION = """
        mutation AddAuditor($organizationId: ID!, $input: AddAuditorInput!) {
          addAuditorToOrganization(organizationId: $organizationId, input: $input) {
            success message
          }
        }
    """
    MUTATION_REMOVE_AUDITOR_FROM_ORGANIZATION = """
        mutation RemoveAuditor($organizationId: ID!, $userId: ID!) {
          removeAuditorFromOrganization(organizationId: $organizationId, userId: $userId) {
            success message
          }
        }
    """

    # ── Manual evaluation mutations ───────────────────────────────────────────
    MUTATION_CALL_MODEL_FOR_MANUAL_EVAL = """
        mutation CallModel($input: CallModelInput!) {
          callModelForManualEval(input: $input) {
            success message output latencyMs
          }
        }
    """
    MUTATION_SUBMIT_MANUAL_TEST_CASE = """
        mutation SubmitManual($input: SubmitManualTestCaseInput!) {
          submitManualTestCase(input: $input) { success message }
        }
    """
    MUTATION_COMPLETE_MODULE_EVALUATION = """
        mutation CompleteModule($input: CompleteModuleEvaluationInput!) {
          completeModuleEvaluation(input: $input) {
            success message canFinishEvaluation
          }
        }
    """
    MUTATION_FINISH_MANUAL_EVALUATION = """
        mutation FinishEval($input: FinishManualEvaluationInput!) {
          finishManualEvaluation(input: $input) { success message }
        }
    """

    # ── Legacy (still referenced by some tests) ───────────────────────────────
    MUTATION_CREATE_DATASET = """
        mutation CreateDataset($input: CreateDatasetInput!) {
          createDataset(input: $input) { success message dataset { id name } }
        }
    """


class TestSandbox:
    """Sandbox-org constants for write-side regression tests.

    Keep magic strings out of test bodies. Tests should reach for these
    rather than hardcoding role names, audit statuses, or org slugs.
    """

    @classmethod
    def org_slug(cls) -> str:
        """Active sandbox slug — empty string when unset (tests skip)."""
        return Config.SANDBOX_ORG_SLUG

    # Auditor assignment statuses (from ParakhAPI mutation enum)
    ASSIGNMENT_STATUS_PENDING = "PENDING"
    ASSIGNMENT_STATUS_ACCEPTED = "ACCEPTED"
    ASSIGNMENT_STATUS_DECLINED = "DECLINED"
    ASSIGNMENT_STATUS_COMPLETED = "COMPLETED"

    # Manual eval submission statuses
    MANUAL_RESULT_PASSED = "PASSED"
    MANUAL_RESULT_FAILED = "FAILED"

    # Audit type domains (for new evaluation wizard regression)
    AUDIT_TYPE_TECHNICAL = "Technical"
    AUDIT_TYPE_DOMAIN = "Domain"
    AUDIT_TYPE_CULTURAL = "Cultural"

    # Evaluation modes
    MODE_AUTOMATED = "automated"
    MODE_MANUAL = "manual"


class TestModelConstants:
    """Enum-like constants for model types, providers, and statuses."""

    MODEL_TYPES = [
        "TRANSLATION", "TEXT_GENERATION", "SUMMARIZATION", "QA",
        "SENTIMENT_ANALYSIS", "TEXT_CLASSIFICATION", "NER",
        "TEXT_TO_SPEECH", "SPEECH_TO_TEXT", "OTHER",
    ]
    PROVIDERS = [
        "OPENAI", "LLAMA_OLLAMA", "LLAMA_TOGETHER", "LLAMA_REPLICATE",
        "LLAMA_CUSTOM", "CUSTOM", "HUGGINGFACE",
    ]
    AUDIT_STATUSES = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
    DATASET_TYPES = [
        "TRANSLATION", "GENERATION", "SUMMARIZATION", "QA", "SENTIMENT",
        "CLASSIFICATION", "NER", "BIAS", "TOXICITY", "GENERAL",
    ]
    RISK_LEVELS = ["HIGH_RISK", "MEDIUM_RISK", "LOW_RISK", "NO_RISK"]
