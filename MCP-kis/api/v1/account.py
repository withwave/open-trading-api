# MCP-kis/api/v1/account.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field # For data validation and response models
import os
import sys

# Ensure the parent directory (MCP-kis) is in sys.path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) # This should be MCP-kis directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import kis_auth as ka # To access KIS environment details if needed
import kis_domstk as kb # KIS Domestic Stock APIs

router = APIRouter()

# Pydantic Models for Response Structures
# Based on KIS API Documentation for 주식잔고조회 (TTTC8434R)
# output1 (예수금 등 상세)
class AccountBalanceResponse(BaseModel):
    dnca_tot_amt: str = Field(description="예수금총금액")
    nxdy_excc_amt: str = Field(description="익일정산금액")
    prvs_rcdl_excc_amt: str = Field(description="가수도정산금액 (예탁금으로 사용될 수 있는 금액)") # Usually referred to as D+2 예수금
    cma_evlu_amt: str = Field(description="CMA평가금액")
    bfdy_buy_qty: str = Field(description="전일매수체결수량", default="0") # Default if not present
    bfdy_sll_qty: str = Field(description="전일매도체결수량", default="0") # Default if not present
    thdt_buy_qty: str = Field(description="금일매수체결수량", default="0") # Default if not present
    thdt_sll_qty: str = Field(description="금일매도체결수량", default="0") # Default if not present
    # Fields from output1 of TTTC8434R (get_inquire_balance_obj)
    asst_icdc_amt: str = Field(description="자산증감액")
    asst_icdc_erng_rt: str = Field(description="자산증감수익률")
    tot_evlu_amt: str = Field(description="총평가금액 (주식, 펀드, 채권 등)")
    scts_evlu_amt: str = Field(description="유가증권평가금액")
    tot_pftlos_amt: str = Field(description="총손익금액")
    tot_pftlos_erng_rt: str = Field(description="총손익수익률")
    # These are just a selection, more can be added from API docs.

# output2 (잔고 상세) - for /positions
class StockPosition(BaseModel):
    pdno: str = Field(description="상품번호 (종목코드)")
    prdt_name: str = Field(description="상품명")
    hldg_qty: str = Field(description="보유수량")
    pchs_avg_pric: str = Field(description="매입평균가격 (매입단가)")
    pchs_amt: str = Field(description="매입금액")
    evlu_pfls_rt: str = Field(description="평가손익율")
    evlu_amt: str = Field(description="평가금액")
    crnt_prc: str = Field(description="현재가 (실시간)")
    # Add other relevant fields from the KIS API response get_inquire_balance_lst (output2 elements)


@router.get("/balance", response_model=AccountBalanceResponse)
async def get_account_balance():
    '''
    Get overall account balance details (예수금, 총평가금액 등).
    Corresponds to 'output1' of KIS API TTTC8434R.
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated or token not available. Check server startup.")

    try:
        balance_data = kb.get_inquire_balance_obj() # This function should return an object with output1 and output2
        if balance_data and hasattr(balance_data, 'output1') and balance_data.output1:
            # output1 is a list containing one dictionary
            output1_data = balance_data.output1[0]
            # Map KIS API response fields to our Pydantic model fields
            # Ensure all fields in AccountBalanceResponse are present in output1_data or provide defaults
            return AccountBalanceResponse(**output1_data)
        else:
            raise HTTPException(status_code=500, detail="Failed to retrieve account balance or unexpected API response format.")
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in get_account_balance: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching account balance: {str(e)}")

@router.get("/positions", response_model=list[StockPosition])
async def get_account_positions():
    '''
    Get list of current stock holdings (보유 주식 리스트).
    Corresponds to 'output2' of KIS API TTTC8434R, which is returned by get_inquire_balance_lst()
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated or token not available. Check server startup.")

    try:
        # get_inquire_balance_lst() returns a pandas DataFrame based on output2
        positions_df = kb.get_inquire_balance_lst()
        if positions_df is not None and not positions_df.empty:
            # Convert DataFrame to list of dicts, ensure keys match StockPosition fields
            # Pandas to_dict(orient='records') is suitable if column names match Pydantic fields
            return positions_df.to_dict(orient='records')
        elif positions_df is not None: # Empty DataFrame (no positions)
            return []
        else:
            # This case implies the API call itself failed or returned something unexpected (e.g., None)
            raise HTTPException(status_code=500, detail="Failed to retrieve account positions. API might have returned no data or an error.")
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error in get_account_positions: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching account positions: {str(e)}")
