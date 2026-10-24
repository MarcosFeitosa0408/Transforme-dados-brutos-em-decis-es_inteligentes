const API_URL = "http://127.0.0.1:8001";

const fileInput = document.getElementById("fileInput");
const selectFileButton = document.getElementById("selectFileButton");
const analyzeButton = document.getElementById("analyzeButton");
const selectedFile = document.getElementById("selectedFile");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");
const results = document.getElementById("results");

const resultFilename = document.getElementById("resultFilename");
const exportAnalysisBtn = document.getElementById("exportAnalysisBtn");
const rowsValue = document.getElementById("rowsValue");
const columnsValue = document.getElementById("columnsValue");
const missingValue = document.getElementById("missingValue");
const duplicatesValue = document.getElementById("duplicatesValue");
const qualityValue = document.getElementById("qualityValue");

const insightsList = document.getElementById("insightsList");
const metricsList = document.getElementById("metricsList");
const statisticsTable = document.getElementById("statisticsTable");

let currentFile = null;
let currentAnalysisData = null;


/*
|--------------------------------------------------------------------------
| Seleção do arquivo
|--------------------------------------------------------------------------
*/

selectFileButton.addEventListener("click", () => {
    fileInput.click();
});


fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];

    clearError();
    results.classList.add("hidden");

    if (!file) {
        currentFile = null;
        selectedFile.textContent = "Nenhum arquivo selecionado";
        analyzeButton.disabled = true;
        return;
    }

    const filename = file.name.toLowerCase();

    const validFile =
        filename.endsWith(".csv") ||
        filename.endsWith(".xlsx");

    if (!validFile) {
        currentFile = null;
        fileInput.value = "";

        selectedFile.textContent = "Nenhum arquivo selecionado";
        analyzeButton.disabled = true;

        showError(
            "Formato não suportado. Selecione um arquivo CSV ou Excel (.xlsx)."
        );

        return;
    }

    currentFile = file;

    selectedFile.textContent =
        `${file.name} • ${formatFileSize(file.size)}`;

    analyzeButton.disabled = false;
});


/*
|--------------------------------------------------------------------------
| Envio para a API
|--------------------------------------------------------------------------
*/

analyzeButton.addEventListener("click", async () => {
    if (!currentFile) {
        showError("Selecione um arquivo antes de iniciar a análise.");
        return;
    }

        clearError();

    currentAnalysisData = null;
    exportAnalysisBtn.disabled = true;

    loading.classList.remove("hidden");
    results.classList.add("hidden");

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analisando...";

    const formData = new FormData();
    formData.append("file", currentFile);

    try {
        const response = await fetch(
            `${API_URL}/analyze`,
            {
                method: "POST",
                body: formData,
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Não foi possível analisar o arquivo."
            );
        }

        renderResults(data);

    } catch (error) {
        showError(
            error.message ||
            "Não foi possível conectar ao servidor do DataPilot."
        );

    } finally {
        loading.classList.add("hidden");

        analyzeButton.disabled = false;
        analyzeButton.textContent = "Analisar dados";
    }
});


/*
|--------------------------------------------------------------------------
| Renderização dos resultados
|--------------------------------------------------------------------------
*/

function renderResults(data) {
    const analysis = data.analysis;

    resultFilename.textContent = data.filename;

    rowsValue.textContent =
        formatInteger(analysis.rows);

    columnsValue.textContent =
        formatInteger(analysis.columns);

    missingValue.textContent =
        formatInteger(analysis.missing_values.total);

    duplicatesValue.textContent =
        formatInteger(analysis.duplicate_rows);

    qualityValue.textContent =
        `${formatNumber(analysis.quality_score)}%`;

    renderInsights(analysis.insights);
    renderMetrics(analysis.metric_columns);
    renderCalendarColumns(
    analysis.calendar_columns,
    analysis.calendar_summary);
    renderStatistics(analysis.numeric_statistics);
    renderMetricsChart(analysis.numeric_statistics);
    renderCategoryChart(analysis.revenue_by_category);
    renderMonthlyChart(analysis.revenue_by_month);
    
    currentAnalysisData = data;
    exportAnalysisBtn.disabled = false;

    results.classList.remove("hidden");

    results.scrollIntoView({
        behavior: "smooth",
        block: "start",

    });
}


function renderInsights(insights) {
    insightsList.innerHTML = "";

    insights.forEach((insight) => {
        const item = document.createElement("li");

        item.textContent = formatBrazilianInsight(insight);

        insightsList.appendChild(item);
    });
}


function renderMetrics(metrics) {
    metricsList.innerHTML = "";

    if (!metrics || metrics.length === 0) {
        metricsList.textContent =
            "Nenhuma métrica numérica identificada.";

        return;
    }

    metrics.forEach((metric) => {
        const tag = document.createElement("span");

        tag.className = "metric-tag";
        tag.textContent = metric;

        metricsList.appendChild(tag);
    });
}


