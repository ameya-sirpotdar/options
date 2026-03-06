import os
import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


EXPECTED_PATHS = [
    "backend/api/__init__.py",
    "backend/agents/__init__.py",
    "backend/services/__init__.py",
    "backend/models/__init__.py",
    "backend/requirements.txt",
    "frontend/vue-app/.gitkeep",
    "infra/bicep/main.bicep",
    "infra/bicep/main.bicepparam.example",
    "infra/bicep/modules/aks.bicep",
    "infra/bicep/modules/storage.bicep",
    "infra/README.md",
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


def test_infra_terraform_directory_does_not_exist():
    terraform_dir = os.path.join(REPO_ROOT, "infra", "terraform")
    assert not os.path.exists(terraform_dir), (
        "infra/terraform/ directory must not exist; legacy Terraform placeholder has been removed"
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