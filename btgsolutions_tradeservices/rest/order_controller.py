from threading import Thread
from time import sleep
import requests
import pandas as pd

ALLOWED_SIDE = ["B","S"]
ALLOWED_ORDER_TYPE = ["Market", "Limit", "Stop limit"]
ALLOWED_DMA = ["true", "false"]
ALLOWED_TIF = [
    "Day", # A ordem funcionará durante todo o horário de negociação do dia.(não participa do leilão).
    "GTC", # "Good Till Cancel". A ordem ficará ativa até que seja executada ou cancelada.
    "MOP", # "At the Opening". Ordem válida para o leilão de abertura.
    "IOC", # "Immediate or Cancel". A ordem será executada com a quantidade disponível e cancelará imediatamente o resto
    "FOK", # "Fill or Kill". Se a ordem não for executada por inteira, todo o pedido será cancelado.
    "GTD", # "Good Till Date". Esta ordem será válida até a data especificada no calendário ao lado.
    "MOC", # "At the Close". Ordem para ser enviada no leilão de fechamento (Closing Call).
    "MOA", # "Good for Auction". Usado para o leilão de abertura e os leilões intradiários.
]

INTEGER_FIELDS = ["qty", "account", "execBroker"]
FLOAT_FIELDS = ["price", "stopPx"]

def _background_periodically_update_orders(order_controller):
    while True:
        sleep(2)
        df_orders = order_controller.summary()
        for index, order in df_orders.iterrows():
            order_controller.order_update_callback(order)

def generic_update_callback(order):

    ret = f"OrderId: {order.get('clOrdId')} - [{order.get('ordStatus')}] {order.get('side')} {order.get('cumQty')}/{order.get('qty')} {order.get('symbol')} @ {order.get('avgPx')}"
    if order.get('price') is not None:
        ret += f" with Px: {order.get('price')}"
    if order.get('stopPx') is not None:
        ret += f" and stopPx: {order.get('stopPx')}"
    if order.get('text') and order.get('text').replace('[B3]','').strip() != "":
        ret += f"\nWARNING: {order.get('text')}"
    
    print(f"Order update: {ret}\n")

def validate_order_parameter_type(parameter_name:str, parameter_value:str):

    if not isinstance(parameter_value, str):
        raise TypeError(f"parameter {parameter_name} should be a string")

def try_to_coerce_parameter_value(parameter_name:str, parameter_value:str):

    if parameter_name in INTEGER_FIELDS:
        try:
            int(parameter_value)
        except:
            raise ValueError(f"parameter {parameter_name} must allow integer parse")
    elif parameter_name in FLOAT_FIELDS:
        try:
            float(parameter_value)
        except:
            raise ValueError(f"parameter {parameter_name} must allow float parse")

def validate_create_order_parameters(symbol:str, side:str, qty:str, account:str, execBroker:str, ordType:str, timeInForce:str, isDMA:str, entity:str, price:str, stopPx:str):

    validate_order_parameter_type("symbol", symbol)
    validate_order_parameter_type("side", side)
    validate_order_parameter_type("qty", qty)
    validate_order_parameter_type("account", account)
    validate_order_parameter_type("execBroker", execBroker)
    validate_order_parameter_type("ordType", ordType)
    validate_order_parameter_type("timeInForce", timeInForce)
    validate_order_parameter_type("isDMA", isDMA)
    validate_order_parameter_type("entity", entity)

    try_to_coerce_parameter_value("qty", qty)
    try_to_coerce_parameter_value("account", account)
    try_to_coerce_parameter_value("execBroker", execBroker)

    if ordType in ["Limit", "Stop limit"]:
        validate_order_parameter_type("price", price)
        try_to_coerce_parameter_value("price", price)
        if ordType == "Stop limit":
            validate_order_parameter_type("stopPx", stopPx)
            try_to_coerce_parameter_value("stopPx", stopPx)

    if side not in ALLOWED_SIDE:
        raise ValueError(f"parameter side should be one of the following: {ALLOWED_SIDE}")
    if ordType not in ALLOWED_ORDER_TYPE:
        raise ValueError(f"parameter ordType should be one of the following: {ALLOWED_ORDER_TYPE}")
    if isDMA not in ALLOWED_DMA:
        raise ValueError(f"parameter isDMA should be one of the following: {ALLOWED_DMA}")
    if timeInForce not in ALLOWED_TIF:
        raise ValueError(f"parameter timeInForce should be one of the following: {ALLOWED_TIF}")

