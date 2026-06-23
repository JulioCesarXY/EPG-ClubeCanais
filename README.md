# 📺 EPG & IPTV Scraper - Clube Canais

[![Atualizar Lista M3U](https://github.com/JulioCesarXY/EPG-ClubeCanais/actions/workflows/main.yml/badge.svg)](https://github.com/JulioCesarXY/EPG-ClubeCanais/actions/workflows/main.yml)

Este repositório contém um script de automação assíncrona em Python que realiza a raspagem (scraping) de canais públicos do site Clube Canais. Utilizando **Playwright** para emulação de navegador e interceptação de tráfego de rede, o script gera automaticamente uma lista no formato `.m3u` com logotipos e categorias organizadas.

A atualização é 100% automatizada através do **GitHub Actions**, rodando todos os dias na nuvem de forma totalmente independente.

---

## 🚀 Como usar a Lista no seu Player IPTV

Para utilizar a lista gerada por este projeto no seu player favorito (como IPTV Smarters, VLC, Perfect Player ou Tivimate), basta copiar o link **Raw** público abaixo e colar na configuração de listas (URL M3U) do seu aplicativo:

```text
https://raw.githubusercontent.com/JulioCesarXY/EPG-ClubeCanais/main/clube_canais_playwright.m3u

```
