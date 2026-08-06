#!/data/data/com.termux/files/usr/bin/sh
#
# Script de inicialização do bot no Termux (Android).
#
# Faz duas coisas:
# 1. Ativa o wake-lock: impede o Android de suspender o Termux em segundo
#    plano (sem isso, o sistema mata o processo depois de um tempo com a
#    tela apagada, mesmo com "sem restrições de bateria").
# 2. Loop de restart: se o processo Python morrer por qualquer motivo
#    (crash, OOM killer do Android, etc), reinicia sozinho depois de alguns
#    segundos, em vez de deixar o bot parado até você notar.
#
# O próprio bot.py já trata quedas de rede reconectando sozinho (com
# backoff). Este script aqui é uma camada extra: cobre o caso do PROCESSO
# inteiro morrer, não só a conexão.

termux-wake-lock

cd /data/data/com.termux/files/home/promo_bot || exit 1

LOG_FILE="bot.log"

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando o bot..." >> "$LOG_FILE"

    python bot.py >> "$LOG_FILE" 2>&1

    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot encerrou (código $EXIT_CODE). Reiniciando em 10s..." >> "$LOG_FILE"
    sleep 10
done