function renderCalendarColumns(columns, summary) {
    const calendarList = document.getElementById("calendarList");

    calendarList.innerHTML = "";

    if (!columns || columns.length === 0) {
        calendarList.textContent =
            "Nenhuma coluna de calendário identificada.";

        return;
    }

    const labels = {
        ano: ["Ano", "Anos"],
        mes: ["Mês", "Meses"],
        dia: ["Dia", "Dias"],
    };

    columns.forEach((column) => {
        const data = summary?.[column];
        const tag = document.createElement("span");

        tag.className = "metric-tag";

        if (data) {
            const normalizedColumn = column
                .toLowerCase()
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "");

            const labelOptions = labels[normalizedColumn];

            if (labelOptions) {
                const isSingleValue =
                    data.minimum === data.maximum;

                const label = isSingleValue
                    ? labelOptions[0]
                    : labelOptions[1];

                tag.textContent = isSingleValue
                    ? `${label}: ${data.minimum}`
                    : `${label}: ${data.minimum} a ${data.maximum}`;
            } else {
                tag.textContent =
                    `${column}: ${data.minimum} a ${data.maximum}`;
            }
        } else {
            tag.textContent = column;
        }

        calendarList.appendChild(tag);
    });
}


function renderStatistics(statistics) {
    statisticsTable.innerHTML = "";

    const entries = Object.entries(statistics);

    if (entries.length === 0) {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td colspan="6">
                Nenhuma estatística numérica disponível.
            </td>
        `;

        statisticsTable.appendChild(row);

        return;
    }

    entries.forEach(([metric, values]) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${escapeHtml(metric)}</td>
            <td>${formatNumber(values.minimum)}</td>
            <td>${formatNumber(values.maximum)}</td>
            <td>${formatNumber(values.mean)}</td>
            <td>${formatNumber(values.median)}</td>
            <td>${formatNumber(values.sum)}</td>
        `;

        statisticsTable.appendChild(row);
    });
}


/*
|--------------------------------------------------------------------------
| Formatação
|--------------------------------------------------------------------------
*/

function formatInteger(value) {
    return new Intl.NumberFormat(
        "pt-BR",
        {
            maximumFractionDigits: 0,
        }
    ).format(value);
}


function formatNumber(value) {
    if (value === null || value === undefined) {
        return "-";
    }

    return new Intl.NumberFormat(
        "pt-BR",
        {
            maximumFractionDigits: 2,
        }
    ).format(value);
}


function formatFileSize(bytes) {
    if (bytes < 1024) {
        return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}


/*
|--------------------------------------------------------------------------
| Converte valores monetários dos insights para pt-BR
|--------------------------------------------------------------------------
*/

function formatBrazilianInsight(text) {
    return text.replace(
        /R\$\s([\d,]+\.\d{2})/g,
        (_, value) => {
            const numericValue =
                Number(value.replace(/,/g, ""));

            return new Intl.NumberFormat(
                "pt-BR",
                {
                    style: "currency",
                    currency: "BRL",
                }
            ).format(numericValue);
        }
    );
}


/*
|--------------------------------------------------------------------------
| Segurança básica para conteúdo inserido na tabela
|--------------------------------------------------------------------------
*/

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/*
|--------------------------------------------------------------------------
| Mensagens
|--------------------------------------------------------------------------
*/

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
}


function clearError() {
    errorMessage.textContent = "";
    errorMessage.classList.add("hidden");
}

function renderMetricsChart(statistics) {
    const canvas = document.getElementById("metricsChart");
    const status = document.getElementById("chartStatus");

    if (!canvas || !status) return;

    if (typeof Chart === "undefined") {
        status.textContent = "Não foi possível carregar a biblioteca de gráficos.";
        return;
    }

    const indicators = {
        Receita: ["receita", "faturamento", "valor_venda", "valor_vendas", "total_vendas", "vendas", "revenue", "sales"],
        Custo: ["custo", "custos", "custo_total", "valor_custo", "cost", "costs"],
        Lucro: ["lucro", "lucro_total", "resultado", "profit"]
    };

    const normalized = Object.entries(statistics || {}).map(([name, data]) => ({
        name: name.normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, "_"),
        data
    }));

    const labels = [];
    const values = [];

    for (const [label, aliases] of Object.entries(indicators)) {
        const match = aliases
            .map(alias => normalized.find(item => item.name === alias))
            .find(item => item && Number.isFinite(item.data.sum));

        if (match) {
            labels.push(label);
            values.push(match.data.sum);
        }
    }

    const previousChart = Chart.getChart(canvas);

    if (previousChart) {
        previousChart.destroy();
    }

    if (labels.length === 0) {
        status.textContent = "Nenhum indicador financeiro identificado para o gráfico.";
        return;
    }

    status.textContent = "Comparativo de indicadores financeiros";

    new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Total (R$)",
                data: values
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}


