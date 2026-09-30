from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.analysis import analyze_dataframe


client = TestClient(app)


def test_analyze_dataframe():
    df = pd.DataFrame(
        {
            "Produto": ["Notebook", "Mouse", "Mouse", None],
            "Vendas": [3500, 120, 120, 500],
            "Regiao": ["Sudeste", "Sul", "Sul", "Nordeste"],
        }
    )

    result = analyze_dataframe(df)

    assert result["rows"] == 4
    assert result["columns"] == 3
    assert result["missing_values"]["total"] == 1
    assert result["duplicate_rows"] == 1
    assert "Produto" in result["column_names"]
    assert 0 <= result["quality_score"] <= 100

    assert "Vendas" in result["numeric_statistics"]
    assert result["numeric_statistics"]["Vendas"]["minimum"] == 120.0
    assert result["numeric_statistics"]["Vendas"]["maximum"] == 3500.0
    assert len(result["insights"]) > 0

    assert "Vendas" in result["metric_columns"]
    assert result["calendar_columns"] == []

def test_upload_csv():
    csv_content = (
        "Produto,Vendas,Regiao\n"
        "Notebook,3500,Sudeste\n"
        "Mouse,120,Sul\n"
        "Mouse,120,Sul\n"
    )

    response = client.post(
        "/analyze",
        files={
            "file": (
                "teste.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "teste.csv"
    assert data["file_type"] == "csv"
    assert data["analysis"]["rows"] == 3
    assert data["analysis"]["columns"] == 3
    assert data["analysis"]["duplicate_rows"] == 1


def test_upload_xlsx():
    df = pd.DataFrame(
        {
            "Produto": ["Notebook", "Mouse", "Teclado"],
            "Vendas": [3500, 120, 250],
            "Regiao": ["Sudeste", "Sul", "Sudeste"],
        }
    )

    excel_file = BytesIO()

    df.to_excel(
        excel_file,
        index=False,
        engine="openpyxl",
    )

    excel_file.seek(0)

    response = client.post(
        "/analyze",
        files={
            "file": (
                "teste.xlsx",
                excel_file.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "teste.xlsx"
    assert data["file_type"] == "xlsx"
    assert data["analysis"]["rows"] == 3
    assert data["analysis"]["columns"] == 3


def test_calendar_columns_are_not_metrics():
    df = pd.DataFrame(
        {
            "ano": [2025, 2025, 2025],
            "mes": [1, 2, 3],
            "dia": [10, 15, 20],
            "receita": [100.0, 200.0, 300.0],
            "lucro": [40.0, 80.0, 120.0],
        }
    )

    result = analyze_dataframe(df)

    assert "ano" in result["calendar_columns"]
    assert "mes" in result["calendar_columns"]
    assert "dia" in result["calendar_columns"]

    assert "receita" in result["metric_columns"]
    assert "lucro" in result["metric_columns"]

    assert "ano" not in result["numeric_statistics"]
    assert "mes" not in result["numeric_statistics"]
    assert "dia" not in result["numeric_statistics"]

    assert "receita" in result["numeric_statistics"]
    assert "lucro" in result["numeric_statistics"]