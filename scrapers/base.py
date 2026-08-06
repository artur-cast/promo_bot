from dataclasses import dataclass
from typing import Optional


@dataclass
class Promo:
    """Representa uma promoção de forma padronizada, não importa a fonte."""
    product_id: str          # ID único do produto (usado pra não repetir alertas)
    title: str
    price: float
    original_price: Optional[float]
    discount_percent: Optional[int]
    coupon: Optional[str]    # código do cupom, se houver
    image_url: str
    product_url: str
    store: str

    def caption(self) -> str:
        lines = [f"🔥 *{self.title}*", ""]
        if self.original_price:
            lines.append(f"~De R$ {self.original_price:.2f}~")
        lines.append(f"💰 *Por R$ {self.price:.2f}*")
        if self.discount_percent:
            lines.append(f"📉 {self.discount_percent}% OFF")
        if self.coupon:
            lines.append(f"🏷️ Cupom: `{self.coupon}`")
        lines.append(f"🏬 {self.store}")
        lines.append(f"\n👉 [Ver oferta]({self.product_url})")
        return "\n".join(lines)