def validate_update_order_parameters(qty:str, price:str, stopPx:str, ordType:str, timeInForce:str):

    if qty is None and price is None and stopPx is None:
        raise Exception(f"Must provide 'qty', 'price' and/or 'stopPx'.")

    validate_order_parameter_type("ordType", ordType)
    if ordType not in ALLOWED_ORDER_TYPE:
        raise ValueError(f"parameter ordType should be one of the following: {ALLOWED_ORDER_TYPE}")

    if qty:
        validate_order_parameter_type("qty", qty)
        try_to_coerce_parameter_value("qty", qty)
    if price:
        validate_order_parameter_type("price", price)
        try_to_coerce_parameter_value("price", price)
    if stopPx:
        validate_order_parameter_type("stopPx", stopPx)
        try_to_coerce_parameter_value("stopPx", stopPx)

    if timeInForce:
        validate_order_parameter_type("timeInForce", timeInForce)
        if timeInForce not in ALLOWED_TIF:
            raise ValueError(f"parameter timeInForce should be one of the following: {ALLOWED_TIF}")

class TradeAPIRequester:
    def __init__(self, token:str, host:str=None):

        if host is None:
            host = "https://api.uat.btgpactualsolutions.com"
            print(f"WARNING: API host was not provided. Using default UAT host '{host}'")
        self.base_url = host + "/api/v1/order" # "https://api.uat.btgpactualsolutions.com/api/v1/order"
        self.headers = {
            "Authorization" : f"Bearer {token}"
        }

    # criar ordem
    def create_order(self, symbol:str, side:str, qty:str, account:str, execBroker:str, ordType:str, timeInForce:str, isDMA:str, entity:str, price:str, stopPx:str):
        
        validate_create_order_parameters(symbol, side, qty, account, execBroker, ordType, timeInForce, isDMA, entity, price, stopPx)

        body = {
            "symbol" : symbol,
            "side" : side,
            "qty" : qty,
            "account" : account,
            "execBroker" : execBroker,
            "ordType" : ordType,
            "timeInForce" : timeInForce,
            "isDMA" : isDMA,
            "entity" : entity,
        }

        if price: body["price"] = price
        if stopPx: body["stopPx"] = stopPx

        r = requests.post(self.base_url, headers=self.headers, json=body)

        if r.status_code not in [200, 202]:
            print(r.status_code)
            print(r.text)

        return r.json()

    # alterar ordem
    def update_order(self, id:str, ordType:str=None, qty:str=None, price:str=None, stopPx:str=None, timeInForce:str=None):

        validate_update_order_parameters(qty, price, stopPx, ordType, timeInForce)

        body = {
            "id": id,
            "ordType": ordType,
        }

        if qty: body["qty"] = qty
        if price: body["price"] = price
        if stopPx: body["stopPx"] = stopPx
        if timeInForce: body["timeInForce"] = timeInForce

        r = requests.put(self.base_url, headers=self.headers, json=body)

        if r.status_code not in [200, 202]:
            print(f"{r.status_code} - {r.text}")

        return r.json()

    # cancelar ordem por id
    def cancel_order(self, id:str):
        r = requests.delete(self.base_url + f"/{id}", headers=self.headers)

        if r.status_code not in [200, 202]:
            print(f"{r.status_code} - {r.text}")

        return r.json()

    # cancelar todas as ordens
    def cancel_all_orders(self):
        r = requests.delete(self.base_url + "/myorders", headers=self.headers)

        if r.status_code not in [200, 202, 204]:
            print(f"{r.status_code} - {r.text}")

        if r.status_code == 204:
            return r.text
        return r.json()

    # consultar todas as ordens
    def get_orders(self):
        r = requests.get(self.base_url, headers=self.headers)

        if r.status_code not in [200, 202]:
            print(f"{r.status_code} - {r.text}")

        return r.json()

    # consultar ordem por ID
    def get_order(self, id:str):
        r = requests.get(f"{self.base_url}/id/{id}", headers=self.headers)

        if r.status_code not in [200, 202]:
            print(f"{r.status_code} - {r.text}")
            raise Exception("Endpoint did not return expected response")

        return r.json()

