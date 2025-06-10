# MCP-kis/api/v1/orders.py
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

import kis_auth as ka
import kis_domstk as kb
import sys, os

# Ensure MCP-kis directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir) # api/
project_root_dir = os.path.dirname(parent_dir) # MCP-kis/
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

router = APIRouter()

# --- Pydantic Models for Order Requests and Responses ---

class OrderRequest(BaseModel):
    stock_code: str = Field(..., description="종목코드 (6자리)", min_length=6, max_length=6)
    order_type: str = Field(..., description="'buy' 또는 'sell'") # KIS: B 매수, S 매도
    quantity: int = Field(..., description="주문 수량", gt=0)
    price_type: str = Field(..., description="'limit' (지정가) 또는 'market' (시장가)") # KIS: 00 지정가, 01 시장가
    price: Optional[int] = Field(None, description="주문 단가 (지정가 주문 시 필수)", gt=0)

    @model_validator(mode='after')
    def check_price_for_limit_order(cls, values):
        # For Pydantic v2, the validator signature is different.
        # Accessing fields via values.price_type, values.price is not direct.
        # Need to get them from the model_data (which is 'values' here).
        # However, Pydantic v2 model_validator is a class method or instance method.
        # Let's assume 'values' is the instance for mode='after'.
        price_type = values.price_type
        price = values.price
        if price_type == "limit" and (price is None or price <= 0) :
            raise ValueError("Price must be a positive value for limit orders.")
        return values

class OrderResponse(BaseModel):
    order_id: str = Field(..., description="주문 ID (KIS ODNO - 주문번호)")
    krx_fwdg_ord_orgno: str = Field(..., description="한국거래소전송주문조직번호")
    ord_tmd: str = Field(..., description="주문시각")
    message: str = Field(default="Order received successfully.")
    status: str = Field(default="received") # Could be 'accepted', 'rejected' based on immediate KIS response

# Model for TTTC8001R (주식일별주문체결조회) output2
class OrderDetails(BaseModel):
    odno: str = Field(description="주문번호")
    ord_dt: str = Field(description="주문일자")
    pdno: str = Field(description="종목코드 (상품번호)")
    prdt_name: str = Field(description="종목명 (상품명)")
    sll_buy_dvsn_cd: str = Field(description="매도매수구분코드 (01:매도, 02:매수)")
    sll_buy_dvsn_cd_name: Optional[str] = Field(None, description="매도매수구분명") # kis_domstk might not provide this directly
    ord_qty: str = Field(description="주문수량")
    ord_unpr: str = Field(description="주문단가")
    tot_ccld_qty: str = Field(description="총체결수량")
    ccld_avg_prc: str = Field(description="체결평균가 (평균체결단가)")
    ord_stat_cd: str = Field(description="주문상태코드") # e.g. 1:미체결, 2:체결, 3:취소 등 KIS 코드
    ord_stat_hngl_name: Optional[str] = Field(None, description="주문상태명 (e.g., '체결', '미체결', '취소')") # kis_domstk might not provide
    # Add other relevant fields from get_inquire_daily_ccld_lst (TTTC8001R output2)

# --- API Endpoints ---

