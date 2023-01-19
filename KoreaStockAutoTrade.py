import requests
import json
import datetime
import time
import yaml

yaml_path = r'D:\git\trading_data\congif.yaml'

with open(yaml_path, encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)
APP_KEY = _cfg['APP_KEY']
APP_SECRET = _cfg['APP_SECRET']
ACCESS_TOKEN = ""
CANO = _cfg['CANO']
ACNT_PRDT_CD = _cfg['ACNT_PRDT_CD']
DISCORD_WEBHOOK_URL = _cfg['DISCORD_WEBHOOK_URL']
URL_BASE = _cfg['URL_BASE']

def send_message(msg):
    """Sending to discord webhook"""
    now = datetime.datetime.now()
    message = {"content": f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"}
    requests.post(DISCORD_WEBHOOK_URL, data=message)
    print(message)

def get_access_token():
    """get access token"""
    headers = {"content-type":"application/json"}
    body = {"grant_type":"client_credentials",
    "appkey":APP_KEY, 
    "appsecret":APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN

def hashkey(datas):
    """hash key"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
    'content-Type' : 'application/json',
    'appKey' : APP_KEY,
    'appSecret' : APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey

def get_current_price(code="005930"):
    """current price check"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
            "authorization": f"Bearer {ACCESS_TOKEN}",
            "appKey":APP_KEY,
            "appSecret":APP_SECRET,
            "tr_id":"FHKST01010100"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr'])

def get_target_price(code="005930"):
    """Investigate acquisition target price with volatility breakthrough strategy"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"FHKST01010400"}
    params = {
    "fid_cond_mrkt_div_code":"J",
    "fid_input_iscd":code,
    "fid_org_adj_prc":"1",
    "fid_period_div_code":"D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_oprc = int(res.json()['output'][0]['stck_oprc']) # today start
    stck_hgpr = int(res.json()['output'][1]['stck_hgpr']) # yesterday high
    stck_lwpr = int(res.json()['output'][1]['stck_lwpr']) # yesterdat low
    target_price = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5
    return target_price

def get_stock_balance():
    """Check balance"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8434R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    send_message(f"==== Balance ====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
            send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    send_message(f"=================")
    return stock_dict

def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC8908R",
        "custtype":"P",
    }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    send_message(f"possible current balance: {cash}won")
    return int(cash)

def buy(code="005930", qty="1"):
    """buying at current market price"""  
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": str(int(qty)),
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0802U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[Buying success!]{str(res.json())}")
        return True
    else:
        send_message(f"[Buying failed!]{str(res.json())}")
        return False

def sell(code="005930", qty="1"):
    """Selling at a market price"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "01",
        "ORD_QTY": qty,
        "ORD_UNPR": "0",
    }
    headers = {"Content-Type":"application/json", 
        "authorization":f"Bearer {ACCESS_TOKEN}",
        "appKey":APP_KEY,
        "appSecret":APP_SECRET,
        "tr_id":"TTTC0801U",
        "custtype":"P",
        "hashkey" : hashkey(data)
    }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        send_message(f"[Sale succese!!]{str(res.json())}")
        return True
    else:
        send_message(f"[Sale failed!!]{str(res.json())}")
        return False

# Begin!
try:
    print('Begin')
    ACCESS_TOKEN = get_access_token()

    symbol_list = ["005930","035720","000660","069500"] # buying wishlist.
    bought_list = [] # bought list
    total_cash = get_balance() # $ had.
    stock_dict = get_stock_balance() # check stock balance
    for sym in stock_dict.keys():
        bought_list.append(sym)
    target_buy_count = 3 # how many company I wanna buy.
    buy_percent = 0.33 # percentage per company.
    buy_amount = total_cash * buy_percent  # amount of money computation as percentages.
    soldout = False

    # send_message("=== Programme Begin!! ===")
    # while True:
    #     t_now = datetime.datetime.now()
    #     t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
    #     t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
    #     t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
    #     t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
    #     today = datetime.datetime.today().weekday()
    #     if today == 5 or today == 6:  # sat or sun.
    #         send_message("Terminating on Sat or Sun.")
    #         break
    #     if t_9 < t_now < t_start and soldout == False: # Selling the remained.
    #         for sym, qty in stock_dict.items():
    #             sell(sym, qty)
    #         soldout == True
    #         bought_list = []
    #         stock_dict = get_stock_balance()
    #     if t_start < t_now < t_sell :  # AM 09:05 ~ PM 03:15 : Buying
    #         for sym in symbol_list:
    #             if len(bought_list) < target_buy_count:
    #                 if sym in bought_list:
    #                     continue
    #                 target_price = get_target_price(sym)
    #                 current_price = get_current_price(sym)
    #                 if target_price < current_price:
    #                     buy_qty = 0  # Initilization quantity.
    #                     buy_qty = int(buy_amount // current_price)
    #                     if buy_qty > 0:
    #                         send_message(f"{sym} 목표가 달성({target_price} < {current_price}) 매수를 시도합니다.")
    #                         result = buy(sym, buy_qty)
    #                         if result:
    #                             soldout = False
    #                             bought_list.append(sym)
    #                             get_stock_balance()
    #                 time.sleep(1)
    #         time.sleep(1)
    #         if t_now.minute == 30 and t_now.second <= 5: 
    #             get_stock_balance()
    #             time.sleep(5)
    #     if t_sell < t_now < t_exit:  # 15:15 ~ 15:20 : selling all the remains
    #         if soldout == False:
    #             stock_dict = get_stock_balance()
    #             for sym, qty in stock_dict.items():
    #                 sell(sym, qty)
    #             soldout = True
    #             bought_list = []
    #             time.sleep(1)
    #     if t_exit < t_now:  # PM 03:20 ~ :Terminating the programme
    #         send_message("Terminating the programme.")
    #         break
except Exception as e:
    send_message(f"[오류 발생]{e}")
    time.sleep(1)