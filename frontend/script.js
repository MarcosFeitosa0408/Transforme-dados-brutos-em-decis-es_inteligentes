const API_URL = "http://127.0.0.1:8001";

const fileInput = document.getElementById("fileInput");
const selectFileButton = document.getElementById("selectFileButton");
const analyzeButton = document.getElementById("analyzeButton");
const selectedFile = document.getElementById("selectedFile");

const loading = document.getElementById("loading");
const errorMessage = document.getElementById("errorMessage");
const results = document.getElementById("results");

const resultFilename = document.getElementById("resultFilename");
const rowsValue = document.getElementById("rowsValue");
const columnsValue = document.getElementById("columnsValue");
const missingValue = document.getElementById("missingValue");
const duplicatesValue = document.getElementById("duplicatesValue");
const qualityValue = document.getElementById("qualityValue");

const insightsList = document.getElementById("insightsList");
const metricsList = document.getElementById("metricsList");
const statisticsTable = document.getElementById("statisticsTable");

let currentFile = null;


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