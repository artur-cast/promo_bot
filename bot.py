import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import telebot
from apscheduler.schedulers.background import BackgroundScheduler

from config import BOT_TOKEN, CHAT_ID, CHECK_INTERVAL_MINUTES, MIN_DISCOUNT_PERCENT
from database import init_db, already_sent, mark_as_sent
from scrapers.mercado_livre import fetch_promos_ml
from scrapers.example_source import fetch_promos_mock

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("promo_bot")

bot = telebot.TeleBot(BOT_TOKEN)

START_TIME = datetime.now()

# Estado simples em memória pra alimentar o /status. Some quando o processo
# reinicia — não precisa persistir, é só um retrato do momento atual.
stats = {
    "last_check": None,
    "total_sent": 0,
    "last_source_results": {},
    "last_source_errors": {},
}

# ---------------------------------------------------------------------------
# Registro de fontes: cada fonte é uma função que retorna List[Promo].
# Pra adicionar uma nova API, implemente scrapers/nova_fonte.py com uma
# função fetch_promos_x() e adicione aqui na lista.
# ---------------------------------------------------------------------------
SOURCES = [
    ("mercado_livre", fetch_promos_ml),
    ("mock", fetch_promos_mock),  # remova depois que tiver fontes reais suficientes
]


def run_source(name: str, fetch_fn):
    """Roda uma fonte isoladamente. Se ela falhar, não derruba as outras."""
    try:
        promos = fetch_fn()
        log.info(f"[{name}] {len(promos)} promoções encontradas")
        stats["last_source_results"][name] = len(promos)
        stats["last_source_errors"].pop(name, None)
        return promos
    except Exception as e:
        log.error(f"[{name}] falhou: {e}")
        stats["last_source_errors"][name] = str(e)
        return []


def check_and_send_promos():
    log.info("Buscando novas promoções em todas as fontes...")

    all_promos = []
    # Roda todas as fontes em paralelo (threads), já que são funções
    # bloqueantes (usam requests por baixo)
    with ThreadPoolExecutor(max_workers=len(SOURCES) or 1) as executor:
        futures = {executor.submit(run_source, name, fn): name for name, fn in SOURCES}
        for future in as_completed(futures):
            all_promos.extend(future.result())

    stats["last_check"] = datetime.now()

    for promo in all_promos:
        if promo.discount_percent and promo.discount_percent < MIN_DISCOUNT_PERCENT:
            continue

        if already_sent(promo.product_id):
            continue

        try:
            bot.send_photo(
                chat_id=CHAT_ID,
                photo=promo.image_url,
                caption=promo.caption(),
                parse_mode="Markdown",
            )
            mark_as_sent(promo.product_id, promo.title, promo.price)
            stats["total_sent"] += 1
            log.info(f"Alerta enviado: {promo.title}")
        except Exception as e:
            log.error(f"Erro ao enviar promoção {promo.product_id}: {e}")

        time.sleep(1)  # evita rate limit do Telegram


def _format_timedelta(td) -> str:
    total_seconds = int(td.total_seconds())
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}min")
    return " ".join(parts)


@bot.message_handler(commands=["status"])
def status_handler(message):
    """Responde com um resumo de saúde do bot. Funciona em DM ou no grupo."""
    uptime = _format_timedelta(datetime.now() - START_TIME)

    if stats["last_check"]:
        last_check_str = stats["last_check"].strftime("%d/%m %H:%M:%S")
        since_check = _format_timedelta(datetime.now() - stats["last_check"])
    else:
        last_check_str = "ainda não rodou"
        since_check = "-"

    lines = [
        "🤖 *Status do bot*",
        "",
        f"⏱️ Online há: {uptime}",
        f"🔎 Última checagem: {last_check_str} (há {since_check})",
        f"📨 Alertas enviados (desde o último start): {stats['total_sent']}",
        f"⏭️ Próxima checagem em até: {CHECK_INTERVAL_MINUTES}min",
        "",
        "*Fontes:*",
    ]

    for name, _ in SOURCES:
        if name in stats["last_source_errors"]:
            lines.append(f"❌ {name}: erro — {stats['last_source_errors'][name]}")
        elif name in stats["last_source_results"]:
            lines.append(f"✅ {name}: {stats['last_source_results'][name]} promoções na última busca")
        else:
            lines.append(f"⏳ {name}: ainda sem dados")

    bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")


def main():
    init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_send_promos, "interval", minutes=CHECK_INTERVAL_MINUTES)
    scheduler.start()

    log.info("Bot iniciado. Rodando primeira checagem imediatamente...")
    check_and_send_promos()

    log.info("Iniciando polling do Telegram...")
    # infinity_polling já reconecta sozinho em caso de queda de internet,
    # com backoff progressivo entre tentativas — não precisa de loop manual.
    bot.infinity_polling(timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    main()
