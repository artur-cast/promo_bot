"""
Este arquivo é o ponto que você precisa adaptar pra fonte real de promoções.

Cada fonte (Awin, AliExpress, Amazon PA-API, scraping) deve implementar uma função
`fetch_promos()` que retorna uma lista de objetos Promo.

Abaixo tem:
1. Um exemplo MOCK (dados falsos) só pra você testar o bot end-to-end AGORA.
2. Um esqueleto comentado de como ficaria com uma API real (requests).
"""

from typing import List
from scrapers.base import Promo


def fetch_promos_mock() -> List[Promo]:
    """Dados falsos só pra testar o fluxo do bot sem depender de API externa."""
    return [
        Promo(
            product_id="mock-001",
            title="Fone Bluetooth XYZ",
            price=89.90,
            original_price=149.90,
            discount_percent=40,
            coupon="FONE40",
            image_url="https://picsum.photos/seed/fone/500/500",
            product_url="https://example.com/produto/fone-xyz",
            store="Loja Exemplo",
        ),
    ]


# ---------------------------------------------------------------------------
# Exemplo de como ficaria com uma API real (ex: Awin). Ajuste os campos
# conforme a documentação da API que você escolher.
# ---------------------------------------------------------------------------
#
# import requests
#
# AWIN_API_TOKEN = "seu_token_aqui"
# AWIN_FEED_URL = "https://api.awin.com/publishers/SEU_ID/feed"
#
# def fetch_promos_awin() -> List[Promo]:
#     resp = requests.get(
#         AWIN_FEED_URL,
#         headers={"Authorization": f"Bearer {AWIN_API_TOKEN}"},
#         params={"discount_min": 20},
#     )
#     resp.raise_for_status()
#     data = resp.json()
#
#     promos = []
#     for item in data["products"]:
#         promos.append(Promo(
#             product_id=str(item["id"]),
#             title=item["product_name"],
#             price=float(item["search_price"]),
#             original_price=float(item.get("rrp_price", 0)) or None,
#             discount_percent=item.get("discount_percent"),
#             coupon=item.get("promotional_code"),
#             image_url=item["aw_image_url"],
#             product_url=item["aw_deep_link"],
#             store=item["merchant_name"],
#         ))
#     return promos
