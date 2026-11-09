"""Utilitários de serialização: tudo que sai da fachada precisa ser JSON puro."""
import math
from datetime import date, datetime

import numpy as np
import pandas as pd


def fmt_data(ts) -> str:
    """'AAAA-MM-DD', o formato de intercâmbio. A apresentação mostra DD/MM/AAAA."""
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def para_pontos(serie: pd.Series, max_pontos: int = 500) -> list[dict]:
    """Série -> [{x: 'AAAA-MM-DD', y: float}], reamostrada por passo fixo (mantém o último ponto).
    Mesmo formato do `pontos_grafico` do Portal FinQuant."""
    s = serie.dropna()
    if len(s) == 0:
        return []
    passo = max(1, math.ceil(len(s) / max_pontos))
    idx = list(range(0, len(s), passo))
    if idx[-1] != len(s) - 1:
        idx.append(len(s) - 1)
    return [{"x": fmt_data(s.index[i]), "y": float(s.iloc[i])} for i in idx]


def json_seguro(obj):
    """Converte recursivamente numpy/pandas/NaN para tipos JSON (NaN/inf -> None)."""
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return fmt_data(obj)
    if isinstance(obj, pd.Series):
        return para_pontos(obj)
    if isinstance(obj, pd.DataFrame):
        df = obj.reset_index() if not isinstance(obj.index, pd.RangeIndex) else obj
        return [json_seguro(r) for r in df.to_dict(orient="records")]
    if isinstance(obj, np.ndarray):
        return [json_seguro(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {str(k): json_seguro(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [json_seguro(x) for x in obj]
    return str(obj)
