"""
Fonte de promoções via Awin.

Diferente do Mercado Livre e da Lomadee, a Awin não tem uma API de "busca"
simples — o acesso a produtos é feito por FEEDS (arquivos CSV) que cada loja
("advertiser"/"programme") disponibiliza, e você só consegue baixar o feed
de lojas que já te aprovaram como afiliado.

Fluxo:
1. Busca a lista de programas (lojas) que já te aprovaram (relationship=joined)
2. Para cada loja, pega a URL do feed de produtos (CSV)
3. Baixa e faz o parsing do CSV, convertendo pra Promo

IMPORTANTE: os nomes de campo padrão da Awin costumam ser:
aw_deep_link, product_name, aw_image_url, search_price, rrp_price
(rrp_price = preço "cheio" recomendado, usamos como original_price)
Mas cada loja pode customizar campos extras — o parsing abaixo ignora
campos desconhecidos e loga o cabeçalho do CSV na primeira execução, pra
você conferir se bate.
"""

import os
import csv
import io
import logging
import requests
from typing import List, Optional
from dotenv import load_dotenv

from scrapers.base import Promo

load_dotenv()
log = logging.getLogger("promo_bot.awin")

API_TOKEN = os.getenv("AWIN_API_TOKEN")
PUBLISHER_ID = os.getenv("AWIN_PUBLISHER_ID")

BASE_URL = "https://api.awin.com"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# Limite de linhas lidas por feed, pra não sobrecarregar o celular
MAX_ROWS_PER_FEED = 300
# Quantas lojas (programas) processar por checagem, pra não demorar demais
MAX_PROGRAMMES = 5

_debug_header_printed = False


def _get_joined_programmes() -> List[dict]:
    resp = requests.get(
        f"{BASE_URL}/publishers/{PUBLISHER_ID}/programmes",
        headers=HEADERS,
        params={"relationship": "joined"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def _get_feed_url(advertiser_id: str) -> Optional[str]:
    resp = requests.get(
        f"{BASE_URL}/publishers/{PUBLISHER_ID}/programmes/{advertiser_id}/datafeeds",
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    feeds = resp.json()
    if not feeds:
        return None
    # Pega o primeiro feed disponível (geralmente só tem um por loja)
    return feeds[0].get("url") or feeds[0].get("feedUrl")


def _parse_feed(feed_url: str, store_name: str) -> List[Promo]:
    global _debug_header_printed
    promos = []

    resp = requests.get(feed_url, timeout=30, stream=True)
    resp.raise_for_status()

    # Feeds da Awin costumam vir em CSV separado por tab ou vírgula.
    # Detecta automaticamente com o Sniffer; se falhar, assume tab (padrão Awin).
    sample = resp.raw.read(4096).decode("utf-8", errors="ignore")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel_tab

    full_text = sample + resp.text
    reader = csv.DictReader(io.StringIO(full_text), dialect=dialect)

    if not _debug_header_printed:
        log.info(f"[awin] Cabeçalho do feed de {store_name}: {reader.fieldnames}")
        _debug_header_printed = True

    for i, row in enumerate(reader):
        if i >= MAX_ROWS_PER_FEED:
            break
        try:
            price = float(row.get("search_price") or row.get("store_price") or 0)
            original_price_raw = row.get("rrp_price") or row.get("base_price")
            original_price = float(original_price_raw) if original_price_raw else None

            if not price or not original_price or original_price <= price:
                continue  # sem desconto real, ignora

            discount_percent = round((1 - price / original_price) * 100)

            product_id = row.get("aw_product_id") or row.get("merchant_product_id")
            if not product_id:
                continue

            promos.append(Promo(
                product_id=f"awin-{product_id}",
                title=row.get("product_name", "Produto"),
                price=price,
                original_price=original_price,
                discount_percent=discount_percent,
                coupon=row.get("promotional_code") or None,
                image_url=row.get("aw_image_url") or row.get("merchant_image_url", ""),
                product_url=row.get("aw_deep_link") or row.get("merchant_deep_link", ""),
                store=store_name,
            ))
        except Exception as e:
            log.warning(f"[awin] Linha ignorada por erro de parsing: {e}")

    return promos


def fetch_promos_awin() -> List[Promo]:
    if not API_TOKEN or not PUBLISHER_ID:
        log.error("[awin] AWIN_API_TOKEN ou AWIN_PUBLISHER_ID não configurados")
        return []

    promos = []
    try:
        programmes = _get_joined_programmes()
    except Exception as e:
        log.error(f"[awin] Erro ao buscar programas aprovados: {e}")
        return []

    for programme in programmes[:MAX_PROGRAMMES]:
        advertiser_id = programme.get("id")
        store_name = programme.get("name", "Loja parceira Awin")
        try:
            feed_url = _get_feed_url(advertiser_id)
            if not feed_url:
                continue
            promos.extend(_parse_feed(feed_url, store_name))
        except Exception as e:
            log.error(f"[awin] Erro processando loja {store_name}: {e}")

    return promos
