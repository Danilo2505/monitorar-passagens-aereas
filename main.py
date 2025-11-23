import schedule
import pandas as pd
from typing import Dict, List, Literal, Optional
import os.path
from shutil import copy
from datetime import datetime
from time import sleep
from scraper import flipmilhas, google, kayak

minutos_espera = 30
pesquisas = (
    (  # 28/12/2025
        "FlipMilhas",
        "https://flipmilhas.com/passagens?adults=4&babies=0&back_date=&children=0&class=economica&departure_date=2025-12-28&destiny=GRU&origin=JDO&rooms=1",
    ),
    (  # 29/12/2025
        "FlipMilhas",
        "https://flipmilhas.com/passagens?adults=4&babies=0&back_date=&children=0&class=economica&departure_date=2025-12-29&destiny=GRU&origin=JDO&rooms=1",
    ),
    (  # 30/12/2025
        "FlipMilhas",
        "https://flipmilhas.com/passagens?adults=4&babies=0&back_date=&children=0&class=economica&departure_date=2025-12-30&destiny=GRU&origin=JDO&rooms=1",
    ),
    # https://www.google.com/travel/flights?gl=BR&hl=pt-BR
    (  # 28/12/2025
        "Google",
        "https://www.google.com/travel/flights/search?tfs=CBwQAhokEgoyMDI1LTEyLTI4ag0IAhIJL20vMDhmcGd0cgcIARIDR1JVQAFAAUABQAFIAXABggELCP___________wGYAQI&tfu=EgoIABAAGAAgAigB&hl=pt-BR&gl=BR",
    ),
    (  # 29/12/2025
        "Google",
        "https://www.google.com/travel/flights/search?tfs=CBwQAhoqEgoyMDI1LTEyLTI5ag0IAhIJL20vMDhmcGd0cg0IAhIJL20vMDIycGZtQAFAAUABQAFIAXABggELCP___________wGYAQI&hl=pt-BR&gl=BR&tcfs=EhcKCS9tLzAyMnBmbRIKU8OjbyBQYXVsbxgEUgRgAngB",
    ),
    (  # 30/12/2025
        "Google",
        "https://www.google.com/travel/flights/search?tfs=CBwQAhokEgoyMDI1LTEyLTMwag0IAhIJL20vMDhmcGd0cgcIARIDR1JVQAFAAUABQAFIAXABggELCP___________wGYAQI&tfu=EgoIABAAGAAgAigB&hl=pt-BR&gl=BR",
    ),
    (  # 28/12/2025, 29/12/2025, 30/12/2025
        "Kayak",
        "https://www.kayak.com.br/flights/JDO-GRU/2025-12-29-flexible-1day/2adults/children-17-17?ucs=15bywhz&sort=price_a",
    ),
)
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


def atualizar_estrutura_excel(caminho_arquivo_excel: str, nome_tabela: str):
    """
    Garante que o arquivo e a aba existam e que as colunas estejam corretas.
    """
    # Se o arquivo NÃO existir → criar com cabeçalho correto
    if not os.path.exists(caminho_arquivo_excel):
        print("Arquivo não existe — criando com cabeçalhos.")

        df_cabecalho = pd.DataFrame(columns=list(nomes_colunas.values()))
        df_cabecalho.to_excel(
            caminho_arquivo_excel, index=False, sheet_name=nome_tabela
        )
        return

    # Lê apenas a aba desejada, criando se não existir
    try:
        df = pd.read_excel(caminho_arquivo_excel, sheet_name=nome_tabela)
    except ValueError:
        # Aba não existe → criar apenas ela sem apagar outras
        print(f"Aba '{nome_tabela}' não existe — criando.")
        with pd.ExcelWriter(
            caminho_arquivo_excel, mode="a", engine="openpyxl"
        ) as writer:
            df_vazio = pd.DataFrame(columns=list(nomes_colunas.values()))
            df_vazio.to_excel(writer, sheet_name=nome_tabela, index=False)
        return

    # Converte os nomes bonitos → internos
    mapa_inverso = {v: k for k, v in nomes_colunas.items()}
    df.rename(columns=mapa_inverso, inplace=True)

    # Garante TODAS as colunas internas
    for col in nomes_colunas.keys():
        if col not in df.columns:
            df[col] = ""

    # Remove colunas extras
    df = df[nomes_colunas.keys()]

    # Converte de volta para os nomes bonitos
    df.rename(columns=nomes_colunas, inplace=True)

    # Salva só a aba ajustada
    with pd.ExcelWriter(
        caminho_arquivo_excel, mode="a", engine="openpyxl", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name=nome_tabela, index=False)

    print("Estrutura da planilha atualizada com sucesso!")