class OrderController:
    """
    Instantiate an order controller. Provide your token, account number, execution broker and entity to start sending orders.

    >>> from btgsolutions_tradeservices import OrderController

    >>> controller = OrderController(
    >>>     token="YOUR_TOKEN",
    >>>     account="YOUR_ACCOUNT_NUMBER",
    >>>     exec_broker="YOUR_EXEC_BROKER",
    >>>     entity="YOUR_ENTITY",
    >>> )

    One can provide a custom order update callback function.

    >>> def order_update_callback(order):
    >>>     print(f"Order update: {order}")

    >>> controller = OrderController(
    >>>     token="YOUR_TOKEN",
    >>>     order_update_callback=order_update_callback,
    >>> )

    Parameters
    ----------------
    token: str
        User token.
        Field is required.
    order_api_host: str
        Order API host address. If not provided, default UAT host will be used.
        Field is not required.
    account: str
        Account.
        Field is not required.
    execBroker: str
        Execution broker.
        Field is not required.
    entity: str
        Associated entity.
        Field is not required.
    order_update_callback: Callable
        Order update callback function. If not provided, a generic callback function will be used.
        Field is not required.
    """
    def __init__(self, token:str, order_api_host:str=None, account:str=None, execBroker:str=None, entity:str=None, order_update_callback=None):

        if order_update_callback is None:
            self.order_update_callback = generic_update_callback
        else:
            self.order_update_callback = order_update_callback
        
        self.token = token

        self.account = account
        self.execBroker = execBroker
        self.entity = entity

        self.key_columns = ['clOrdId', 'symbol', 'side', 'qty', 'price', 'stopPx', 'ordStatus', 'text']

        self._t_api = TradeAPIRequester(token=token, host=order_api_host)

        self.daemon = Thread(target=_background_periodically_update_orders, args=(self,), daemon=True, name='order_updater')
        self.daemon.start()

    def create_order(self, symbol:str, side:str, qty:str, timeInForce:str, isDMA:str, price:str=None, stopPx:str=None, ordType:str=None, account:str=None, execBroker:str=None, entity:str=None):
        """
        Create new order

        >>> orderId = controller.create_order(
        >>>     symbol="PETR4",
        >>>     side="S",
        >>>     qty="5000",
        >>>     price="20.41",
        >>>     timeInForce="Day",
        >>>     isDMA="true"
        >>> )

        Parameters
        ----------------
        symbol: str
            Ticker symbol.
            Field is required.
        side: str
            Side of transaction.
            Allowed values: 'B', 'S'.
            Field is required.
        qty: str
            Number of units to transact.
            Field is required.
        timeInForce: str
            New order time in force (if applicable).
            Field is required.
        isDMA: str
            is DMA.
            Field is required.
        price: str
            New order price (if applicable).
            Field is not required.
        stopPx: str
            New order stop price (if applicable).
            Field is not required.
        ordType: str
            Order type.
            Field is required.
        account: str
            Account.
            Field is not required if it has already been provided at class instantiation.
        execBroker: str
            Execution broker.
            Field is not required if it has already been provided at class instantiation.
        entity: str
            Associated entity.
            Field is not required if it has already been provided at class instantiation.
        """

        if account is None: account = self.account
        if execBroker is None: execBroker = self.execBroker 
        if entity is None: entity = self.entity
        
        return self._t_api.create_order( 
            symbol=symbol,
            side=side,
            qty=qty,
            account=account,
            execBroker=execBroker,
            ordType=ordType,
            timeInForce=timeInForce,
            isDMA=isDMA,
            entity=entity,
            price=price,
            stopPx=stopPx,
        )
    
    def change_order(self, id:str, qty:str, price:str=None, stopPx:str=None, timeInForce:str=None, ordType:str=None):
        """
        Change an order

        >>> orderId = controller.create_order(
        >>>     id="YOUR_ORDER_ID",
        >>>     qty="5000",
        >>>     price="20.43",
        >>>     timeInForce="Day"
        >>> )

        Parameters
        ----------------
        id: str
            Order id.
            Field is required.
        qty: str
            New order quantity.
            Field is required.
        price: str
            New order price (if applicable).
            Field is not required.
        stopPx: str
            New order stop price (if applicable).
            Field is not required.
        timeInForce: str
            New order time in force (if applicable).
            Field is not required.
        ordType: str
            Order type.
            Field is not required.
        """
        id = id.split(':')[0]
        return self._t_api.update_order(
            id=id,
            ordType=ordType,
            qty=qty,
            price=price,
            stopPx=stopPx,
            timeInForce=timeInForce
        )
    
    def cancel_order(self, id:str):
        """
        Cancel an order

        >>> orderId = controller.cancel_order(
        >>>     id="YOUR_ORDER_ID",
        >>> )

        Parameters
        ----------------
        id: str
            Order id.
            Field is required.
        """
        id = id.split(':')[0]
        return self._t_api.cancel_order(id)

    def cancel_all_orders(self,):
        """
        Cancel all orders

        >>> controller.cancel_all_orders()
        """
        return self._t_api.cancel_all_orders()

    def get_order(self, id:str):
        """
        Retrieve an order status

        >>> orderStatus = controller.get_order(
        >>>     id="YOUR_ORDER_ID",
        >>> )

        Parameters
        ----------------
        id: str
            Order id.
            Field is required.
        """
        id = id.split(':')[0]
        return self._t_api.get_order(id)

    def get_orders(self):
        """
        Retrieve all order status

        >>> controller.get_orders()
        """
        return self._t_api.get_orders()
    
    def summary(self, detailed:bool=True):
        """
        Get a summary of all order status, in a Pandas DataFrame format.

        >>> summary = controller.summary()

        Parameters
        ----------------
        detailed: str
            If 'True', returns all status info about an order. If 'False', returns a summarized version.
            Field is not required.
        """
        res = self.get_orders()
        df = pd.DataFrame(res)
        
        if detailed is True:
            return df
        return df[df.columns[df.columns.isin(self.key_columns)]]
