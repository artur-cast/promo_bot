"""
Rode este script UMA VEZ para obter o refresh_token do Mercado Livre.
Depois disso, o bot renova o access_token sozinho — você não precisa rodar
isso de novo (a menos que revogue o acesso).

Como usar:
1. Preencha ML_CLIENT_ID, ML_CLIENT_SECRET e ML_REDIRECT_URI no .env
2. Rode: python oauth_setup_ml.py
3. Abra a URL impressa, faça login/autorize
4. Você será redirecionado para ML_REDIRECT_URI com ?code=XXXX na URL
5. Cole esse "code" quando o script pedir
6. O script vai imprimir o refresh_token — copie pro seu .env
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("ML_CLIENT_ID")
CLIENT_SECRET = os.getenv("ML_CLIENT_SECRET")
REDIRECT_URI = os.getenv("ML_REDIRECT_URI", "https://localhost")

AUTH_URL = (
    f"https://auth.mercadolivre.com.br/authorization"
    f"?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
)


def main():
    print("Abra esta URL no navegador, faça login e autorize o app:\n")
    print(AUTH_URL)
    print()
    code = input("Cole aqui o valor do parâmetro 'code' da URL de redirecionamento: ").strip()

    resp = requests.post(
        "https://api.mercadolibre.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    print("\nSucesso! Copie estes valores para o seu .env:\n")
    print(f"ML_ACCESS_TOKEN={data['access_token']}")
    print(f"ML_REFRESH_TOKEN={data['refresh_token']}")


if __name__ == "__main__":
    main()
