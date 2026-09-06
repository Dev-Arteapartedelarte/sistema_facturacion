.PHONY: help install dev migrate test shell superuser format lint type-check check run clean

help:
	@echo "Comandos disponibles:"
	@echo "  install        Instalar dependencias de producción"
	@echo "  dev            Instalar todas las dependencias (producción + desarrollo)"
	@echo "  migrate        Ejecutar migraciones de Django"
	@echo "  makemigrations Crear migraciones de Django"
	@echo "  test           Ejecutar pruebas con pytest"
	@echo "  shell          Abrir shell de Django"
	@echo "  superuser      Crear superusuario"
	@echo "  format         Formatear código con Ruff"
	@echo "  lint           Lint con Ruff"
	@echo "  type-check     Type checking con mypy"
	@echo "  check          Ejecutar todos los quality gates"
	@echo "  run            Ejecutar servidor de desarrollo"
	@echo "  clean          Limpiar archivos temporales"

install:
	uv sync

dev:
	uv sync --group dev

migrate:
	uv run python manage.py migrate

makemigrations:
	uv run python manage.py makemigrations

test:
	uv run pytest

test-cov:
	uv run pytest --cov=. --cov-report=html --cov-report=term --cov-fail-under=80

shell:
	uv run python manage.py shell

superuser:
	uv run python manage.py createsuperuser

format:
	uv run ruff check --fix .
	uv run ruff format .

lint:
	uv run ruff check .

type-check:
	uv run mypy .

check:
	@echo "🔍 Running linter..."
	uv run ruff check .
	@echo ""
	@echo "🔍 Running type checker..."
	uv run mypy .
	@echo ""
	@echo "🔍 Running tests..."
	uv run pytest --cov=. --cov-report=term --cov-fail-under=80
	@echo ""
	@echo "✅ All quality gates passed!"

run:
	uv run python manage.py runserver

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true