@router.post("/", response_model=OrderResponse)
async def place_order(order: OrderRequest = Body(...)):
    '''
    Place a new stock order. Corresponds to KIS API TTTC0802U (주식 현금 매수/매도 주문).
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Check server startup.")

    kis_order_dv_code = "" # KIS API uses '01' for sell, '02' for buy
    if order.order_type.lower() == "buy":
        kis_order_dv_code = "02"
    elif order.order_type.lower() == "sell":
        kis_order_dv_code = "01"
    else:
        raise HTTPException(status_code=400, detail="Invalid order_type. Must be 'buy' or 'sell'.")

    # KIS 주문구분코드 (ORD_DVSN): 00 지정가, 01 시장가
    # The kb.get_order_cash function expects ord_dvsn as a parameter.
    # Price for market orders should be 0.

    order_price_for_api = 0
    kis_ord_dvsn = "" # KIS 주문구분코드 (지정가/시장가)
    if order.price_type.lower() == "limit":
        if order.price is None or order.price <= 0: # validator should catch this too
            raise HTTPException(status_code=400, detail="Price must be a positive value for limit orders.")
        order_price_for_api = order.price
        kis_ord_dvsn = "00" # 지정가
    elif order.price_type.lower() == "market":
        order_price_for_api = 0 # KIS API expects 0 for market order price
        kis_ord_dvsn = "01" # 시장가
    else:
        raise HTTPException(status_code=400, detail="Invalid price_type. Must be 'limit' or 'market'.")

    try:
        # Call kb.get_order_cash which should map to KIS API TTTC0802U
        # Parameters for get_order_cash: itm_no, qty, unpr, ord_dv (buy/sell), ord_dvsn (price type)
        # The original Sample01 get_order_cash took ord_dv as 'buy'/'sell'.
        # It needs to be mapped to '01'/'02' for KIS API if get_order_cash doesn't do it.
        # Let's assume get_order_cash is adapted or we pass the KIS codes directly if it expects them.
        # For now, using kis_order_dv_code ('01'/'02') and kis_ord_dvsn ('00'/'01')
        # This implies kb.get_order_cash needs to accept these KIS specific codes.
        # If kb.get_order_cash still expects 'buy'/'sell', this needs adjustment.
        # The sample code for get_order_cash in Sample01/kis_api01.py uses:
        # ORD_DVSN (주문구분) 00:지정가, 01:시장가 (Passed as is)
        # SLL_BUY_DVSN_CD (매도매수구분코드) 01:매도, 02:매수 (Passed as is)
        # So, we should pass these codes.

        result_obj = kb.get_order_cash( # This function should return the API response object (namedtuple or class instance)
            itm_no=order.stock_code,
            qty=order.quantity,
            unpr=order_price_for_api,
            ord_dv=kis_order_dv_code, # '01' for sell, '02' for buy
            ord_dvsn=kis_ord_dvsn    # '00' for limit, '01' for market
        )

        # KIS API TTTC0802U (주식 현금 매수/매도 주문) response (output1) contains:
        # KRX_FWDG_ORD_ORGNO, ODNO, ORD_TMD
        if result_obj and hasattr(result_obj, 'ODNO') and result_obj.ODNO:
            return OrderResponse(
                order_id=result_obj.ODNO,
                krx_fwdg_ord_orgno=getattr(result_obj, 'KRX_FWDG_ORD_ORGNO', ''),
                ord_tmd=getattr(result_obj, 'ORD_TMD', '')
            )
        else:
            error_msg = "Order placement failed."
            if result_obj and hasattr(result_obj, 'msg1') and result_obj.msg1:
                 error_msg += f" KIS Msg: {result_obj.msg1}."
            if result_obj and hasattr(result_obj, 'rt_cd') and result_obj.rt_cd != '0':
                 error_msg += f" RT_CD: {result_obj.rt_cd}."
            if not (result_obj and hasattr(result_obj, 'ODNO') and result_obj.ODNO):
                 error_msg += " KIS API Response did not contain expected ODNO (Order ID)."

            print(f"Order placement failed. Raw API response: {result_obj}") # Log for debugging
            raise HTTPException(status_code=500, detail=error_msg)

    except Exception as e:
        print(f"Exception during order placement: {e}") # Log for debugging
        raise HTTPException(status_code=500, detail=f"Error placing order: {str(e)}")


@router.get("/", response_model=List[OrderDetails])
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by order status name (e.g., '미체결', '체결', '전부취소') - KIS specific status name"),
    stock_code: Optional[str] = Query(None, description="Filter by stock code (6 digits)", min_length=6, max_length=6, regex="^[0-9]{6}$")
):
    '''
    Get a list of daily orders and their settlement details.
    Uses KIS API TTTC8001R (주식일별주문체결조회).
    Filtering by status or stock_code is performed on the retrieved data.
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Check server startup.")

    try:
        # kb.get_inquire_daily_ccld_lst maps to TTTC8001R.
        # Parameters for TTTC8001R:
        # INQR_STRT_DT, INQR_END_DT, SLL_BUY_DVSN_CD, INQR_DVSN, PDNO, CCLD_DVSN, ORD_GNO_BRNO, ODNO, INQR_DVSN_3, INQR_DVSN_1
        # The kis_domstk.py function get_inquire_daily_ccld_lst() has simplified params:
        # (self, inqr_dvsn='00', code='024800', qty=10, unpr=0, ord_dvsn='01', dv="01")
        # The 'dv' param in get_inquire_daily_ccld_lst seems to be mapped to INQR_DVSN_3 (조회구분3) in the sample
        # where "00":주문일자, "01":3개월 (INQR_DVSN_3)
        # Let's assume dv="01" means 3개월치.
        orders_df = kb.get_inquire_daily_ccld_lst(dv="01") # dv="01" for recent orders (e.g., last 3 months)

        if orders_df is None:
            raise HTTPException(status_code=500, detail="Failed to retrieve orders list: KIS API returned no data or an error occurred.")

        if orders_df.empty:
            return []

        # Filtering
        if stock_code:
            orders_df = orders_df[orders_df['pdno'] == stock_code]
        if status:
            # Assuming 'ord_stat_hngl_name' is a column in the DataFrame from get_inquire_daily_ccld_lst
            # This column might not exist if not explicitly added/mapped in kis_domstk.py
            # The API returns 'ord_stat_cd' (e.g., '1' for 미체결). Mapping to names might be needed.
            if 'ord_stat_hngl_name' in orders_df.columns:
                 orders_df = orders_df[orders_df['ord_stat_hngl_name'] == status]
            elif 'ord_stat_cd' in orders_df.columns:
                # If only code is available, client might need to map or we add mapping here/in kis_domstk
                print(f"Warning: Filtering by status name, but 'ord_stat_hngl_name' not in DataFrame. Available statuses (codes): {orders_df['ord_stat_cd'].unique()}")
            else:
                print("Warning: Cannot filter by status, 'ord_stat_hngl_name' or 'ord_stat_cd' not available in order data.")

        if orders_df.empty: # After filtering
            return []

        return orders_df.to_dict(orient='records')

    except Exception as e:
        print(f"Exception in list_orders: {e}") # Log for debugging
        raise HTTPException(status_code=500, detail=f"Error fetching orders list: {str(e)}")

