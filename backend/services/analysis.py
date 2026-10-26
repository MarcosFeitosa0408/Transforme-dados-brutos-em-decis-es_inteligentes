import re
import unicodedata

import pandas as pd


CALENDAR_COLUMNS = {
    "ano",
    "mes",
    "mês",
    "dia",
}

BUSINESS_COLUMN_ALIASES = {
    "receita": (
        "receita",
        "faturamento",
        "valor_venda",
        "valor_vendas",
        "total_vendas",
        "vendas",
        "revenue",
        "sales",
    ),
    "custo": (
        "custo",
        "custos",
        "custo_total",
        "valor_custo",
        "cost",
        "costs",
    ),
    "lucro": (
        "lucro",
        "lucro_total",
        "resultado",
        "profit",
    ),
    "margem_percentual": (
        "margem_percentual",
        "margem",
        "margem_lucro",
        "margem_de_lucro",
        "profit_margin",
        "margin",
    ),
    "quantidade": (
        "quantidade",
        "qtd",
        "qtde",
        "unidades",
        "quantity",
        "units",
    ),
}

def normalize_column_name(column_name: str) -> str:
    """
    Padroniza nomes de colunas para facilitar a identificação automática.
    """

    name = str(column_name).strip().lower()

    name = unicodedata.normalize("NFKD", name)
    name = "".join(
        character
        for character in name
        if not unicodedata.combining(character)
    )

    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")

    return name


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
        if normalize_column_name(column) not in CALENDAR_COLUMNS
    ]

    calendar_columns = [
        column
        for column in numeric_columns
        if normalize_column_name(column) in CALENDAR_COLUMNS
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
            }

        if (
            normalize_column_name(column)
            not in BUSINESS_COLUMN_ALIASES["margem_percentual"]
        ):
            numeric_statistics[column]["sum"] = round(
                    float(series.sum()), 2
         )  

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
        normalize_column_name(column): column
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

    # Validação da consistência financeira
    financial_consistency = None

    required_columns = ("receita", "custo", "lucro")

    if all(
        name in detected_business_columns
        for name in required_columns
    ):
        revenue_col = detected_business_columns["receita"]
        cost_col = detected_business_columns["custo"]
        profit_col = detected_business_columns["lucro"]

        columns = [revenue_col, cost_col, profit_col]

        if all(
            pd.api.types.is_numeric_dtype(df[col])
            for col in columns
        ):
            valid_rows = df[columns].dropna()

            differences = (
                valid_rows[revenue_col]
                - valid_rows[cost_col]
                - valid_rows[profit_col]
            )

            inconsistent_mask = differences.abs().round(2) > 0

            inconsistent_records = valid_rows.loc[inconsistent_mask]

            inconsistent_details = []

            for row_index, row in inconsistent_records.iterrows():
                revenue = float(row[revenue_col])
                cost = float(row[cost_col])
                reported_profit = float(row[profit_col])
                calculated_profit = revenue - cost

                inconsistent_details.append({
                    "row_number": int(row_index) + 1,
                    "revenue": round(revenue, 2),
                    "cost": round(cost, 2),
                    "reported_profit": round(reported_profit, 2),
                    "calculated_profit": round(calculated_profit, 2),
                    "difference": round(
                        calculated_profit - reported_profit, 2
                    ),
                })

            inconsistent_rows = int(
                inconsistent_mask.sum()
            )

            financial_consistency = {
                "checked_rows": int(len(valid_rows)),
                "inconsistent_rows": inconsistent_rows,
                "inconsistent_details": inconsistent_details,
            }
    
    # Identificação de valores financeiros que merecem revisão
    financial_value_alerts = {}

    for business_name in ("receita", "custo", "lucro"):
        column = detected_business_columns.get(business_name)

        if column is None:
            continue

        series = df[column]

        if not pd.api.types.is_numeric_dtype(series):
            continue

        financial_value_alerts[business_name] = {
            "column": column,
            "negative_rows": int((series < 0).sum()),
            "zero_rows": int((series == 0).sum()),
            "missing_rows": int(series.isna().sum()),
        }
    revenue_by_category = []

    if (
        "receita" in detected_business_columns
        and "categoria" in normalized_columns
    ):
        revenue_column = detected_business_columns["receita"]
        category_column = normalized_columns["categoria"]

        if pd.api.types.is_numeric_dtype(df[revenue_column]):
            grouped = (
                df.groupby(category_column)[revenue_column]
                .sum()
                .sort_values(ascending=False)
            )

            revenue_by_category = [
                {
                    "category": str(category),
                    "revenue": round(float(total), 2),
                }
                for category, total in grouped.items()
            ]

                # Agrupamento da receita por ano e mês
    revenue_by_month = []

    if (
        "receita" in detected_business_columns
        and "ano" in normalized_columns
        and "mes" in normalized_columns
    ):
        revenue_column = detected_business_columns["receita"]
        year_column = normalized_columns["ano"]
        month_column = normalized_columns["mes"]

        if (
            pd.api.types.is_numeric_dtype(df[revenue_column])
            and pd.api.types.is_numeric_dtype(df[year_column])
            and pd.api.types.is_numeric_dtype(df[month_column])
        ):
            grouped_monthly = (
                df.groupby([year_column, month_column])[revenue_column]
                .sum()
                .sort_index()
            )

            revenue_by_month = [
                {
                    "year": int(year),
                    "month": int(month),
                    "revenue": round(float(total), 2),
                }
                for (year, month), total in grouped_monthly.items()
            ]

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

    calendar_summary = {}

    for column in calendar_columns:
        series = df[column].dropna()

        if not series.empty:
            calendar_summary[column] = {
                "minimum": int(series.min()),
                "maximum": int(series.max()),
                "unique_values": int(series.nunique()),
            }

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
        "calendar_summary": calendar_summary,
        "numeric_statistics": numeric_statistics,
        "revenue_by_category": revenue_by_category,
        "revenue_by_month": revenue_by_month,
        "financial_consistency": financial_consistency,
        "financial_value_alerts": financial_value_alerts,
        "insights": insights,
    }