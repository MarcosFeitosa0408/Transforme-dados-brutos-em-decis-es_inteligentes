import pandas as pd


CALENDAR_COLUMNS = {
    "ano",
    "mes",
    "mês",
    "dia",
}

BUSINESS_COLUMN_ALIASES = {
    "receita": {
        "receita",
        "faturamento",
        "valor_venda",
        "valor_vendas",
        "total_vendas",
        "vendas",
        "revenue",
        "sales",
    },
    "custo": {
        "custo",
        "custos",
        "custo_total",
        "valor_custo",
        "cost",
        "costs",
    },
    "lucro": {
        "lucro",
        "lucro_total",
        "resultado",
        "profit",
    },
    "margem_percentual": {
        "margem_percentual",
        "margem",
        "margem_lucro",
        "margem_de_lucro",
        "profit_margin",
        "margin",
    },
    "quantidade": {
        "quantidade",
        "qtd",
        "qtde",
        "unidades",
        "quantity",
        "units",
    },
}


def analyze_dataframe(df: pd.DataFrame) -> dict:
    """
    Analisa um DataFrame e retorna informações sobre
    estrutura, qualidade, estatísticas e insights dos dados.
    """

    total_rows = len(df)
    total_columns = len(df.columns)

    missing_by_column = {
        column: int(value)
        for column, value in df.isnull().sum().items()
    }

    total_missing = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    data_types = {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }

    total_cells = total_rows * total_columns

    if total_cells == 0:
        quality_score = 0.0
    else:
        missing_percentage = (total_missing / total_cells) * 100

        duplicate_percentage = (
            (duplicate_rows / total_rows) * 100
            if total_rows > 0
            else 0
        )

        quality_score = 100 - missing_percentage - duplicate_percentage
        quality_score = max(0, min(100, quality_score))

    # Identificação das colunas numéricas
    numeric_columns = df.select_dtypes(include="number").columns.tolist()

    # Separa métricas de campos numéricos de calendário
    metric_columns = [
        column
        for column in numeric_columns
        if column.lower() not in CALENDAR_COLUMNS
    ]

    calendar_columns = [
        column
        for column in numeric_columns
        if column.lower() in CALENDAR_COLUMNS
    ]

    # Estatísticas somente para métricas úteis
    numeric_statistics = {}

    for column in metric_columns:
        series = df[column].dropna()

        if not series.empty:
            numeric_statistics[column] = {
                "minimum": float(series.min()),
                "maximum": float(series.max()),
                "mean": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "sum": round(float(series.sum()), 2),
            }

    insights = []

    # Qualidade dos dados
    if total_missing == 0:
        insights.append("Não foram encontrados valores ausentes.")
    else:
        insights.append(
            f"Foram encontrados {total_missing} valores ausentes no conjunto de dados."
        )

    if duplicate_rows == 0:
        insights.append("Não foram encontradas linhas duplicadas.")
    else:
        insights.append(
            f"Foram encontradas {duplicate_rows} linhas duplicadas."
        )

    insights.append(
        f"Foram identificadas {len(metric_columns)} métricas numéricas para análise."
    )

    # Insights de negócio
    normalized_columns = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    detected_business_columns = {}

    for business_name, aliases in BUSINESS_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized_columns:
                detected_business_columns[business_name] = (
                    normalized_columns[alias]
                )
                break

    if "receita" in detected_business_columns:
        column = detected_business_columns["receita"]
        total_revenue = float(df[column].sum())

        insights.append(
            f"Receita total identificada: R$ {total_revenue:,.2f}."
        )

    if "custo" in detected_business_columns:
        column = detected_business_columns["custo"]
        total_cost = float(df[column].sum())

        insights.append(
            f"Custo total identificado: R$ {total_cost:,.2f}."
        )

    if "lucro" in detected_business_columns:
        column = detected_business_columns["lucro"]
        total_profit = float(df[column].sum())

        insights.append(
            f"Lucro total identificado: R$ {total_profit:,.2f}."
        )

    if "margem_percentual" in detected_business_columns:
        column = detected_business_columns["margem_percentual"]
        average_margin = float(df[column].mean())

        insights.append(
            f"Margem percentual média: {average_margin:.2f}%."
        )

    if quality_score >= 90:
        insights.append(
            "O conjunto apresenta alto índice de qualidade pelos critérios atuais."
        )
    elif quality_score >= 70:
        insights.append(
            "O conjunto apresenta qualidade moderada e merece revisão."
        )
    else:
        insights.append(
            "O conjunto apresenta problemas relevantes de qualidade."
        )

    return {
        "rows": total_rows,
        "columns": total_columns,
        "column_names": df.columns.tolist(),
        "data_types": data_types,
        "missing_values": {
            "total": total_missing,
            "by_column": missing_by_column,
        },
        "duplicate_rows": duplicate_rows,
        "quality_score": round(quality_score, 2),
        "numeric_columns": numeric_columns,
        "metric_columns": metric_columns,
        "calendar_columns": calendar_columns,
        "numeric_statistics": numeric_statistics,
        "insights": insights,
    }