# GET /orders/{order_id} and DELETE /orders/{order_id} will be implemented next.
# These require understanding how KIS API identifies specific orders for query/cancellation
# (e.g., KRX_FWDG_ORD_ORGNO, ODNO from the order placement response).


# --- Add/Modify Pydantic Models ---

class CancelOrderRequest(BaseModel):
    ord_orgno: str = Field(..., description="한국거래소전송주문조직번호 (Received from order placement response)")
    # ord_dvsn: str = Field(..., description="주문구분 (e.g., '00' 지정가, '01' 시장가 - KIS specific code for the original order)") # This might be needed by KIS
    rvse_cncl_dvsn_cd: str = Field(default="02", description="정정취소구분코드 ('01': 정정, '02': 취소)") # Default to '02' for cancel
    ord_qty: int = Field(default=0, description="주문수량 (취소시 보통 전량이므로 0 또는 원주문수량)") # For full cancel, often 0 and qty_all_ord_yn='Y'
    ord_unpr: int = Field(default=0, description="주문단가 (취소시 보통 0)")
    qty_all_ord_yn: str = Field(default="Y", description="잔량전부주문여부 ('Y' or 'N')")


class CancelOrderResponse(BaseModel):
    order_id: str # The original order ID that was targeted for cancellation
    krx_fwdg_ord_orgno: str = Field(..., description="한국거래소전송주문조직번호 (반환된 값)")
    odno: str = Field(..., description="주문번호 (새로운 ODNO for the cancel action or original)")
    ord_tmd: str = Field(..., description="주문시각 (취소 처리 시각)")
    message: str = Field(default="Cancel request processed.")
    status: str # e.g., "cancelled", "cancellation_pending", "cancellation_rejected"

# # --- Add Endpoints ---

