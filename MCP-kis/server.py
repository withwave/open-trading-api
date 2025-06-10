# MCP-kis/server.py
from fastapi import FastAPI
import uvicorn
import os
import sys

# Ensure the current directory is in sys.path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import KIS authentication module
import kis_auth as ka

app = FastAPI(
    title="MCP-KIS API",
    description="API server for My Capital Planner using Korea Investment & Securities (KIS) API.",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    # Authenticate with KIS API at server startup
    # The product code can be passed if different from default in YAML
    # ka.auth(product="01")
    if not ka.auth():
        # This error won't stop FastAPI from starting, but will be printed to console.
        # Consider a more robust way to handle critical startup failures if needed,
        # e.g., by setting a global state that API endpoints can check.
        print("CRITICAL: KIS API Authentication failed at server startup.")
        # raise RuntimeError("KIS API Authentication failed at server startup.") # This would stop the server
    else:
        print("KIS API Authentication successful at server startup.")
        print(f"Trading Environment: {'Paper Trading' if ka.isPaperTrading() else 'Real Trading'}")
        print(f"Using Account: {ka.getTREnv().my_acct}, Product Code: {ka.getTREnv().my_prod}")

@app.get("/")
async def root():
    return {"message": "Welcome to MCP-KIS API. See /docs for API documentation."}

# API router imports
from api.v1 import account as account_router
from api.v1 import market as market_router
from api.v1 import orders as orders_router

app.include_router(account_router.router, prefix="/api/v1/account", tags=["Account"])
app.include_router(market_router.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(orders_router.router, prefix="/api/v1/orders", tags=["Trading Orders"])

if __name__ == "__main__":
    # This is for running the server directly using `python server.py`
    # For production, you might use `uvicorn MCP-kis.server:app --reload` from the project root
    # Ensure KIS_APP_DIR is set if running from a different directory than MCP-kis
    print("Starting MCP-KIS server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
