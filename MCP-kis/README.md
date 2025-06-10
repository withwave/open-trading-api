# MCP-kis: API Server for KIS Trading

This project provides an API server to interact with the Korea Investment & Securities (KIS) API for trading.
It is based on the official `Sample01` provided by KIS and uses FastAPI to expose a RESTful API.
This server is designed to be consumed by client applications, such as the Claude AI desktop application.

## Features

-   FastAPI web server exposing KIS functionalities.
-   Endpoints for account balance, positions, market prices, and order management.
-   Configuration of API keys and account details via `kis_devlp.yaml`.
-   Selection between mock (paper) trading and real trading environments through `kis_devlp.yaml`.
-   Automatic interactive API documentation via OpenAPI (Swagger UI at `/docs`).
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
    # This now includes fastapi and uvicorn.
    ```

5.  **Configure your API credentials in `kis_devlp.yaml`:**
    -   Open `MCP-kis/kis_devlp.yaml`.
    -   Set the `trading_mode` to `"mock"` (for paper trading) or `"real"` (for live trading).
    -   Fill in your API keys and secrets for both modes.
    -   Fill in your account numbers for both modes.
    -   Set `my_prod` to your default product code (e.g., "01" for domestic stocks).

## Running the Server

1.  **Ensure your virtual environment is activated and you are in the `MCP-kis` directory.**

2.  **Start the FastAPI server:**
    You can run the server directly using:
    ```bash
    python server.py
    ```
    Alternatively, for development with auto-reload, run from the parent directory of `MCP-kis` (if your project root contains `MCP-kis` as a subdirectory):
    ```bash
    uvicorn MCP-kis.server:app --reload --host 0.0.0.0 --port 8000
    ```
    Or, if you are already inside the `MCP-kis` directory:
    ```bash
    uvicorn server:app --reload --host 0.0.0.0 --port 8000
    ```
    The server will typically be available at `http://localhost:8000`.

## API Usage

Once the server is running, you can interact with the API.
-   **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
-   **Alternative API Documentation (ReDoc):** `http://localhost:8000/redoc`

### API Overview
The API is versioned under `/api/v1/`. Key endpoint groups include:
-   `/api/v1/account/balance`: Get account balance.
-   `/api/v1/account/positions`: Get current stock holdings.
-   `/api/v1/market/price/{stock_code}`: Get price for a stock.
-   `/api/v1/orders/`: Place new orders, list existing orders.
-   `/api/v1/orders/{order_id}`: Get or cancel a specific order.

Refer to the interactive documentation at `/docs` for detailed request/response schemas and to try out the API.

## CLI Examples (Optional)

The file `MCP-kis/kis_cli_examples.py` (formerly `main.py`) contains the original command-line examples for direct KIS API interaction, similar to `Sample01`. This can be run for testing KIS API functions directly:
```bash
python kis_cli_examples.py
```
Ensure `kis_devlp.yaml` is configured before running these examples.

## Disclaimer

-   This is a sample application. Use it at your own risk.
-   Ensure you understand the KIS API documentation and terms of service.
-   The developers of this tool are not responsible for any financial losses incurred.

## Manual API Testing with cURL

Once the server is running, you can test the API endpoints using a tool like `curl`.
Replace `YOUR_STOCK_CODE` and `YOUR_ORDER_ID` with actual values.
For POST requests, ensure your `kis_devlp.yaml` is configured, especially for trading actions.

**Get Account Balance:**
```bash
curl -X GET "http://localhost:8000/api/v1/account/balance" -H "accept: application/json"
```

**Get Account Positions:**
```bash
curl -X GET "http://localhost:8000/api/v1/account/positions" -H "accept: application/json"
```

**Get Stock Price (e.g., for stock code 005930):**
```bash
curl -X GET "http://localhost:8000/api/v1/market/price/005930" -H "accept: application/json"
```

**Place a Limit Buy Order:**
(Ensure your KIS API is configured for mock or real trading and has funds/permissions)
```bash
curl -X POST "http://localhost:8000/api/v1/orders/" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
           "stock_code": "005930",
           "order_type": "buy",
           "quantity": 1,
           "price_type": "limit",
           "price": 50000
         }'
```
# Note the response from the above command, it will contain an `order_id` (ODNO)
# and `krx_fwdg_ord_orgno`. You'll need these for querying or cancelling this specific order.
# Let's say the ODNO was "0000123456" and KRX_FWDG_ORD_ORGNO was "06010".

**List Recent Orders:**
```bash
curl -X GET "http://localhost:8000/api/v1/orders/" -H "accept: application/json"
```

**List Orders for a Specific Stock (e.g., 005930):**
```bash
curl -X GET "http://localhost:8000/api/v1/orders/?stock_code=005930" -H "accept: application/json"
```

**Get Specific Order Details (replace 0000123456 with an actual order_id/ODNO from your system):**
```bash
curl -X GET "http://localhost:8000/api/v1/orders/0000123456" -H "accept: application/json"
```

**Cancel an Order (replace 0000123456 with ODNO and use corresponding KRX_FWDG_ORD_ORGNO):**
```bash
curl -X DELETE "http://localhost:8000/api/v1/orders/0000123456" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
           "ord_orgno": "06010"
         }'
# Add other fields to the JSON body if your CancelOrderRequest model requires them
# (e.g. rvse_cncl_dvsn_cd, ord_qty, ord_unpr, qty_all_ord_yn - though many have defaults).
```
