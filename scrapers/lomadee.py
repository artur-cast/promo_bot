"""
Fonte de promoções via API da Lomadee (developer.lomadee.com).

Bem mais simples que a do Mercado Livre: não usa OAuth, só um app-token fixo
+ sourceId, passados direto na URL/query string.

IMPORTANTE — leia antes de rodar:
A Lomadee não documenta publicamente (de forma estável) os nomes exatos de
todos os campos retornados no JSON de cada oferta, e isso pode variar um
pouco. Por isso, na primeira execução, esta função imprime o JSON bruto do
primeiro item retornado nos logs — use isso pra confirmar se os nomes de
campo abaixo (price, thumbnail, link etc) batem com o que a API está
realmente devolvendo, e ajuste se precisar.
"""

import os
import logging
import requests
from typing import List, Optional
from dotenv import load_dotenv

from scrapers.base import Promo

load_dotenv()
log = logging.getLogger("promo_bot.lomadee")

APP_TOKEN = os.getenv("LOMADEE_APP_TOKEN")
SOURCE_ID = os.getenv("LOMADEE_SOURCE_ID")

BASE_URL = f"https://api.lomadee.com/v2/{APP_TOKEN}"

# Já printamos o JSON bruto uma vez só, pra não poluir o log a cada checagem
_debug_printed = False


def _to_promo(item: dict) -> Optional[Promo]:
    global _debug_printed
    if not _debug_printed:
        log.info(f"[lomadee] Exemplo de item bruto da API: {item}")
        _debug_printed = True

    try:
        price = float(item.get("price") or item.get("priceFrom") or 0)
        original_price_raw = item.get("priceFrom") or item.get("originalPrice")
        original_price = float(original_price_raw) if original_price_raw else None

        if not price:
            return None

        discount_percent = None
        if original_price and original_price > price:
            discount_percent = round((1 - price / original_price) * 100)

        store_name = ""
        if isinstance(item.get("store"), dict):
            store_name = item["store"].get("name", "")
        else:
            store_name = item.get("storeName", "Loja parceira")

        return Promo(
            product_id=f"lomadee-{item.get('id') or item.get('productId')}",
            title=item.get("name") or item.get("productName", "Produto"),
            price=price,
            original_price=original_price,
            discount_percent=discount_percent,
            coupon=item.get("coupon"),
            image_url=item.get("thumbnail") or item.get("image", ""),
            product_url=item.get("link") or item.get("url", ""),
            store=store_name or "Loja parceira",
        )
    except Exception as e:
        log.warning(f"[lomadee] Item ignorado por erro de parsing: {e} | item={item}")
        return None


def fetch_promos_lomadee() -> List[Promo]:
    if not APP_TOKEN or not SOURCE_ID:
        log.error("[lomadee] LOMADEE_APP_TOKEN ou LOMADEE_SOURCE_ID não configurados")
        return []

    promos = []
    try:
        resp = requests.get(
            f"{BASE_URL}/offer/_bestsellers",
            params={"sourceId": SOURCE_ID},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # A resposta costuma vir dentro de uma chave "offers" -> "offer",
        # mas isso pode variar; tratamos os formatos mais prováveis.
        items = (
            data.get("offers", {}).get("offer")
            if isinstance(data.get("offers"), dict)
            else data.get("offers") or data.get("items") or []
        )

        for item in items:
            promo = _to_promo(item)
            if promo:
                promos.append(promo)

    except Exception as e:
        log.error(f"[lomadee] Erro na busca: {e}")

    return promos
