import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def load_csv(file_path, encoding=None, sep=None, date_formats=None):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if encoding is None:
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'cp866', 'latin1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    f.read(1024)
                encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if encoding is None:
            raise ValueError("Could not detect file encoding")

    if sep is None:
        with open(file_path, 'r', encoding=encoding) as f:
            first_line = f.readline()
        if ',' in first_line and first_line.count(',') >= first_line.count(';'):
            sep = ','
        elif ';' in first_line:
            sep = ';'
        elif '\t' in first_line:
            sep = '\t'
        else:
            sep = ','

    df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

    metadata = {
        "file_name": file_path.name,
        "file_path": str(file_path.absolute()),
        "encoding": encoding,
        "separator": sep,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    return df, metadata


def clean_data(df):
    cleaning_log = []

    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()

    na_markers = ['', 'NA', 'N/A', 'NULL', 'null', 'Null', '-', '?', 'NaN', 'nan', 'None', 'none']
    df = df.replace(na_markers, pd.NA)
    cleaning_log.append("Standardised missing value markers to NA")

    df = df.replace([np.inf, -np.inf], pd.NA)
    cleaning_log.append("Replaced inf values with NA")

    return df, cleaning_log


def detect_column_types(df):
    types = {}
    for col in df.columns:
        non_na = df[col].dropna()
        if len(non_na) == 0:
            types[col] = "empty"
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            types[col] = "numeric"
            continue

        try:
            sample = non_na.astype(str).iloc[:100]
            parsed = pd.to_datetime(sample, format='mixed')
            if len(parsed.dropna()) / len(sample) > 0.7:
                types[col] = "datetime"
                continue
        except (ValueError, TypeError):
            pass

        if df[col].nunique() < min(30, len(df) * 0.05):
            types[col] = "categorical"
        else:
            types[col] = "text"

    return types
