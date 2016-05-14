# eBayAPy
Python wrapper for the eBay API services.

eBay has many API services, the most common being the [Trading API.](http://developer.ebay.com/Devzone/XML/docs/reference/ebay/index.html)

To start using the eBayAPy:

```python
# eBay will provide you with the credentials when you register for the API.
trading = eBayAPI.Trading(auth_token=<YOUR-AUTH-TOKEN>,
                          app_id=<YOUR-APP-ID>,
                          cert_id=<YOUR-CERT-ID>,
                          dev_id=<YOUR-DEV-ID>)

eBay_orders = trading.GetOrders()
addResponse = trading.AddItem('XMLObject(check documentation)')
```
