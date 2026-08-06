"""
Fonte de promoções via API do Mercado Livre.

Estratégia: busca itens de categorias específicas ordenados por maior
desconto, usando o parâmetro `sort=promotional` / filtro de desconto
disponível na busca pública autenticada.

IMPORTANTE: a geração do link de AFILIADO em si (com sua comissão) não tem
API pública — você gera manualmente no painel de afiliados e substitui o
domínio, OU usa a ferramenta de "encurtador" deles colando a URL do produto.
Por isso, `product_url` aqui traz o link normal do produto; o TODO abaixo
mostra onde plugar a conversão pro link de afiliado.
"""

import os
import time
import requests
from typing import List, Optional
from dotenv import load_dotenv

from scrapers.base import Promo

load_dotenv()

CLIENT_ID = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("ML_REFRESH_TOKEN")

SITE_ID = "MLB"  # MLB = Brasil

_token_cache = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Retorna um access_token válido, renovando via refresh_token se preciso."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    resp = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    # renova um pouco antes de expirar de verdade (margem de 60s)
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60

    # Nota: o Mercado Livre pode rotacionar o refresh_token a cada uso.
    # Se isso acontecer no seu app, salve data.get("refresh_token") de volta
    # no seu armazenamento de configuração.

    return _token_cache["access_token"]


def _search_category(category_id: str, limit: int = 20) -> List[dict]:
    token = _get_access_token()
    resp = requests.get(
        f"https://api.mercadolibre.com/sites/{SITE_ID}/search",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "category": category_id,
            "sort": "price_asc",  # ajuste conforme o que quer priorizar
            "limit": limit,
        },
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def _to_promo(item: dict) -> Optional[Promo]:
    price = item.get("price")
    original_price = item.get("original_price")  # só vem quando está em promoção

    if not original_price or original_price <= price:
        return None  # sem desconto real, ignora

    discount_percent = round((1 - price / original_price) * 100)

    thumbnail = item.get("thumbnail", "").replace("http://", "https://")

    return Promo(
        product_id=f"ml-{item['id']}",
        title=item["title"],
        price=price,
        original_price=original_price,
        discount_percent=discount_percent,
        coupon=None,  # ML raramente expõe cupom via API; geralmente é desconto direto
        image_url=thumbnail,
        # TODO: trocar por link de afiliado depois de aprovado no programa
        product_url=item["permalink"],
        store="Mercado Livre",
    )


# Categorias de exemplo (você pode ver a lista completa em
# https://api.mercadolibre.com/sites/MLB/categories)
CATEGORIES = {
    "eletronicos": "MLB1000",
    "celulares": "MLB1051",
    "informatica": "MLB1648",
}


def fetch_promos_ml() -> List[Promo]:
    promos = []
    for name, category_id in CATEGORIES.items():
        try:
            items = _search_category(category_id)
            for item in items:
                promo = _to_promo(item)
                if promo:
                    promos.append(promo)
        except Exception as e:
            print(f"[ML] Erro buscando categoria {name}: {e}")
    return promos
