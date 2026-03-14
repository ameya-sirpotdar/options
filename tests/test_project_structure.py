import os
import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


EXPECTED_PATHS = [
    # Backend package init files
    "backend/api/__init__.py",
    "backend/agents/__init__.py",
    "backend/services/__init__.py",
    "backend/models/__init__.py",
    "backend/requirements.txt",
    # Consolidated backend services
    "backend/services/schwab_service.py",
    "backend/services/trades_comparison_service.py",
    "backend/services/polling_service.py",
    # Backend models (one-per-file layout)
    "backend/models/options_contract.py",
    "backend/models/options_chain_request.py",
    "backend/models/options_chain_response.py",
    "backend/models/tradability_score.py",
    "backend/models/tradability_metrics.py",
    # Backend agents
    "backend/agents/options_data_agent.py",
    "backend/agents/tradability_agent.py",
    "backend/agents/metrics_agent.py",
    "backend/agents/workflow.py",
    "backend/agents/state.py",
    # Backend API routers
    "backend/api/routers/trades.py",
    "backend/api/routers/options_chain.py",
    # Tests package init files
    "tests/services/__init__.py",
    "tests/agents/__init__.py",
    "tests/models/__init__.py",
    # Tests for consolidated services
    "tests/services/test_schwab_service.py",
    "tests/services/test_trades_comparison_service.py",
    # Tests for agents
    "tests/agents/test_options_data_agent.py",
    "tests/agents/test_tradability_agent.py",
    "tests/agents/test_metrics_agent.py",
    # Tests for models
    "tests/models/test_model_imports.py",
    # Frontend
    "frontend/vue-app/.gitkeep",
    "frontend/vue-app/src/api/endpoints.js",
    "frontend/vue-app/src/composables/useMarketData.js",
    # Infra
    "infra/bicep/main.bicep",
    "infra/bicep/main.bicepparam.example",
    "infra/bicep/modules/acr.bicep",
    "infra/bicep/modules/aks.bicep",
    "infra/bicep/modules/storage.bicep",
    "infra/README.md",
    "infra/k8s/deployment.yaml",
    "infra/k8s/service.yaml",
    "backend/Dockerfile",
    "tests/test_project_structure.py",
]


@pytest.mark.parametrize("relative_path", EXPECTED_PATHS)
def test_expected_path_exists(relative_path):
    full_path = os.path.join(REPO_ROOT, relative_path)
    assert os.path.exists(full_path), (
        f"Expected path does not exist in repository: {relative_path}"
    )


def test_backend_api_is_python_package():
    init_file = os.path.join(REPO_ROOT, "backend", "api", "__init__.py")
    assert os.path.isfile(init_file), (
        "backend/api/__init__.py must be a file to qualify as a Python package"
    )


def test_backend_agents_is_python_package():
    init_file = os.path.join(REPO_ROOT, "backend", "agents", "__init__.py")
    assert os.path.isfile(init_file), (
        "backend/agents/__init__.py must be a file to qualify as a Python package"
    )


def test_backend_services_is_python_package():
    init_file = os.path.join(REPO_ROOT, "backend", "services", "__init__.py")
    assert os.path.isfile(init_file), (
        "backend/services/__init__.py must be a file to qualify as a Python package"
    )


def test_backend_models_is_python_package():
    init_file = os.path.join(REPO_ROOT, "backend", "models", "__init__.py")
    assert os.path.isfile(init_file), (
        "backend/models/__init__.py must be a file to qualify as a Python package"
    )


def test_backend_requirements_txt_is_not_empty():
    req_file = os.path.join(REPO_ROOT, "backend", "requirements.txt")
    assert os.path.isfile(req_file), (
        "backend/requirements.txt must exist"
    )
    assert os.path.getsize(req_file) > 0, (
        "backend/requirements.txt must not be empty"
    )


def test_frontend_vue_app_directory_exists():
    vue_app_dir = os.path.join(REPO_ROOT, "frontend", "vue-app")
    assert os.path.isdir(vue_app_dir), (
        "frontend/vue-app/ directory must exist"
    )


def test_infra_k8s_directory_exists():
    k8s_dir = os.path.join(REPO_ROOT, "infra", "k8s")
    assert os.path.isdir(k8s_dir), (
        "infra/k8s/ directory must exist"
    )


def test_backend_dockerfile_exists():
    dockerfile = os.path.join(REPO_ROOT, "backend", "Dockerfile")
    assert os.path.isfile(dockerfile), (
        "backend/Dockerfile must exist"
    )


def test_infra_bicep_directory_exists():
    bicep_dir = os.path.join(REPO_ROOT, "infra", "bicep")
    assert os.path.isdir(bicep_dir), (
        "infra/bicep/ directory must exist"
    )


def test_infra_bicep_modules_directory_exists():
    modules_dir = os.path.join(REPO_ROOT, "infra", "bicep", "modules")
    assert os.path.isdir(modules_dir), (
        "infra/bicep/modules/ directory must exist"
    )


def test_infra_bicep_main_bicep_exists():
    main_bicep = os.path.join(REPO_ROOT, "infra", "bicep", "main.bicep")
    assert os.path.isfile(main_bicep), (
        "infra/bicep/main.bicep must exist"
    )


