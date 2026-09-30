from io import BytesIO

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.services.analysis import analyze_dataframe


app = FastAPI(
    title="DataPilot API",
    description="Transforme dados brutos em decisões inteligentes.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "DataPilot API está funcionando.",
        "status": "online",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze_file(file: UploadFile = File(...)):
    filename = file.filename or ""
    filename_lower = filename.lower()

    allowed_extensions = (".csv", ".xlsx")

    if not filename_lower.endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Envie um arquivo CSV ou Excel (.xlsx).",
        )

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="O arquivo está vazio.",
            )

        file_buffer = BytesIO(contents)

        if filename_lower.endswith(".csv"):
            dataframe = pd.read_csv(file_buffer)

        elif filename_lower.endswith(".xlsx"):
            dataframe = pd.read_excel(
                file_buffer,
                engine="openpyxl",
            )

        if dataframe.empty:
            raise HTTPException(
                status_code=400,
                detail="O arquivo não possui dados.",
            )

        analysis = analyze_dataframe(dataframe)

        return {
            "filename": filename,
            "file_type": "csv" if filename_lower.endswith(".csv") else "xlsx",
            "analysis": analysis,
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível analisar o arquivo: {error}",
        )