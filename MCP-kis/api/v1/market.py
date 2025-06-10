# MCP-kis/api/v1/market.py
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
import kis_auth as ka # To access KIS environment details if needed
import kis_domstk as kb # KIS Domestic Stock APIs
import sys, os

# Ensure MCP-kis directory is in sys.path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # This should be api/
project_root_dir = os.path.dirname(parent_dir) # This should be MCP-kis/
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)


router = APIRouter()

# Pydantic Model for Response Structure
# Based on KIS API (FHKST01010100) 주식현재가시세
class StockPriceResponse(BaseModel):
    stck_prpr: str = Field(description="주식 현재가")
    prdy_vrss: str = Field(description="전일 대비")
    prdy_vrss_sign: str = Field(description="전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)")
    acml_vol: str = Field(description="누적 거래량")
    stck_oprc: str = Field(description="시가")
    stck_hgpr: str = Field(description="고가")
    stck_lwpr: str = Field(description="저가")
    # Other potentially useful fields from the API:
    # prdy_ctrt: 전일 대비율
    # vol_inrt: 거래량증가율 (전일거래량대비)
    # stck_sdpr: 기준가
    # etc.

@router.get("/price/{stock_code}", response_model=StockPriceResponse)
async def get_stock_price(
    stock_code: str = Path(..., title="Stock Code", description="The 6-digit stock code (e.g., '005930')", min_length=6, max_length=6, regex="^[0-9]{6}$")
):
    '''
    Get current price information for a given stock.
    Uses KIS API FHKST01010100 (주식현재가시세).
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated or token not available. Check server startup.")

    # Validation for stock_code is partially handled by Path's regex, min_length, max_length
    # but an explicit check can be kept if preferred or for non-FastAPI contexts.
    # if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
    #     raise HTTPException(status_code=400, detail="Invalid stock code format. Must be 6 digits.")

    try:
        # kb.get_inquire_price returns a namedtuple (or similar object) with stock data
        price_data_obj = kb.get_inquire_price(itm_no=stock_code)
        if price_data_obj:
            # Convert the namedtuple/object to a dictionary to unpack into the Pydantic model.
            # vars() works well if price_data_obj is an object with __dict__ (like a typical class instance).
            # If it's a namedtuple, _asdict() is the method.
            # Assuming get_inquire_price returns an object that vars() can handle or a namedtuple.
            if hasattr(price_data_obj, '_asdict'): # Check if it's a namedtuple
                price_data_dict = price_data_obj._asdict()
            else: # Assume it's a class instance
                price_data_dict = vars(price_data_obj)

            return StockPriceResponse(**price_data_dict)
        else:
            # This case means API returned no data (e.g. invalid stock code not caught by KIS server but returns empty)
            raise HTTPException(status_code=404, detail=f"Price data not found for stock code: {stock_code}. KIS API returned no data.")
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in get_stock_price for {stock_code}: {e}")
        # Check if the error is due to KIS API specific error message e.g. from APIResp.printError()
        # Error messages from KIS might be in e.g. e.detail or similar if the exception is an HTTPException from a lower layer.
        # For now, a generic 500.
        raise HTTPException(status_code=500, detail=f"Error fetching price for {stock_code}: {str(e)}")
