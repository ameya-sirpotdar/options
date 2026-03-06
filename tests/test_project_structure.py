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
    "infra/terraform/.gitkeep",
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


def test_infra_terraform_directory_exists():
    terraform_dir = os.path.join(REPO_ROOT, "infra", "terraform")
    assert os.path.isdir(terraform_dir), (
        "infra/terraform/ directory must exist"
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