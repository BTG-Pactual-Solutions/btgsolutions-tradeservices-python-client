# BTG Solutions Trade API package

BTG solutions trade api package.


## Usage

Get your token and use it in the examples below.

> Instantiate an order controller. Provide your token, account number, execution broker and entity to start sending orders.

```Python
controller = OrderController(
    token=token,
    account="YOUR_ACCOUNT_NUMBER",
    exec_broker="YOUR_EXEC_BROKER",
    entity="YOUR_ENTITY",
)
```

> One can provide a custom order update callback function.

```Python
def order_update_callback(order):
    print(f"Order update: {order}")

controller = OrderController(
    token=token,
    account="YOUR_ACCOUNT_NUMBER",
    exec_broker="YOUR_EXEC_BROKER",
    entity="YOUR_ENTITY",
    order_update_callback=order_update_callback,
)
```

> Create an order and receive the resulting order ID.

```Python
orderId = controller.create_order(
    symbol="PETR4",
    side="S",
    qty="5000",
    price="20.41",
    timeInForce="Day",
    isDMA="true"
)
```
> Change order.

```Python
controller.change_order(
    id="YOUR_ORDER_ID",
    qty="5000",
    price="20.43",
    timeInForce="Day"
)
```

> Cancel order.

```Python
controller.cancel_order(
    id="YOUR_ORDER_ID",
)
```

> Get a summary of all your orders.

```Python
controller.summary()
```

## Support

Get help at support@btgpactualsolutions.com