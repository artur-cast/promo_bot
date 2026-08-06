# Promo Bot — Alertas de promoções no Telegram

## Como rodar localmente

```bash
# 1. Criar ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# edite o .env com seu BOT_TOKEN e CHAT_ID

# 4. Rodar
python bot.py
```

Isso já vai postar no grupo usando os dados MOCK (fake), só pra validar
que o fluxo (agendamento → filtro → envio) está funcionando.

## Próximos passos

1. **Trocar a fonte de dados**: edite `scrapers/example_source.py` (ou crie um
   novo arquivo em `scrapers/`) implementando a busca real via API de afiliados
   (Awin, Lomadee, AliExpress, Amazon PA-API). Depois troque o import em `bot.py`:
   ```python
   from scrapers.sua_fonte import fetch_promos_real as fetch_promos_mock
   ```
2. **Ajustar filtros**: `MIN_DISCOUNT_PERCENT` no `.env` controla o desconto mínimo.
3. **Múltiplas fontes**: você pode chamar várias funções `fetch_promos_*()` dentro
   de `check_and_send_promos()` e juntar os resultados numa lista só.

## Hospedagem

- **Teste rápido/grátis**: Railway ou Render (free tier) — suba o repo, defina
  as variáveis de ambiente no painel, comando de start `python bot.py`.
- **Celular Android parado**: veja a seção "Rodando no Termux (Android)" abaixo.
- **Produção**: VPS (Hetzner/Contabo) rodando com `systemd`:
  ```ini
  # /etc/systemd/system/promo_bot.service
  [Unit]
  Description=Promo Bot Telegram
  After=network.target

  [Service]
  WorkingDirectory=/caminho/para/promo_bot
  ExecStart=/caminho/para/promo_bot/venv/bin/python bot.py
  Restart=always
  User=seu_usuario

  [Install]
  WantedBy=multi-user.target
  ```
  Depois: `sudo systemctl enable --now promo_bot`

## Rodando no Termux (Android)

Transforma um celular parado em um "servidor" 24/7 pro bot.

### 1. Preparar o celular
- Deixe sempre carregando e conectado ao Wi-Fi
- Configurações → Apps → Termux → Bateria → "Sem restrições"

### 2. Instalar
Instale **Termux** e **Termux:Boot** pelo [F-Droid](https://f-droid.org)
(não use a versão da Play Store, está desatualizada).

```bash
pkg update && pkg upgrade
pkg install python git termux-api
git clone https://github.com/seu-usuario/promo_bot.git
cd promo_bot
pip install -r requirements.txt
cp .env.example .env
nano .env   # preencha os tokens
```

### 3. Rodar com proteção contra queda de rede e de processo
```bash
chmod +x run.sh
./run.sh
```
O `run.sh` ativa o wake-lock (impede o Android de suspender o processo) e
reinicia o bot automaticamente se ele cair por qualquer motivo. O `bot.py`
por si só já reconecta sozinho em caso de queda de internet, com backoff
progressivo — o `run.sh` cobre o caso do processo inteiro morrer.

Pra rodar em segundo plano e poder fechar o app do Termux:
```bash
pkg install tmux
tmux new -s promobot
./run.sh
# Ctrl+B, depois D pra "sair" sem matar o processo
# tmux attach -t promobot para voltar a ver os logs
```

### 4. Iniciar sozinho ao ligar o celular
Com o Termux:Boot instalado:
```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_bot.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
cd /data/data/com.termux/files/home/promo_bot
./run.sh
EOF
chmod +x ~/.termux/boot/start_bot.sh
```
Agora, se o celular reiniciar (queda de luz, atualização do sistema etc), o
bot volta a rodar sozinho.

### Acompanhar os logs
```bash
tail -f bot.log
```

## Estrutura do projeto

```
promo_bot/
├── bot.py                  # ponto de entrada, agendamento e envio
├── config.py                # variáveis de configuração
├── database.py               # controle de promoções já enviadas (SQLite)
├── scrapers/
│   ├── base.py               # modelo padrão Promo
│   └── example_source.py     # fonte mock + esqueleto de fonte real
├── requirements.txt
└── .env.example
```
