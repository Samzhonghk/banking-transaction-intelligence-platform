FROM apache/airflow:3.3.0-python3.13

WORKDIR /opt/airflow/project

COPY --chown=airflow:root pyproject.toml README.md ./
COPY --chown=airflow:root src ./src
COPY --chown=airflow:root data ./data
COPY --chown=airflow:root warehouse ./warehouse
COPY --chown=airflow:root orchestration/airflow/dags /opt/airflow/dags

RUN python -m venv /opt/airflow/project-venv \
    && /opt/airflow/project-venv/bin/pip install --no-cache-dir \
        "/opt/airflow/project" \
        "dbt-postgres>=1.11,<1.12"
