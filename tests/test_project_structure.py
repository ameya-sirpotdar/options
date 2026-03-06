import os
import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


EXPECTED_PATHS = [
    "backend/__init__.py" if False else "backend/api/__init__.py",
    "backend/agents/__init__.py",
    "backend/services/__init__.py",
    "backend/models/__init__.py",
    "backend/requirements.txt",
    "frontend/vue-app/.gitkeep",
    "tests/test_project_structure.py",
    "infra/bicep/main.bicep",
    "infra/bicep/modules/aks.bicep",
    "infra/bicep/modules/storage.bicep",
    "infra/bicep/main.bicepparam.example",
    "infra/bicep/.gitignore",
    "infra/README.md",
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


def test_bicep_files_exist():
    bicep_files = [
        os.path.join(REPO_ROOT, "infra", "bicep", "main.bicep"),
        os.path.join(REPO_ROOT, "infra", "bicep", "modules", "aks.bicep"),
        os.path.join(REPO_ROOT, "infra", "bicep", "modules", "storage.bicep"),
    ]
    for bicep_file in bicep_files:
        assert os.path.isfile(bicep_file), (
            f"Expected Bicep file does not exist: {os.path.relpath(bicep_file, REPO_ROOT)}"
        )


def test_infra_bicep_gitignore_exists():
    gitignore_file = os.path.join(REPO_ROOT, "infra", "bicep", ".gitignore")
    assert os.path.isfile(gitignore_file), (
        "infra/bicep/.gitignore must exist to protect sensitive parameter files"
    )


def test_legacy_terraform_placeholder_directory_removed():
    terraform_dir = os.path.join(REPO_ROOT, "infra", "terraform")
    assert not os.path.isdir(terraform_dir), (
        "infra/terraform/ legacy placeholder directory should have been removed in Story 1.3"
    )