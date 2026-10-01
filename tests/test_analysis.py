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


def test_business_column_aliases():
    df = pd.DataFrame(
        {
            "produto": ["A", "B", "C"],
            "faturamento": [1000.0, 2000.0, 3000.0],
            "cost": [400.0, 800.0, 1200.0],
            "profit": [600.0, 1200.0, 1800.0],
            "qtd": [10, 20, 30],
        }
    )

    result = analyze_dataframe(df)

    assert result["rows"] == 3

    assert any(
        "Receita total identificada: R$ 6,000.00."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "Custo total identificado: R$ 2,400.00."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "Lucro total identificado: R$ 3,600.00."
        in insight
        for insight in result["insights"]
    )


def test_percentage_metric_does_not_have_sum():
    df = pd.DataFrame(
        {
            "receita": [100.0, 200.0, 300.0],
            "margem_percentual": [60.0, 65.0, 70.0],
        }
    )

    result = analyze_dataframe(df)

    assert "sum" in result["numeric_statistics"]["receita"]
    assert "sum" not in result["numeric_statistics"]["margem_percentual"]

    assert result["numeric_statistics"]["receita"]["sum"] == 600.0
    assert result["numeric_statistics"]["margem_percentual"]["mean"] == 65.0


def test_normalizes_business_column_names():
    df = pd.DataFrame(
        {
            "Total Vendas": [1000.0, 2000.0, 3000.0],
            "CUSTO TOTAL": [400.0, 800.0, 1200.0],
            "Profit": [600.0, 1200.0, 1800.0],
            "Margem de Lucro": [60.0, 60.0, 60.0],
        }
    )

    result = analyze_dataframe(df)

    assert any(
        "Receita total identificada: R$ 6,000.00."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "Custo total identificado: R$ 2,400.00."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "Lucro total identificado: R$ 3,600.00."
        in insight
        for insight in result["insights"]
    )

    assert any(
        "Margem percentual média: 60.00%."
        in insight
        for insight in result["insights"]
    )

def test_normalizes_calendar_column_names():
    df = pd.DataFrame(
        {
            "ANO": [2025, 2025, 2025],
            "Mês": [1, 2, 3],
            "Dia": [10, 15, 20],
            "Receita": [100.0, 200.0, 300.0],
        }
    )

    result = analyze_dataframe(df)

    assert "ANO" in result["calendar_columns"]
    assert "Mês" in result["calendar_columns"]
    assert "Dia" in result["calendar_columns"]

    assert "ANO" not in result["metric_columns"]
    assert "Mês" not in result["metric_columns"]
    assert "Dia" not in result["metric_columns"]

    assert "Receita" in result["metric_columns"]

def test_profit_margin_alias_does_not_have_sum():
    df = pd.DataFrame(
        {
            "Receita": [100.0, 200.0, 300.0],
            "Margem de Lucro": [60.0, 65.0, 70.0],
        }
    )

    result = analyze_dataframe(df)

    assert "sum" in result["numeric_statistics"]["Receita"]
    assert "sum" not in result["numeric_statistics"]["Margem de Lucro"]

    assert result["numeric_statistics"]["Receita"]["sum"] == 600.0
    assert (
        result["numeric_statistics"]["Margem de Lucro"]["mean"]
        == 65.0
    )