from typing import Dict, List, Optional
from abc import abstractmethod

nomes_colunas = {
    "dia_pesquisa": "Dia da Pesquisa",
    "horario_pesquisa": "Horário da Pesquisa",
    "companhia": "Companhia",
    "data": "Data",
    "horario_saida": "Horário de Saída",
    "horario_chegada": "Horário de Chegada",
    "preco_individual": "Preço Individual",
    "preco_total": "Preço Total",
    "aeroportos": "Aeroportos",
    "aeroportos_de_escala": "Aeroportos de Escala",
    "detalhe_escalas": "Detalhe Escalas",
    "duracao": "Duração",
    "classe": "Classe",
}


class BaseScraper:
    """Interface base para todos os scrapers."""

    def __init__(self, link, numero_maximo_de_ofertas=10):
        self.link = link
        self.numero_maximo_de_ofertas = numero_maximo_de_ofertas

    @abstractmethod
    def limpar(self, texto: Optional[str]) -> str:
        """Normaliza textos retirados do site."""
        if not texto:
            return ""
        return (
            texto.replace("\xa0", "")
            .replace("R$ ", "R$")
            .replace("R$", "")
            .replace(" no total", "")
            .strip()
        )

    def scrape(self) -> List[Dict[str, str]]:
        """Executa o scraping e retorna uma lista de registros."""
        raise NotImplementedError("Scrapers devem implementar o método scrape()")

    def gerar_link(self) -> str:
        """Gera o link de pesquisa de acordo com o site, aeroportos, datas, classes, etc."""
        link = ""
        return link
