
import pandas as pd
import numpy as np


# ── 1. Signal Donchian ─────────────────────────────────────────────────────────

def compute_signals(df: pd.DataFrame,
                    entry_window: int = 20,
                    exit_window:  int = 10) -> pd.DataFrame:
    
    df = df.copy().sort_values("date").reset_index(drop=True)

    # Canaux Donchian (shift(1) pour éviter le lookahead bias)
    df["upper"]       = df["high"].rolling(entry_window).max().shift(1)
    df["lower"]       = df["low"].rolling(entry_window).min().shift(1)
    df["exit_upper"]  = df["high"].rolling(exit_window).max().shift(1)
    df["exit_lower"]  = df["low"].rolling(exit_window).min().shift(1)

    # Calcul du signal jour par jour
    signal   = np.zeros(len(df))
    position = 0  # position courante : +1, -1, ou 0

    for i in range(len(df)):
        if pd.isna(df.loc[i, "upper"]):
            signal[i] = 0
            continue

        close = df.loc[i, "close"]

        if position == 0:
            if close > df.loc[i, "upper"]:
                position = 1
            elif close < df.loc[i, "lower"]:
                position = -1

        elif position == 1:
            if close < df.loc[i, "exit_lower"]:
                position = 0
            elif close < df.loc[i, "lower"]:
                position = -1

        elif position == -1:
            if close > df.loc[i, "exit_upper"]:
                position = 0
            elif close > df.loc[i, "upper"]:
                position = 1

        signal[i] = position

    df["signal"] = signal
    return df


# ── 2. Backtest par asset ──────────────────────────────────────────────────────

def backtest_asset(df: pd.DataFrame,
                   entry_window:     int   = 20,
                   exit_window:      int   = 10,
                   transaction_cost: float = 0.001) -> pd.DataFrame:
    """
    Backteste la stratégie sur un seul asset indépendamment.
    Retourne un DataFrame avec les rendements nets journaliers.
    """
    sig = compute_signals(df, entry_window, exit_window)
    sig = sig.set_index("date")

    sig["daily_return"]    = sig["close"].pct_change()
    sig["strategy_return"] = sig["signal"].shift(1) * sig["daily_return"]
    sig["cost"]            = sig["signal"].diff().abs() * transaction_cost
    sig["net_return"]      = sig["strategy_return"] - sig["cost"]

    return sig


# ── 3. Backtest portfolio ──────────────────────────────────────────────────────

def run_backtest(data:             dict,
                 entry_window:     int   = 20,
                 exit_window:      int   = 10,
                 transaction_cost: float = 0.001,
                 initial_capital:  float = 100_000) -> dict:

    asset_results = {}
    asset_equity  = {}
    trades        = {}

    for asset, df in data.items():
        res = backtest_asset(df, entry_window, exit_window, transaction_cost)
        asset_results[asset] = res

        # Equity curve par asset (base 100)
        asset_equity[asset] = (1 + res["net_return"].dropna()).cumprod() * 100

        # Nombre de trades
        trades[asset] = int(res["signal"].diff().abs().gt(0).sum())

    # Portfolio = moyenne equal-weight des rendements de chaque asset
    returns_df        = pd.DataFrame({a: r["net_return"] for a, r in asset_results.items()})
    portfolio_returns = returns_df.mean(axis=1).dropna()
    equity_curve      = (1 + portfolio_returns).cumprod() * initial_capital

    return {
        "signals":      {a: r for a, r in asset_results.items()},
        "returns":      returns_df,
        "asset_equity": asset_equity,
        "portfolio":    portfolio_returns,
        "equity_curve": equity_curve,
        "trades":       pd.Series(trades, name="nb_trades"),
    }


# ── 4. Métriques de performance ────────────────────────────────────────────────

def compute_metrics(result: dict, freq: int = 252) -> pd.Series:
    
    r      = result["portfolio"].dropna()
    equity = result["equity_curve"].dropna()

    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    ann_return   = (1 + total_return) ** (freq / len(r)) - 1
    ann_vol      = r.std() * np.sqrt(freq)
    sharpe       = ann_return / ann_vol if ann_vol > 0 else np.nan

    rolling_max  = equity.cummax()
    drawdown     = (equity - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    calmar        = ann_return / abs(max_drawdown) if max_drawdown != 0 else np.nan
    down_vol      = r[r < 0].std() * np.sqrt(freq)
    sortino       = ann_return / down_vol if down_vol > 0 else np.nan
    win_rate      = (r > 0).sum() / len(r)
    gross_profit  = r[r > 0].sum()
    gross_loss    = abs(r[r < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.nan

    return pd.Series({
        "Période":             f"{equity.index.min().date()} → {equity.index.max().date()}",
        "Jours de trading":    len(r),
        "Capital initial ($)": f"{result['equity_curve'].iloc[0]:,.0f}",
        "Capital final ($)":   f"{equity.iloc[-1]:,.0f}",
        "Total Return (%)":    round(total_return * 100, 2),
        "Ann. Return (%)":     round(ann_return * 100, 2),
        "Ann. Volatility (%)": round(ann_vol * 100, 2),
        "Sharpe Ratio":        round(sharpe, 3),
        "Sortino Ratio":       round(sortino, 3),
        "Calmar Ratio":        round(calmar, 3),
        "Max Drawdown (%)":    round(max_drawdown * 100, 2),
        "Win Rate (%)":        round(win_rate * 100, 2),
        "Profit Factor":       round(profit_factor, 3),
        "Nb Trades Total":     int(result["trades"].sum()),
    })