def _parse_brazil_price(s: Optional[str]) -> Optional[float]:
    """
    Converte strings de preço em notação brasileira para float.
    Exemplos:
      "2.150"       -> 2150.0
      "2.150,00"    -> 2150.0
      "R$ 2.150,00" -> 2150.0
      "2150"        -> 2150.0
    Retorna None se não conseguir parsear.
    """
    if s is None:
        return None
    txt = str(s).strip()
    if txt == "":
        return None

    # remover símbolos e espaços comuns
    txt = txt.replace("R$", "").replace(" ", "").replace("\xa0", "")
    txt = txt.replace("no total", "").strip()

    # Se tem vírgula => existe parte decimal (formato BR). Remove pontos de milhares e trocar vírgula por ponto.
    try:
        if "," in txt:
            cleaned = txt.replace(".", "").replace(",", ".")
            return float(cleaned)
        # Se tem ponto mas não vírgula: provavelmente é separador de milhares -> remover pontos
        if "." in txt:
            cleaned = txt.replace(".", "")
            return float(cleaned)
        # só número simples
        return float(txt)
    except Exception:
        return None


def _format_brazil_number(n: Optional[float]) -> str:
    """
    Formata float como string no padrão brasileiro '1.234,56'.
    Se n for None, retorna string vazia.
    """
    if n is None:
        return ""
    # Garante float
    try:
        v = float(n)
    except Exception:
        return ""
    # Formata com separador de milhares (padrão en: ',' e '.'), depois troca
    s = f"{v:,.2f}"  # ex: "2,150.00"
    s = s.replace(",", "X")  # temp
    s = s.replace(".", ",")  # agora "2,150,00"
    s = s.replace("X", ".")  # finalmente "2.150,00"
    return s


def salvar_dados_excel(
    caminho_arquivo_excel,
    nome_tabela,
    dados: List[Dict[str, str]] | Dict[str, str],
    modo: Optional[Literal["acrescentar", "sobrescrever"]] = "acrescentar",
    criar_arquivo_se_nao_existir=True,
    formatar_preco_brasil: bool = True,
):
    # Converter 1 registro → lista
    if isinstance(dados, dict):
        dados = [dados]

    # Criar arquivo se não existir
    if not os.path.exists(caminho_arquivo_excel):
        if criar_arquivo_se_nao_existir:
            df_cabecalho = pd.DataFrame(columns=list(nomes_colunas.values()))
            df_cabecalho.to_excel(
                caminho_arquivo_excel, index=False, sheet_name=nome_tabela
            )
        else:
            return

    # Ler a aba (ou criar se não existir)
    try:
        df_existente = pd.read_excel(caminho_arquivo_excel, sheet_name=nome_tabela)
    except ValueError:
        df_existente = pd.DataFrame(columns=list(nomes_colunas.values()))

    # Novo dataframe
    df_novo = pd.DataFrame(dados)

    # Garantir colunas internas
    for col in nomes_colunas.keys():
        if col not in df_novo.columns:
            df_novo[col] = ""

    # Normaliza ordem/nomes internos e renomeia para nomes bonitos
    df_novo = df_novo[list(nomes_colunas.keys())]
    df_novo.rename(columns=nomes_colunas, inplace=True)

    # --- Tratamento de preços: converte e formata (opcional) ---
    price_cols = ["Preço Individual", "Preço Total"]  # nomes bonitos após o rename
    for col in price_cols:
        if col in df_novo.columns:
            # parsear cada célula para número BR
            parsed = df_novo[col].apply(lambda x: _parse_brazil_price(x))
            if formatar_preco_brasil:
                # reformatar para string no padrão brasileiro (ex: 2.150,00)
                df_novo[col] = parsed.apply(lambda v: _format_brazil_number(v))
            else:
                # deixar como número (float); útil se quiser cálculos no Excel
                df_novo[col] = parsed

    # Juntar dados se for append
    if modo == "acrescentar":
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    # Salvar aba correta
    with pd.ExcelWriter(
        caminho_arquivo_excel,
        mode="a",
        engine="openpyxl",
        if_sheet_exists="replace",
    ) as writer:
        df_final.to_excel(writer, sheet_name=nome_tabela, index=False)


