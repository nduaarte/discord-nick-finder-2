import requests
import random
import string
import time
import os
import redis

# ─────────────────────────────────────────
# CONFIGURAÇÃO — 4 CARACTERES, LETRAS E NÚMEROS
# ─────────────────────────────────────────
TAMANHO = 4
# Combina letras minúsculas (a-z) e números (0-9)
CHARS = string.ascii_lowercase + string.digits  
DELAY = 10.0

# Conexão Automática com o Redis do Railway para lembrar dos nicks já testados
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    db = redis.Redis.from_url(REDIS_URL, decode_responses=True)
else:
    db = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Lista de Proxies Fixas (Webshare)
PROXIES_LISTA = [
    # Suas proxies entram aqui...
]
# ─────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def gerar_senha():
    upper = random.choices(string.ascii_uppercase, k=4)
    lower = random.choices(string.ascii_lowercase, k=4)
    digits = random.choices(string.digits, k=4)
    special = random.choices("!@#$%^&*", k=4)
    all_chars = upper + lower + digits + special
    random.shuffle(all_chars)
    return "".join(all_chars)

def gerar_nick():
    return "".join(random.choices(CHARS, k=TAMANHO))

def verificar_disponibilidade(username, proxy_url=None):
    url = "https://discord.com/api/v9/auth/register"
    payload = {
        "username": username,
        "email": f"check_{random.randint(100000,999999)}@tempcheck.invalid",
        "password": gerar_senha(),
        "date_of_birth": "2000-01-01",
        "consent": True
    }
    
    proxies_config = None
    if proxy_url:
        socks_url = proxy_url.replace("http://", "socks5://")
        proxies_config = {
            "http": socks_url,
            "https": socks_url
        }

    try:
        r = requests.post(url, json=payload, headers=HEADERS, proxies=proxies_config, timeout=5)
        data = r.json()
        errors = str(data)

        if r.status_code == 200:
            return True
        elif "USERNAME_TOO_MANY_USERS" in errors or "username" in str(data.get("errors", {})):
            return False
        elif "email" in str(data.get("errors", {})) or "captcha" in errors.lower():
            return True
        elif r.status_code == 429:
            retry = float(r.headers.get("Retry-After", 5))
            origem = "no IP do Proxy" if proxy_url else "no seu IP Local"
            print(f"  ⚠️  Rate limit {origem}! (Bloqueio de {retry:.0f}s)", end="", flush=True)
            if not proxy_url:
                time.sleep(retry)
            return None
        else:
            return None
    except requests.RequestException:
        origem = "no proxy (SOCKS5)" if proxy_url else "na conexão local"
        print(f"  ❌ Erro de conexão {origem}", end="", flush=True)
        return None

def main():
    print("🎯 Discord Finder — 4 letras + Números | Logs do Railway", flush=True)
    print("=" * 50, flush=True)
    print(f"Caracteres: {CHARS}", flush=True)
    print(f"Combinações possíveis: {len(CHARS)**TAMANHO:,}", flush=True)
    print(f"⚙️  Usando proxies fixas da Webshare: {len(PROXIES_LISTA)}", flush=True)
    
    print("=" * 50, flush=True)
    print("🔗 Conectando ao Redis...", end="", flush=True)
    
    try:
        # Alterado para '4letras_num' para isolar os bancos
        total_testados_inicial = db.scard("discord:4letras_num:testados")
        total_achados_inicial = db.scard("discord:4letras_num:disponiveis")
        print(f" ✅ Conectado! {total_testados_inicial} conhecidos | {total_achados_inicial} já encontrados.", flush=True)
    except redis.RedisError as e:
        print(f"\n🚨 Erro crítico ao conectar no Redis: {e}", flush=True)
        return
        
    print("=" * 50, flush=True)
    print("🚀 Iniciando loop de testes...", flush=True)
    print()

    tentativas_sessao = 0

    while True:
        nick = gerar_nick()
        
        # Alterado para '4letras_num'
        if db.sismember("discord:4letras_num:testados", nick):
            continue
        
        print(f"[{tentativas_sessao+1:>5}] Testando: {nick} ... ", end="", flush=True)

        proxy_atual = random.choice(PROXIES_LISTA) if PROXIES_LISTA else None
        disponivel = verificar_disponibilidade(nick, proxy_atual)

        if disponivel is True:
            tentativas_sessao += 1
            print(" ✨🎉 ✅ DISPONÍVEL! ✅ 🎉✨", flush=True)
            # Alterado para '4letras_num'
            db.sadd("discord:4letras_num:testados", nick)
            db.sadd("discord:4letras_num:disponiveis", nick)
            time.sleep(DELAY)

        elif disponivel is False:
            tentativas_sessao += 1
            print(" ❌ ocupado", flush=True)
            # Alterado para '4letras_num'
            db.sadd("discord:4letras_num:testados", nick)
            time.sleep(DELAY)

        else:
            se_com_proxy = "e alternando proxy imediatamente..." if PROXIES_LISTA else "e aguardando rate limit..."
            print(f" -> 🔄 Pulando {se_com_proxy}", flush=True)

        if tentativas_sessao > 0 and tentativas_sessao % 10 == 0 and disponivel is not None:
            # Alterado para '4letras_num'
            total_geral = db.scard("discord:4letras_num:testados")
            total_sucessos = db.scard("discord:4letras_num:disponiveis")
            print(f"  📊 Progresso: {total_geral} testados | ⭐ {total_sucessos} DISPONÍVEIS salvos.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Parado pelo usuário.", flush=True)
