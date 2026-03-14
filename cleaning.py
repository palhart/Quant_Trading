import pandas as pd
import numpy as np


def clean_futures(filepath, asset_name):

    # 1. Chargement
    df = pd.read_csv(filepath, parse_dates=["date"])

    # 2. Supprimer les mesures live_* (doublons temps réel)
    df = df[~df["measure"].str.startswith("live_")].copy()

    # 3. Garder uniquement OHLCV + open_interest
    df = df[df["measure"].isin(["open", "high", "low", "close", "volume", "open_interest"])]

    # 4. Pivot : (date, contract) → colonnes OHLCV
    pivot = df.pivot_table(
        index=["date", "contract"],
        columns="measure",
        values="value",
        aggfunc="first"
    ).reset_index()
    pivot.columns.name = None

    # S'assurer que toutes les colonnes existent
    for col in ["open", "high", "low", "close", "volume", "open_interest"]:
        if col not in pivot.columns:
            pivot[col] = np.nan

    # 5. Front Month : pour chaque date, garder le contrat avec le plus haut open_interest
    pivot = pivot.dropna(subset=["close"])

    front_rows = []
    for date, group in pivot.groupby("date"):
        group_sorted = group.sort_values("open_interest", ascending=False)
        front_rows.append(group_sorted.iloc[0])

    result = pd.DataFrame(front_rows).reset_index(drop=True)
    result = result.sort_values("date").reset_index(drop=True)
    result["asset"] = asset_name


    price_cols = ["open", "high", "low", "close"]

    rollover_indices = result.index[
        result["contract"] != result["contract"].shift(1)
    ].tolist()

    # Parcourir du plus récent au plus ancien pour cumuler les ratios correctement
    for idx in reversed(rollover_indices):
        if idx == 0:
            continue

        price_before = result.loc[idx - 1, "close"]
        price_after  = result.loc[idx,     "close"]

        if price_before == 0 or pd.isna(price_before) or pd.isna(price_after):
            continue

        ratio = price_after / price_before
        result.loc[:idx - 1, price_cols] = result.loc[:idx - 1, price_cols] * ratio

    # 7. Colonnes finales
    cols = ["date", "asset", "contract", "open", "high", "low", "close", "volume", "open_interest"]
    return result[[c for c in cols if c in result.columns]]


def load_all_clean(files: dict) -> dict:
    """
    Charge et nettoie tous les assets.

    Retourne
    --------
    dict : {"KC": DataFrame, "CC": DataFrame, ...}
    """
    data = {}
    for asset, path in files.items():
        print(f"Cleaning {asset}...")
        data[asset] = clean_futures(path, asset)
        df = data[asset]
        print(f"  {len(df)} jours | {df['date'].min().date()} → {df['date'].max().date()}")
        print(f"  Contrats utilisés : {df['contract'].nunique()}")
        print()
    return data