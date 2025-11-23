from playwright.sync_api import sync_playwright
from typing import Dict, List
from datetime import datetime
from .base import *


class FlipMilhasScraper(BaseScraper):
    DEFAULT_SELETORES = {
        "espera": "div.relative.grid.grid-cols-1.p-6.bg-white.shadow-sm.rounded-lg.gap-6.my-6",
        "cards": "div.relative.grid.grid-cols-1.p-6.bg-white.shadow-sm.rounded-lg.gap-6.my-6",
    }

    DEFAULT_SELETORES_CARDS = {
        "companhia": "span.font-semibold.text-lg.text-gray-800",
        "data": ".gap-2.text-sm > div:nth-child(1) > span:nth-child(2)",
        "horario_saida": "div.rounded-lg.p-2 > div.mt-4 > div > div > div:nth-child(3) > p.font-medium",
        "horario_chegada": "div.rounded-lg.p-2 > div.mt-4 > div > div > div:nth-child(4) > p.font-medium",
        "aeroportos": "div.flex.flex-col.gap-2.text-gray-700.w-full > div:nth-child(1)",
        # "aeroportos_de_escala": "",
        "detalhe_escalas": "div.rounded-lg.p-2 > div.mt-4 > div > div > p.text-sm.font-medium",
        "duracao": "div.rounded-lg.p-2 > div.mt-4 > div > div > div:nth-child(5) > p.font-medium",
        # "preco_individual": "",
        "preco_total": "p.text-black.font-bold.text-xl",
        "classe": ".text-sm.px-3.bg-gray-100.rounded",
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