def test_infra_bicep_main_bicepparam_example_exists():
    param_example = os.path.join(REPO_ROOT, "infra", "bicep", "main.bicepparam.example")
    assert os.path.isfile(param_example), (
        "infra/bicep/main.bicepparam.example must exist"
    )


def test_infra_bicep_aks_module_exists():
    aks_bicep = os.path.join(REPO_ROOT, "infra", "bicep", "modules", "aks.bicep")
    assert os.path.isfile(aks_bicep), (
        "infra/bicep/modules/aks.bicep must exist"
    )


def test_infra_bicep_acr_module_exists():
    acr_bicep = os.path.join(REPO_ROOT, "infra", "bicep", "modules", "acr.bicep")
    assert os.path.isfile(acr_bicep), (
        "infra/bicep/modules/acr.bicep must exist"
    )


def test_infra_bicep_storage_module_exists():
    storage_bicep = os.path.join(REPO_ROOT, "infra", "bicep", "modules", "storage.bicep")
    assert os.path.isfile(storage_bicep), (
        "infra/bicep/modules/storage.bicep must exist"
    )


def test_infra_readme_exists():
    readme = os.path.join(REPO_ROOT, "infra", "README.md")
    assert os.path.isfile(readme), (
        "infra/README.md must exist"
    )


def test_backend_directory_exists():
    backend_dir = os.path.join(REPO_ROOT, "backend")
    assert os.path.isdir(backend_dir), (
        "backend/ directory must exist"
    )


def test_frontend_directory_exists():
    frontend_dir = os.path.join(REPO_ROOT, "frontend")
    assert os.path.isdir(frontend_dir), (
        "frontend/ directory must exist"
    )


def test_infra_directory_exists():
    infra_dir = os.path.join(REPO_ROOT, "infra")
    assert os.path.isdir(infra_dir), (
        "infra/ directory must exist"
    )


def test_tests_directory_exists():
    tests_dir = os.path.join(REPO_ROOT, "tests")
    assert os.path.isdir(tests_dir), (
        "tests/ directory must exist"
    )


def test_tests_services_is_python_package():
    init_file = os.path.join(REPO_ROOT, "tests", "services", "__init__.py")
    assert os.path.isfile(init_file), (
        "tests/services/__init__.py must be a file to qualify as a Python package"
    )


def test_tests_agents_is_python_package():
    init_file = os.path.join(REPO_ROOT, "tests", "agents", "__init__.py")
    assert os.path.isfile(init_file), (
        "tests/agents/__init__.py must be a file to qualify as a Python package"
    )


def test_tests_models_is_python_package():
    init_file = os.path.join(REPO_ROOT, "tests", "models", "__init__.py")
    assert os.path.isfile(init_file), (
        "tests/models/__init__.py must be a file to qualify as a Python package"
    )


def test_backend_api_routers_directory_exists():
    routers_dir = os.path.join(REPO_ROOT, "backend", "api", "routers")
    assert os.path.isdir(routers_dir), (
        "backend/api/routers/ directory must exist"
    )


def test_consolidated_schwab_service_exists():
    schwab_service = os.path.join(REPO_ROOT, "backend", "services", "schwab_service.py")
    assert os.path.isfile(schwab_service), (
        "backend/services/schwab_service.py must exist as the consolidated Schwab service"
    )


def test_consolidated_trades_comparison_service_exists():
    trades_service = os.path.join(
        REPO_ROOT, "backend", "services", "trades_comparison_service.py"
    )
    assert os.path.isfile(trades_service), (
        "backend/services/trades_comparison_service.py must exist as the consolidated "
        "trades comparison service"
    )


def test_model_files_exist():
    model_files = [
        "options_contract.py",
        "options_chain_request.py",
        "options_chain_response.py",
        "tradability_score.py",
        "tradability_metrics.py",
    ]
    for model_file in model_files:
        full_path = os.path.join(REPO_ROOT, "backend", "models", model_file)
        assert os.path.isfile(full_path), (
            f"backend/models/{model_file} must exist in the one-per-file model layout"
        )


def test_trades_router_exists():
    trades_router = os.path.join(REPO_ROOT, "backend", "api", "routers", "trades.py")
    assert os.path.isfile(trades_router), (
        "backend/api/routers/trades.py must exist for the RESTful trades API"
    )


def test_options_chain_router_exists():
    options_chain_router = os.path.join(
        REPO_ROOT, "backend", "api", "routers", "options_chain.py"
    )
    assert os.path.isfile(options_chain_router), (
        "backend/api/routers/options_chain.py must exist"
    )


def test_frontend_endpoints_js_exists():
    endpoints_js = os.path.join(
        REPO_ROOT, "frontend", "vue-app", "src", "api", "endpoints.js"
    )
    assert os.path.isfile(endpoints_js), (
        "frontend/vue-app/src/api/endpoints.js must exist"
    )


def test_frontend_use_market_data_composable_exists():
    composable = os.path.join(
        REPO_ROOT, "frontend", "vue-app", "src", "composables", "useMarketData.js"
    )
    assert os.path.isfile(composable), (
        "frontend/vue-app/src/composables/useMarketData.js must exist"
    )