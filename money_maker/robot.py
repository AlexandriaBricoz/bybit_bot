from datetime import datetime
import pandas as pd
import yaml
import math
from pybit.unified_trading import HTTP
from utils import calculate_timestamp, from_timestamp, assign_order_name
      
form = yaml.safe_load(open('form.yml', 'r'))
session = HTTP(testnet=False, api_key=form['bybit']['api_key'], api_secret=form['bybit']['api_secret'])

class Robot:

    def __init__(self) -> None:
        pass

    def delete_all_orders(self):
        session.cancel_all_orders(
            category="spot",
            symbol=form['symbol'],
            orderFilter = 'StopOrder'
            )
        session.cancel_all_orders(
            category="spot",
            symbol=form['symbol'],
            orderFilter = 'Order'
            )
    def create_order_11(self):
        btc_amnt = float(session.get_coin_balance(accountType="UNIFIED", coin="BTC")['result']['balance']['walletBalance'])
        btc_amnt = math.floor(btc_amnt * 10**6) / 10**6
        if btc_amnt >= 0.0002:
            session.place_order(
                category = 'spot',
                symbol=form['symbol'],
                isLeverage = form['isLeverage'],
                orderType = "Market",
                side = 'Sell',
                qty = btc_amnt, #продать current объем btc
                marketUnit = 'baseCoin' 
                )
        else:
            usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
            session.place_order(
                category = 'spot',
                symbol=form['symbol'],
                isLeverage = form['isLeverage'],
                orderType = "Market",
                side = 'Buy',
                qty = form['values']['q9'], # купить резервный объем btc
                #qty = usdc_amnt, 
                #marketUnit = 'quoteCoin' 
                marketUnit = 'baseCoin'                
                )
                
            btc_amnt = float(session.get_coin_balance(accountType="UNIFIED", coin="BTC")['result']['balance']['walletBalance'])
            btc_amnt = math.floor(btc_amnt * 10**6) / 10**6
            session.place_order(
                category = 'spot',
                symbol=form['symbol'],
                isLeverage = form['isLeverage'],
                orderType = "Market",
                side = 'Sell',
                qty = btc_amnt, #продать current объем btc
                marketUnit = 'baseCoin' 
                )
            
    def create_order_1(self):
        marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        #last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderFilter = 'StopOrder',
            orderType = "Market",
            side = 'Sell',
            #triggerPrice = last_order_price,
            triggerPrice = marketPrice - form['ints']['int_1'],
            #triggerPrice = last_order_price - form['int_triggers']['int_trigger3'],
            #triggerPrice = last_order_price + form['int_triggers']['int_trigger2'],
            qty = form['values']['q1'],
            marketUnit = 'baseCoin'
        )


    #def create_order_1(self):
        #marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        #session.place_order( 
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderType = "Limit",
            #side = 'Sell',
            #orderFilter = 'StopOrder',
            #triggerPrice = marketPrice - form['ints']['int_1'] + form['int_triggers']['int_trigger1'],
            #price = marketPrice - form['ints']['int_1'],
            #qty = form['values']['q1'],
            #marketUnit = 'baseCoin'
            #)            
    

    #def create_order_enter_1(self):
        #usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        #session.place_order( 
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderType = "Market",
            #side = 'Buy',
            #qty = usdc_amnt,
            #marketUnit = 'quoteCoin'
        #)
    def create_order_enter_2(self):
        #usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        session.place_order(
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = 'Market',
            side = 'Buy',
            #qty = usdc_amnt,
            #marketUnit = 'quoteCoin'
            qty = form['values']['q_enter2'],
            marketUnit = 'quoteCoin'            
        )
    def create_order_8(self):
        usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        session.place_order(
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = 'Market',
            side = 'Buy',
            qty = usdc_amnt,
            marketUnit = 'quoteCoin'
        )
        
    #def create_order_7(self):
        #usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        #last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        #session.place_order(
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderType = 'limit',
            #side = 'Buy',
            #qty = usdc_amnt,
            #triggerPrice = last_order_price - form['ints']['int_3'] - form['int_triggers']['int_trigger1'],
            #price = last_order_price - form['ints']['int_3'],
            #qty = form['values']['q3'],            
            #marketUnit = 'quoteCoin'
        #)
        
    def create_order_7(self):
        usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        session.place_order(
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = 'Market',
            side = 'Buy',
            qty = usdc_amnt,
            marketUnit = 'quoteCoin'
        )           
        
    def create_order_9(self):
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = "Market",
            side = 'Buy',
            qty = form['values']['q9'], # купить резервный объем btc
            marketUnit = 'baseCoin'
        )

    def create_order_5(self):
        marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        #last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderFilter = 'StopOrder',
            orderType = "Market",
            side = 'Sell',
            triggerPrice = marketPrice - form['ints']['int_2'],
            #triggerPrice = last_order_price - form['int_triggers']['int_trigger3'],
            #triggerPrice = last_order_price + form['int_triggers']['int_trigger2'],
            qty = form['values']['q5'],
            marketUnit = 'baseCoin'
        )
        
    def create_order_10(self):
        btc_amnt = float(session.get_coin_balance(accountType="UNIFIED", coin="BTC")['result']['balance']['walletBalance'])
        btc_amnt = math.floor(btc_amnt * 10**6) / 10**6
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = "Market",
            side = 'Sell',
            qty = btc_amnt,
            marketUnit = 'baseCoin'
        )     
        
    def create_order_1(self):
        #marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderFilter = 'StopOrder',
            orderType = "Market",
            side = 'Sell',
            triggerPrice = last_order_price - form['ints']['int_1'],
            #triggerPrice = marketPrice - form['ints']['int_2'],
            #triggerPrice = last_order_price - form['int_triggers']['int_trigger3'],
            #triggerPrice = last_order_price + form['int_triggers']['int_trigger2'],
            qty = form['values']['q5'],
            marketUnit = 'baseCoin'
        )        

    #def create_order_1(self):
        #marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        #session.place_order( 
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderType = "Limit",
            #side = 'Sell',
            #orderFilter = 'StopOrder',
            #triggerPrice = marketPrice,
            #triggerPrice = marketPrice - form['ints']['int_1']+form['int_triggers']['int_trigger1'],            
            #price = marketPrice - form['ints']['int_1'],
            #price = marketPrice - form['ints']['int_1'],            
            #qty = form['values']['q1'],
            #marketUnit = 'baseCoin'
            #)            
    #def create_order_3(self):
        #marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        #session.place_order( 
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderType = "Limit",
            #side = 'Sell',
            #orderFilter = 'StopOrder',
            #triggerPrice = marketPrice-form['ints']['int_3']+form['int_triggers']['int_trigger2'],
            #price = marketPrice - form['ints']['int_3'],
            #qty = form['values']['q3'],
            #marketUnit = 'baseCoin'
            #)

    # Последний вариант - 10-05-2024 
    def create_order_3(self):
        usdc_amnt = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        session.place_order(
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = 'Market',
            side = 'Buy',
            #qty = form['values']['q3'],
            qty = usdc_amnt,
            marketUnit = 'quoteCoin'
        )   
        
    #def create_order_3(self):
        #last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        #session.place_order( 
            #category = 'spot',
            #symbol=form['symbol'],
            #isLeverage = form['isLeverage'],
            #orderFilter = 'StopOrder',
            #orderType = "Market",
            #side = 'buy',
            #triggerPrice = last_order_price + form['ints']['int_3'],
            #qty = form['values']['q3'],
            #marketUnit = 'baseCoin'  
        #)            
        
    def create_order_4(self):
        btc_amnt = float(session.get_coin_balance(accountType="UNIFIED", coin="BTC")['result']['balance']['walletBalance'])
        btc_amnt = math.floor(btc_amnt * 10**6) / 10**6
        session.place_order( 
            category = 'spot',
            symbol=form['symbol'],
            isLeverage = form['isLeverage'],
            orderType = "Market",
            side = 'Sell',
            qty = btc_amnt,
            marketUnit = 'baseCoin'
        ) 
        
    def check_exec_time(self):
        execTime = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return execTime
    def check_market_price(self):
        marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        return marketPrice
    def check_last_order_price(self):
        last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['execPrice'])
        return last_order_price
    def check_last_order_side(self):
        last_order_id = session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['side']
        return last_order_id
    def check_last_order_trigger_price(self):
        last_order_price = float(session.get_executions(category='spot', symbol=form['symbol'])['result']['list'][0]['triggerPrice'])
        return last_order_price

    def check_orders(self):
        #обработка отсутствия ор
        bbt_request = session.get_open_orders(category='spot', symbol=form['symbol'])
        open_orders = bbt_request['result']['list']
        attribs_ = ['orderType', 'side', 'qty', 'triggerPrice', 'price', 'createdTime']
        fr_ =  pd.DataFrame.from_records(open_orders)[attribs_]
        fr_['qty'] = fr_['qty'].astype(float)
        fr_['createdTime'] = pd.to_datetime(fr_['createdTime'].apply(lambda x: from_timestamp(x)))
        fr_['createdTime'] = fr_['createdTime'].dt.time
        fr_['name'] = fr_.apply(assign_order_name, axis =1)
        return fr_
    def check_trades(self):
        trades = session.get_executions(category="spot",)['result']['list']
        trades_table = pd.DataFrame.from_records(trades)
        attr_ = ['orderType', 'side', 'execQty', 'execPrice', 'execTime']
        trades_table = trades_table[attr_]
        trades_table['execQty'] = trades_table['execQty'].astype(float)
        trades_table.rename(columns={'execQty':'qty'}, inplace = True)
        trades_table['execTime'] = pd.to_datetime(trades_table['execTime'].apply(lambda x: from_timestamp(x)))
        trades_table['execTime'] = trades_table['execTime'].dt.time
        trades_table['name'] = trades_table.apply(assign_order_name, axis =1)
        return trades_table
    def check_trades_via_order_history(self):
        fr_ = pd.DataFrame.from_records(session.get_order_history(category="spot",)['result']['list'])
        fr_ = fr_[fr_['orderStatus']=='Filled']
        attribs_ = ['orderType', 'side', 'qty', 'avgPrice', 'createdTime']
        fr_ = fr_[attribs_]
        fr_['qty'] = fr_['qty'].astype(float)
        fr_.rename(columns={'avgPrice':'execPrice'}, inplace = True)
        fr_.rename(columns={'createdTime':'execTime'}, inplace = True)
        fr_['execTime'] = pd.to_datetime(fr_['execTime'].apply(lambda x: from_timestamp(x)))
        fr_['execTime'] = fr_['execTime'].dt.time
        fr_['name'] = fr_.apply(assign_order_name, axis =1)
        return fr_
    def calculate_balance(self):
        marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        token1_balance = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        token2_balance = float(session.get_coin_balance(accountType="UNIFIED",coin="BTC",)['result']['balance']['walletBalance'])
        total_balance = token1_balance + marketPrice * token2_balance
        return token1_balance, token2_balance, total_balance
    def calculate_total_balance(self):
        marketPrice = float(session.get_tickers(category="spot", symbol=form['symbol'])['result']['list'][0]['ask1Price'])
        token1_balance = float(session.get_coin_balance(accountType="UNIFIED",coin="USDC",)['result']['balance']['walletBalance'])
        token2_balance = float(session.get_coin_balance(accountType="UNIFIED",coin="BTC",)['result']['balance']['walletBalance'])
        total_balance = token1_balance + marketPrice * token2_balance
        return total_balance 

    def calc_open_orders_id(self):
        bbt_req = session.get_open_orders(category = 'spot', symbol=form['symbol'])
        open_orders_ = bbt_req['result']['list']
        open_orders_id_ = pd.DataFrame.from_records(open_orders_)['orderId'].to_list()
        open_orders_id_.reverse()
        return open_orders_id_
    def calc_open_orders_table(self):
        bbt_req = session.get_open_orders(category = 'spot', symbol=form['symbol'])
        open_orders_ = bbt_req['result']['list']

        attribs_ = ['symbol','orderType', 'side', 'qty', 'triggerPrice', 'price', 'createdTime']
        fr_ =  pd.DataFrame.from_records(open_orders_)[attribs_]
        # fr_['createdTime'] = pd.to_datetime(fr_['createdTime'].apply(lambda x: from_timestamp(x)))
        # fr_['createdTime'] = fr_['createdTime'].dt.time
        return fr_