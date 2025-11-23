from playwright.sync_api import sync_playwright
from typing import Dict, List
from datetime import datetime
from .base import *


class GoogleScraper(BaseScraper):
    DEFAULT_SELETORES_CARDS = {
        "companhia": "div.sSHqwe.tPgKwe.ogfYpf > span",
        "data": "div.GYgkab.YICvqf.kStSsc.ieVaIb > div > input",
        "horario_saida": "div.zxVSec.YMlIz.tPgKwe.ogfYpf > span > span:nth-child(1) > span > span > span",
        "horario_chegada": "div.zxVSec.YMlIz.tPgKwe.ogfYpf > span > span:nth-child(2) > span > span > span",
        "aeroportos": "span.PTuQse.sSHqwe.tPgKwe.ogfYpf",
        "aeroportos_de_escala": "div.sSHqwe.tPgKwe.ogfYpf",
        "detalhe_escalas": "div.EfT7Ae.AdWm1c.tPgKwe > span.ogfYpf",
        "duracao": "div.gvkrdb.AdWm1c.tPgKwe.ogfYpf",
        # "preco_individual": "",
        "preco_total": "div.BVAVmf.I11szd.POX3ye > div.YMlIz.FpEdX > span",
        # "classe": "",
    }

    DEFAULT_SELETORES = {
        "espera": "div.yR1fYc > div.mxvQLc.ceis6c.uj4xv.uVdL1c.A8qKrc",
        "cards": f"div.yR1fYc > div.mxvQLc.ceis6c.uj4xv.uVdL1c.A8qKrc:has({DEFAULT_SELETORES_CARDS['preco_total']})",
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
                page.wait_for_load_state()
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
                        if chave == "data":
                            texto = page.locator(seletor).first.input_value()
                        else:
                            texto = card.locator(seletor).first.text_content()
                        info[chave] = self.limpar(texto)

                    info_cards.append(info)

            finally:
                browser.close()

            return info_cards
