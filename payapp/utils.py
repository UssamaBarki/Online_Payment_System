import requests

def fetch_exchange_rates(currency1, currency2, amount):
    """
    Calls the RESTful currency conversion API and retrieves the converted amount.
    Example API call: /conversion/USD/GBP/100/
    """
    url = f"https://0.0.0.0:8000/payapp/conversion/{currency1}/{currency2}/{amount}/"

    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            return data.get("converted_amount")
        else:
            return None
    except requests.exceptions.RequestException:
        return None