def fazer_backup_dados(caminho_original, caminho_destino):
    # !!! Criar diretório de destino se ele não existir !!!
    copy(src=caminho_original, dst=caminho_destino)


def pesquisar_valores(lista_pesquisas=pesquisas) -> int:
    for pesquisa in lista_pesquisas:
        if pesquisa[0] == "FlipMilhas":
            try:
                # Atualiza a estrutura do Excel
                atualizar_estrutura_excel("dados/dados.xlsx", "FlipMilhas")

                print("--- FlipMilhas ---")
                print("Pesquisando valores...")
                ofertas_flipmilhas = flipmilhas.FlipMilhasScraper(
                    link=pesquisa[1]
                ).scrape()
                print("Salvando dados...")
                salvar_dados_excel(
                    caminho_arquivo_excel="dados/dados.xlsx",
                    nome_tabela="FlipMilhas",
                    dados=ofertas_flipmilhas,
                )
                print("Dados salvos!")
            except Exception as e:
                print(e)
        elif pesquisa[0] == "Google":
            try:
                # Atualiza a estrutura do Excel
                atualizar_estrutura_excel("dados/dados.xlsx", "Google")

                print("--- Google ---")
                print("Pesquisando valores...")
                ofertas_google = google.GoogleScraper(link=pesquisa[1]).scrape()
                print("Salvando dados...")
                salvar_dados_excel(
                    caminho_arquivo_excel="dados/dados.xlsx",
                    nome_tabela="Google",
                    dados=ofertas_google,
                )
                print("Dados salvos!")
            except Exception as e:
                print(e)
        elif pesquisa[0] == "Kayak":
            try:
                # Atualiza a estrutura do Excel
                atualizar_estrutura_excel("dados/dados.xlsx", "Kayak")

                print("--- Kayak ---")
                print("Pesquisando valores...")
                ofertas_kayak = kayak.KayakScraper(link=pesquisa[1]).scrape()
                print("Salvando dados...")
                salvar_dados_excel(
                    caminho_arquivo_excel="dados/dados.xlsx",
                    nome_tabela="Kayak",
                    dados=ofertas_kayak,
                )
                print("Dados salvos!")

            except Exception as e:
                print(e)
    fazer_backup_dados(
        "dados/dados.xlsx",
        f"dados/backups/dados_backup_{datetime.now().strftime("%d-%m-%Y")}-{datetime.now().strftime("%H-%M")}.xlsx",
    )
    print("")
    return 0


if __name__ == "__main__":
    # Pesquisa os valores no início da execução
    pesquisar_valores()

    # Agenda uma tarefa para pesquisar os valores a cada minutos_espera
    schedule.every(minutos_espera).minutes.do(pesquisar_valores)

    print("Monitoramento iniciado.")

    while True:
        schedule.run_pending()
        sleep(1)  # Não trava nada, só roda quando precisa