function renderCategoryChart(categories) {
    const canvas = document.getElementById("categoryChart");
    const status = document.getElementById("categoryChartStatus");

    if (!canvas || !status) return;

    if (typeof Chart === "undefined") {
        status.textContent =
            "Não foi possível carregar a biblioteca de gráficos.";
        return;
    }

    const previousChart = Chart.getChart(canvas);

    if (previousChart) {
        previousChart.destroy();
    }

    if (!Array.isArray(categories) || categories.length === 0) {
        status.textContent =
            "Nenhum dado de receita por categoria foi identificado.";
        return;
    }

    const labels = categories.map(item => item.category);
    const values = categories.map(item => item.revenue);

    status.textContent = "Comparativo de receita por categoria";

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Receita (R$)",
                data: values,
                backgroundColor: "rgba(45, 185, 225, 0.7)"
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}


function renderMonthlyChart(monthlyData) {
    const canvas = document.getElementById("monthlyChart");
    const status = document.getElementById("monthlyChartStatus");

    if (!canvas || !status) return;

    if (typeof Chart === "undefined") {
        status.textContent =
            "Não foi possível carregar a biblioteca de gráficos.";
        return;
    }

    const previousChart = Chart.getChart(canvas);

    if (previousChart) {
        previousChart.destroy();
    }

    if (!Array.isArray(monthlyData) || monthlyData.length === 0) {
        status.textContent =
            "Nenhum dado de receita mensal foi identificado.";
        return;
    }

    const monthNames = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ];

    const validData = monthlyData.filter(item =>
        Number.isInteger(item.year) &&
        Number.isInteger(item.month) &&
        item.month >= 1 &&
        item.month <= 12 &&
        Number.isFinite(item.revenue)
    );

    if (validData.length === 0) {
        status.textContent =
            "Nenhum período mensal válido foi identificado.";
        return;
    }

    validData.sort((a, b) =>
        a.year - b.year || a.month - b.month
    );

    const labels = validData.map(item =>
        `${monthNames[item.month - 1]}/${item.year}`
    );

    const values = validData.map(item => item.revenue);

    status.textContent = "Comparativo da receita ao longo dos meses";

    new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Receita (R$)",
                data: values,
                borderColor: "rgb(45, 185, 225)",
                backgroundColor: "rgba(45, 185, 225, 0.15)",
                borderWidth: 3,
                tension: 0.2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}


exportAnalysisBtn.addEventListener("click", () => {
    if (!currentAnalysisData) {
        return;
    }

    const { filename, analysis } = currentAnalysisData;

    const lines = [
        "DATAPILOT - RELATORIO DE ANALISE",
        "================================",
        "",
        `Arquivo analisado: ${filename}`,
        `Linhas: ${formatInteger(analysis.rows)}`,
        `Colunas: ${formatInteger(analysis.columns)}`,
        `Valores ausentes: ${formatInteger(analysis.missing_values.total)}`,
        `Linhas duplicadas: ${formatInteger(analysis.duplicate_rows)}`,
        `Qualidade dos dados: ${formatNumber(analysis.quality_score)}%`,
        "",
        "INSIGHTS AUTOMATICOS",
        "--------------------",
        ...(analysis.insights || []).map(
            insight => `- ${formatBrazilianInsight(insight)}`
        ),
        "",
        "ESTATISTICAS NUMERICAS",
        "----------------------",
        ...Object.entries(analysis.numeric_statistics || {}).map(
            ([name, values]) =>
                `${name}: minimo ${formatNumber(values.minimum)}, ` +
                `maximo ${formatNumber(values.maximum)}, ` +
                `media ${formatNumber(values.mean)}, ` +
                `mediana ${formatNumber(values.median)}, ` +
                `total ${"sum" in values ? formatNumber(values.sum) : "N/A"}`
        ),
        "",
        "RECEITA POR CATEGORIA",
        "---------------------",
        ...(analysis.revenue_by_category || []).map(
            item => `${item.category}: R$ ${formatNumber(item.revenue)}`
        ),
        "",
        "EVOLUCAO MENSAL DA RECEITA",
        "-------------------------",
        ...(analysis.revenue_by_month || []).map(
            item =>
                `${String(item.month).padStart(2, "0")}/${item.year}: ` +
                `R$ ${formatNumber(item.revenue)}`
        )
    ];

    const blob = new Blob(
        ["\uFEFF", lines.join("\r\n")],
        { type: "text/plain;charset=utf-8" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "DataPilot_Relatorio_Analise.txt";

    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
});