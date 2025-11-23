from playwright.sync_api import sync_playwright
from typing import Dict, List
from datetime import datetime
from .base import *


class KayakScraper(BaseScraper):
    DEFAULT_SELETORES_CARDS = {
        "companhia": "div.J0g6-operator-text",
        "data": "div.tdCx-bottom",
        "horario_saida": "div.VY2U > div.vmXl.vmXl-mod-variant-large > span:nth-child(1)",
        "horario_chegada": "div.VY2U > div.vmXl.vmXl-mod-variant-large > span:nth-child(3)",
        "aeroportos": "div.EFvI",
        "aeroportos_de_escala": "div.JWEO > div.vmXl.vmXl-mod-variant-default",
        "detalhe_escalas": "div.JWEO > div.c_cgF.c_cgF-mod-variant-full-airport.c_cgF-mod-theme-foreground-neutral",
        "duracao": "div.xdW8.xdW8-mod-full-airport > div.vmXl.vmXl-mod-variant-default",
        "preco_individual": "div.e2GB-price-text",
        "preco_total": "div.f8F1-small-emph.f8F1-multiple-ptc-price-label",
        "classe": "div.DOum-name",
    }

    DEFAULT_SELETORES = {
        "espera": ".Fxw9-result-item-container",
        "cards": f".nrc6.nrc6-mod-pres-default.nrc6-mod-desktop-responsive:has({DEFAULT_SELETORES_CARDS['preco_total']})",
    }

    def scrape(self) -> List[Dict[str, str]]:
        with sync_playwright() as p:
            # Abre o navegador e cria uma nova página
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            info_cards: List[Dict[str, str]] = []

            try:
                info_inicial = {
                    # DD/MM/AAAA
                    "dia_pesquisa": datetime.now().strftime("%d/%m/%Y"),
                    # HH:MM
                    "horario_pesquisa": datetime.now().strftime("%H:%M"),
                }
                page.goto(self.link)
                # Aguarda pelo container principal
                page.wait_for_selector(self.DEFAULT_SELETORES["espera"])
                # Pega os cards das ofertas de passagens
                cards_locator = page.locator(self.DEFAULT_SELETORES["cards"])
                n_cards = cards_locator.count()
                if n_cards > self.numero_maximo_de_ofertas:
                    n_cards = self.numero_maximo_de_ofertas
                # Percorre cada card e pega suas informações
                for i in range(n_cards):
                    card = cards_locator.nth(i)
                    # Cria um novo dicionário por card
                    info = info_inicial.copy()

                    for chave, seletor in self.DEFAULT_SELETORES_CARDS.items():
                        texto = card.locator(seletor).first.text_content()
                        info[chave] = self.limpar(texto)

                    info_cards.append(info)

            finally:
                browser.close()

            return info_cards
