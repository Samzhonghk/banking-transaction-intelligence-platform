import sys
from pathlib import Path
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


def test_main_runs_pipeline_and_disposes_engine(
    monkeypatch,
    capsys,
) -> None:
    """The application entry point should resolve a source and run the pipeline."""
    engine = MagicMock(spec=Engine)
    connection = MagicMock(spec=Connection)
    engine.connect.return_value.__enter__.return_value = connection
    connection.execute.return_value.scalar_one_or_none.return_value = 37

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
