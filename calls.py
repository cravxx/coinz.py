import requests

get_ticker = {
    'Bittrex': lambda market: requests.get("https://bittrex.com/api/v1.1/public/getticker?market=" + market).json(),
    'Binance': lambda market: requests.get("https://api.binance.com/api/v1/ticker/24hr?symbol=" + market).json()
}

get_last_price = {
    'Bittrex': lambda market, name: float(
        requests.get("https://bittrex.com/api/v1.1/public/getticker?market=" + market + \
                     "-" + name).json()["result"]["Last"]),
    'Binance': lambda market, name: float(
        requests.get("https://api.binance.com/api/v1/ticker/24hr?symbol=" + name.upper() \
                     + "" + market.upper()).json()["lastPrice"])
}
