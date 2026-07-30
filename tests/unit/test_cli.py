import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, sentinel

from sqlalchemy.engine import Connection, Engine

from banking_intelligence import cli


def test_build_parser_parses_csv_ingestion_arguments() -> None:
    """The CLI should expose the inputs required by the CSV pipeline."""
    args = cli.build_parser().parse_args(
        [
            "ingest-csv",
            "data/samples/demo_transactions.csv",
            "--source-name",
            "demo-csv",
            "--pipeline-name",
            "manual-demo",
        ]
    )

    assert args.command == "ingest-csv"
    assert args.file_path == Path("data/samples/demo_transactions.csv")
    assert args.source_name == "demo-csv"
    assert args.pipeline_name == "manual-demo"


def test_build_parser_parses_api_ingestion_arguments() -> None:
    """The CLI should expose the inputs required by the API pipeline."""
    args = cli.build_parser().parse_args(
        [
            "ingest-api",
            "--source-name",
            "partner-api",
            "--page-size",
            "250",
            "--pipeline-name",
            "partner-api-manual",
        ]
    )

    assert args.command == "ingest-api"
    assert args.source_name == "partner-api"
    assert args.page_size == 250
    assert args.pipeline_name == "partner-api-manual"


def test_main_runs_pipeline_and_disposes_engine(
    monkeypatch,
    capsys,
) -> None:
    """The application entry point should resolve a source and run the pipeline."""
    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.connect.return_value.__enter__.return_value = connection
    connection.execute.return_value.one_or_none.return_value = SimpleNamespace(
        id=37,
        base_url=None,
    )

    pipeline = Mock(return_value=91)
    monkeypatch.setattr(cli, "Settings", Mock(return_value=sentinel.settings))
    monkeypatch.setattr(
        cli,
        "create_database_engine",
        Mock(return_value=engine),
    )
    monkeypatch.setattr(cli, "run_csv_transaction_pipeline", pipeline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "banking-intelligence",
            "ingest-csv",
            "data/samples/demo_transactions.csv",
            "--source-name",
            "demo-csv",
            "--pipeline-name",
            "manual-demo",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    pipeline.assert_called_once_with(
        engine=engine,
        file_path=Path("data/samples/demo_transactions.csv"),
        source_system_id=37,
        pipeline_name="manual-demo",
    )
    engine.dispose.assert_called_once_with()
    assert "ETL run 91 completed successfully" in capsys.readouterr().out


def test_main_runs_authenticated_api_pipeline_and_closes_session(
    monkeypatch,
    capsys,
) -> None:
    """The API command should authenticate, run the pipeline, and clean up."""
    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.connect.return_value.__enter__.return_value = connection
    connection.execute.return_value.one_or_none.return_value = SimpleNamespace(
        id=52,
        base_url="https://partner.example/transactions",
    )

    token = Mock()
    token.get_secret_value.return_value = "test-api-token"
    settings = SimpleNamespace(transaction_api_token=token)
    session = MagicMock()
    session.headers = {}
    pipeline = Mock(return_value=92)

    monkeypatch.setattr(cli, "Settings", Mock(return_value=settings))
    monkeypatch.setattr(
        cli,
        "create_database_engine",
        Mock(return_value=engine),
    )
    monkeypatch.setattr(
        cli,
        "build_retry_session",
        Mock(return_value=session),
    )
    monkeypatch.setattr(cli, "run_api_transaction_pipeline", pipeline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "banking-intelligence",
            "ingest-api",
            "--source-name",
            "partner-api",
            "--page-size",
            "250",
            "--pipeline-name",
            "partner-api-manual",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert session.headers["Authorization"] == "Bearer test-api-token"
    pipeline.assert_called_once_with(
        engine=engine,
        url="https://partner.example/transactions",
        source_system_id=52,
        session=session,
        page_size=250,
        pipeline_name="partner-api-manual",
    )
    session.close.assert_called_once_with()
    engine.dispose.assert_called_once_with()
    assert "ETL run 92 completed successfully" in capsys.readouterr().out
