from decimal import Decimal, InvalidOperation

import requests
from django.core.cache import cache
from rest_framework.exceptions import ValidationError


API_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
CACHE_KEY = "cbu_currency_rates"
CACHE_TIMEOUT = 60 * 60


def get_exchange_rate_to_uzs(currency):
    """
    Markaziy bank API orqali valyuta kursini oladi.
    """

    currency = currency.upper()

    # So'mni so'mga aylantirish kursi 1 ga teng.
    if currency == "UZS":
        return Decimal("1.0000")

    # Oldin API dan olingan kurs saqlanganmi, tekshiramiz.
    cached_rates = cache.get(CACHE_KEY)

    if cached_rates is not None:
        if currency in cached_rates:
            return Decimal(cached_rates[currency])

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError):
        raise ValidationError({
            "currency": "Markaziy bank API dan valyuta kursini olib bo'lmadi."
        })

    rates = {}

    # API qaytargan valyutalarni ko'rib chiqamiz.
    for item in data:
        code = item.get("Ccy")

        try:
            rate = Decimal(str(item["Rate"]))
            nominal = Decimal(str(item.get("Nominal", "1")))

            if code and nominal > 0 and rate > 0:
                rates[code] = str(rate / nominal)

        except (KeyError, TypeError, InvalidOperation):
            continue

    if not rates:
        raise ValidationError({
            "currency": "Markaziy bank API dan kurslar olinmadi."
        })

    # Barcha valyuta kurslarini bir soatga saqlaymiz.
    cache.set(CACHE_KEY, rates, CACHE_TIMEOUT)

    if currency not in rates:
        raise ValidationError({
            "currency": f"{currency} valyutasi API da topilmadi."
        })

    return Decimal(rates[currency])