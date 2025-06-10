# MCP-kis: My Capital Planner for KIS API

This project provides a basic framework to interact with the Korea Investment & Securities (KIS) API for trading. It is based on the official `Sample01` provided by KIS.

## Features

-   Configuration of API keys and account details via `kis_devlp.yaml`.
-   Selection between mock (paper) trading and real trading environments through `kis_devlp.yaml`.
-   Basic examples for fetching account balance and stock prices.
-   Designed to run in a Python virtual environment.

## Setup

1.  **Clone the repository (if you haven't already).**

2.  **Navigate to the `MCP-kis` directory:**
    ```bash
    cd MCP-kis
    ```

3.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure your API credentials:**
    -   Open `MCP-kis/kis_devlp.yaml`.
    -   Set the `trading_mode` to `"mock"` for paper trading or `"real"` for live trading.
    -   Fill in your API keys and secrets:
        -   For real trading: `my_app`, `my_sec`.
        -   For mock trading: `paper_app`, `paper_sec`.
    -   Fill in your account numbers:
        -   For real trading: `my_acct_stock` (for stocks), `my_acct_future` (for futures).
        -   For mock trading: `my_paper_stock`, `my_paper_future`.
    -   Set `my_prod` to your default product code (e.g., "01" for domestic stocks).

## Usage

1.  **Ensure your virtual environment is activated.**

2.  **Run the main script:**
    ```bash
    python main.py
    ```
    The script will authenticate using the details in `kis_devlp.yaml` and then execute the example API calls (fetching balance and a sample stock price).

3.  **Customize `main.py`** to implement your specific trading strategies or data analysis logic.

## Disclaimer

-   This is a sample application. Use it at your own risk.
-   Ensure you understand the KIS API documentation and terms of service.
-   The developers of this tool are not responsible for any financial losses incurred.
