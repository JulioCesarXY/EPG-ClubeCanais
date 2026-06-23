import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

BASE_URL = "https://clubecanais.com.br"
NOME_ARQUIVO_M3U = "clube_canais_playwright.m3u"

async def extrair_tudo():
    async with async_playwright() as p:
        # Lança o Chromium em modo headless (sem interface gráfica)
        browser = await p.chromium.launch(headless=True)
        # Configura um User-Agent de desktop comum para evitar bloqueios simples
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print("[1] Acessando a Home para ler as categorias...")
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        html_home = await page.content()
        soup_home = BeautifulSoup(html_home, 'html.parser')
        
        select_cat = soup_home.find('select', {'name': 'category'})
        if not select_cat:
            print("[!] Não foi possível encontrar as categorias.")
            await browser.close()
            return

        categorias = []
        for option in select_cat.find_all('option'):
            cat_id = option.get('value')
            if cat_id and cat_id != "0":
                categorias.append((cat_id, option.text.replace("-", "").strip()))

        banco_canais = {}

        print(f"[2] Varrendo {len(categorias)} categorias para mapear os canais...")
        for cat_id, cat_nome in categorias:
            url_filtro = f"{BASE_URL}/index.php?category={cat_id}"
            await page.goto(url_filtro, wait_until="domcontentloaded")
            html_cat = await page.content()
            soup_cat = BeautifulSoup(html_cat, 'html.parser')

            links = soup_cat.find_all('a', href=re.compile(r'channel\.php\?id=\d+'))
            for link in links:
                match = re.search(r'id=(\d+)', link['href'])
                if match:
                    canal_id = match.group(1)
                    img_tag = link.find('img')
                    logo_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else ""
                    if logo_url.startswith('/'):
                        logo_url = BASE_URL + logo_url

                    linhas = [l.strip() for l in link.get_text().split('\n') if l.strip()]
                    nome_canal = linhas[0] if linhas else f"Canal {canal_id}"

                    banco_canais[canal_id] = {
                        "id": canal_id,
                        "nome": nome_canal,
                        "logo": logo_url,
                        "categoria": cat_nome,
                        "stream": None
                    }

        print(f"-> Total de {len(banco_canais)} canais mapeados. Iniciando extração dos streams...")

        # [3] Extração dos streams abrindo canal por canal e interagindo
        lista_m3u = ["#EXTM3U\n"]
        contador = 0

        for canal_id, canal_info in banco_canais.items():
            contador += 1
            url_canal = f"{BASE_URL}/channel.php?id={canal_id}"
            stream_encontrado = None

            # Função interna para monitorar e capturar links .m3u8 trafegados na rede
            def interceptar_resposta(response):
                nonlocal stream_encontrado
                url = response.url
                if ".m3u8" in url.lower() or "stream" in url.lower():
                    stream_encontrado = url

            page.on("response", interceptar_resposta)

            try:
                await page.goto(url_canal, wait_until="domcontentloaded")
                
                # Força o clique no botão de Iniciar (btnPlay) para disparar o player JS
                btn_play = page.locator("#btnPlay")
                if await btn_play.count() > 0:
                    await btn_play.click()
                    # Aguarda até 3 segundos para a rede carregar o vídeo
                    await page.wait_for_timeout(3000)

                # Se capturou pela rede ou se já estava no HTML, salva
                if stream_encontrado:
                    canal_info["stream"] = stream_encontrado
                else:
                    # Fallback: tenta ler o HTML caso o link já estivesse lá de forma estática
                    html_canal = await page.content()
                    links_m3u8 = re.findall(r"https?://[^\s\"']+\.m3u8[^\s\"']*", html_canal)
                    if links_m3u8:
                        canal_info["stream"] = links_m3u8[0].replace('\\/', '/')

                if canal_info["stream"]:
                    print(f"[{contador}/{len(banco_canais)}] [OK] {canal_info['nome']}")
                    lista_m3u.append(f'#EXTINF:-1 tvg-id="{canal_info["id"]}" tvg-name="{canal_info["nome"]}" tvg-logo="{canal_info["logo"]}" group-title="{canal_info["categoria"]}",{canal_info["nome"]}\n')
                    lista_m3u.append(f'{canal_info["stream"]}\n')
                else:
                    print(f"[{contador}/{len(banco_canais)}] [FALHA] {canal_info['nome']}")

            except Exception as e:
                print(f"[{contador}/{len(banco_canais)}] [ERRO] {canal_info['nome']}: {e}")

            # Remove o listener para o próximo canal
            page.remove_listener("response", interceptar_resposta)

        # Grava os resultados
        with open(NOME_ARQUIVO_M3U, "w", encoding="utf-8") as f:
            f.writelines(lista_m3u)

        print(f"\nProcesso concluído! Arquivo '{NOME_ARQUIVO_M3U}' gerado.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(extrair_tudo())