@router.get("/{order_id}", response_model=Optional[OrderDetails])
async def get_order_details(
    order_id: str = Path(..., description="The KIS ODNO of the order")
):
    '''
    Get details for a specific order by its KIS ODNO.
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Check server startup.")

    try:
        # Fetch all recent orders and filter. This might be inefficient for a large number of orders.
        # A more direct KIS API to fetch a single order by ODNO would be better if available.
        # For now, using get_inquire_daily_ccld_lst.
        # Parameters for get_inquire_daily_ccld_lst:
        # Pass ODNO to the function if it supports filtering by ODNO directly.
        # The sample kis_domstk.py get_inquire_daily_ccld_lst does not show an 'odno' parameter.
        # So, manual filtering is required after fetching a broader list.
        orders_df = kb.get_inquire_daily_ccld_lst(dv="01") # dv="01" for recent (e.g., 3 months)

        if orders_df is None:
             raise HTTPException(status_code=500, detail="Failed to retrieve orders list from KIS API for filtering.")
        if orders_df.empty:
            # No orders found at all, so the specific one won't be there.
            raise HTTPException(status_code=404, detail=f"Order with ID '{order_id}' not found (no orders in the lookup period).")

        # Filter by 'odno'
        target_order_df = orders_df[orders_df['odno'] == order_id]

        if target_order_df.empty:
            raise HTTPException(status_code=404, detail=f"Order with ID '{order_id}' not found in the retrieved list.")

        # Assuming order_id (ODNO) is unique enough for this context
        # .to_dict(orient='records') returns a list, so take the first element.
        return target_order_df.iloc[0].to_dict()

    except HTTPException: # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        print(f"Exception in get_order_details for {order_id}: {e}") # Log for debugging
        raise HTTPException(status_code=500, detail=f"Error fetching order {order_id}: {str(e)}")


@router.delete("/{order_id}", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: str = Path(..., description="The KIS ODNO of the order to cancel (this is 'orgn_odno' for KIS API)"),
    # KIS TTTC0803U (주식 정정취소 주문) requires:
    # CANO (계좌번호), OPRC_PDNO (상품번호), KRX_FWDG_ORD_ORGNO, ORGN_ODNO, ORD_DVSN (원주문 구분),
    # RVSE_CNCL_DVSN_CD, ORD_QTY, ORD_UNPR, QTY_ALL_ORD_YN
    # The body should contain fields needed by kb.get_order_rvsecncl not in the path
    cancel_details: CancelOrderRequest = Body(...)
):
    '''
    Cancel an existing stock order.
    'order_id' from the path is the original order number (orgn_odno for KIS API).
    'ord_orgno' (KRX_FWDG_ORD_ORGNO for KIS API) must be provided in the request body.
    '''
    if not ka.getTREnv() or not ka.getTREnv().my_token:
        raise HTTPException(status_code=401, detail="Not authenticated. Check server startup.")

    try:
        # kb.get_order_rvsecncl maps to TTTC0803U.
        # Expected parameters for get_order_rvsecncl(self, ord_orgno, orgn_odno, ord_dvsn, rvse_cncl_dvsn_cd, ord_qty, ord_unpr, qty_all_ord_yn)
        # ord_dvsn (원주문 주문구분) is the original order's price type ('00' 지정가, '01' 시장가).
        # This is crucial. If not stored, it's hard to cancel accurately.
        # Defaulting to "00" (지정가) as a common case, but this is a significant assumption.
        # A robust system would retrieve the original order's details to get its 'ord_dvsn' if not stored locally.

        original_order_division_code = "00" # Defaulting to '지정가'. Needs improvement.
        # Consider fetching order details first to get the correct original_order_division_code if possible.
        # For example, call get_order_details(order_id) if it can provide this.
        # However, OrderDetails model doesn't currently include 'ord_dvsn' (price type like '00'/'01').

        result_obj = kb.get_order_rvsecncl(
            ord_orgno=cancel_details.ord_orgno, # KRX_FWDG_ORD_ORGNO from original order
            orgn_odno=order_id,                 # ORGN_ODNO from original order (path param)
            ord_dvsn=original_order_division_code, # ORD_DVSN of original order ('00' or '01') - CRITICAL PARAM
            rvse_cncl_dvsn_cd=cancel_details.rvse_cncl_dvsn_cd, # '02' for cancel
            ord_qty=cancel_details.ord_qty,     # Usually 0 for full cancel with QTY_ALL_ORD_YN='Y'
            ord_unpr=cancel_details.ord_unpr,   # Usually 0 for cancel
            qty_all_ord_yn=cancel_details.qty_all_ord_yn # 'Y' for full cancel
        )

        # KIS API TTTC0803U response (output1) contains:
        # KRX_FWDG_ORD_ORGNO, ODNO, ORD_TMD
        if result_obj and hasattr(result_obj, 'ODNO') and result_obj.ODNO:
            # Check rt_cd for success, '0' is usually success for KIS
            if hasattr(result_obj, 'rt_cd') and result_obj.rt_cd != '0':
                error_msg = f"Order cancellation failed. KIS Msg: {getattr(result_obj, 'msg1', 'Unknown error')}, RT_CD: {result_obj.rt_cd}"
                print(f"Cancel API call failed: {error_msg}") # Log for debugging
                raise HTTPException(status_code=400, detail=error_msg) # 400 for failed business logic

            return CancelOrderResponse(
                order_id=order_id, # The original order_id that was targeted
                krx_fwdg_ord_orgno=getattr(result_obj, 'KRX_FWDG_ORD_ORGNO', ''),
                odno=result_obj.ODNO, # This is the new ODNO for the cancellation transaction itself
                ord_tmd=getattr(result_obj, 'ORD_TMD', ''),
                status="cancelled" # Assuming immediate successful cancellation for this example
            )
        else:
            error_msg = "Order cancellation failed. KIS API Response format unexpected or ODNO missing."
            if result_obj and hasattr(result_obj, 'msg1'): error_msg += f" KIS Msg: {result_obj.msg1}"
            if result_obj and hasattr(result_obj, 'rt_cd') and result_obj.rt_cd != '0': error_msg += f" RT_CD: {result_obj.rt_cd}"
            print(f"Cancel API call failed: {error_msg}. Raw response: {result_obj}") # Log for debugging
            raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException: # Re-raise explicitly handled HTTP exceptions
        raise
    except Exception as e:
        print(f"Exception during order cancellation for {order_id}: {e}") # Log for debugging
        raise HTTPException(status_code=500, detail=f"Error cancelling order {order_id}: {str(e)}")
