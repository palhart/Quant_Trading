# 🌾 Quant Trading – Donchian Breakout Strategy

This project explores a systematic **trend-following strategy** applied to agricultural futures markets (**Coffee, Cocoa, Sugar, Cotton**). It includes a full pipeline from data cleaning (continuous futures construction) to backtesting and parameter optimization.

## 📈 Strategy Logic

The strategy uses **Donchian Channels** to identify breakouts:

1.  **Entry Rule**:
    *   **LONG** if `Close` > Highest **High** of the last `entry_window` days (Breakout Up).
    *   **SHORT** if `Close` < Lowest **Low** of the last `entry_window` days (Breakout Down).
2.  **Exit Rule**:
    *   Exit Long if `Close` < Lowest **Low** of the last `exit_window` days.
    *   Exit Short if `Close` > Highest **High** of the last `exit_window` days.
3.  **Portfolio**:
    *   Equal Weight allocation across the 4 assets.

## 📂 Project Structure

### 1. Data Processing (`cleaning.py`)
Raw futures data often consists of multiple expirations. We construct a **Continuous Series** by:
*   **Front Month Selection**: Selecting the contract with the highest *Open Interest* for each day.
*   **Back-Adjustment**: Using the **Ratio Method** at each rollover to eliminate price gaps between contracts, ensuring accurate technical signals.

### 2. Backtesting Engine (`backtesting.py`)
A vectorized backtest engine using `pandas`:
*   Signal generation without lookahead bias (`shift(1)`).
*   Transaction costs simulation.
*   Performance metrics: **Sharpe Ratio**, **Sortino**, **Max Drawdown**, **Win Rate**, **Calmar Ratio**.

### 3. Analysis Notebook (`python.ipynb`)
The main playground which:
*   Visualizes price series and rollover dates.
*   Analyzes Open Interest distribution.
*   Runs the strategy with base parameters (20/10).
*   **Grid Search Optimization**: Tests combinations of entry/exit windows to maximize the Sharpe Ratio.
*   Compares the **Base Strategy** vs **Optimized Strategy**.

---

## ⚠️ Data Requirement

**The dataset is not included in this repository.** You must provide your own futures data to run the backtest.

1.  Create a `data/` folder at the root of the project.
2.  Add your CSV files inside.
3.  Ensure the file paths match the dictionary defined in the **Notebook (Cell 3)**:
    ```python
    FILES = {
        "KC": "./data/KC.csv",
        "CC": "./data/CC.csv",
        "SB": "./data/SB.csv",
        "CT": "./data/CT.csv"
    }
    ```

## 🚀 Setup & Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### 1. Install `uv`
If you don't have it installed, see the [installation docs](https://docs.astral.sh/uv/getting-started/installation/).

**Linux / macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
*Make sure to add `~/.cargo/bin` to your `$PATH` if it's not already there.*

### 2. Install Dependencies
Navigate to the root of this repo and run:

```bash
uv sync
```
This will create a virtual environment in `.venv`.

### 3. Activate Environment
To activate the environment manually:

```bash
source .venv/bin/activate
```

### 💡 Tip: Auto-activation (zsh)
Add the following to your `~/.zshrc` to automatically activate Python envs whenever you `cd` into a directory with a `.venv` folder:

```bash
autoload -U add-zsh-hook
activate_if_env() {
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
}
add-zsh-hook chpwd activate_if_env
activate_if_env
```