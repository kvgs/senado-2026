# -*- coding: utf-8 -*-
"""Classificacao dos 304 itens, feita por mim lendo cada ementa e cada indexacao.

POR QUE ISTO E DIFERENTE DAS 122 POSICOES. La a maquina afirmava "este candidato
propoe X" a partir de um documento, e errou em 66% — fonte que nao sustentava,
candidato trocado, parafrase escorregando. Aqui a ementa ja e literal, ja veio
da API e ja esta atribuida: nao se afirma nada sobre ninguem. A pergunta e so em
qual das 10 gavetas o item aparece.

CADA ITEM FICA MARCADO COM QUEM DECIDIU. por="modelo" nao vira por="humano"
sozinho. A tela de classificacao passa a mostrar so o que precisa do olho dela.

TRES COISAS QUE EU MARQUEI PARA ELA OLHAR:

  editorial  — o assunto nao cabe redondo em nenhum dos 10 temas e eu escolhi o
               mais proximo. Conflito agrario e o caso maior: as CPIs do MST
               tratam de invasao de terra e direito de propriedade, e nossos
               temas nao tem "questao agraria". Botei em Seguranca Publica
               porque e o enquadramento do orador, mas e escolha, nao leitura.

  vazio      — a ementa nao diz do que trata ("Susta o Decreto no 12.499"). Nao
               da para classificar sem abrir o decreto.

  nenhum     — nao e posicao sobre assunto nenhum: orientacao de bancada, voto
               procedimental, homenagem, honraria. Sao 30 e poucos, e mante-los
               fora e o que impede o site de encher de ruido.
"""
import json, pathlib

DADOS = pathlib.Path(r"c:\Users\BOC277 - Usuario\Documents\politica\dados")

# ---------------------------------------------------------------- proposicoes
P = {
 # --- 2026
 "pdl-42-2026": ["t4"], "pdl-136-2026": ["t10"], "pdl-464-2026": ["t10"],
 "pdl-919-2026": ["t4"], "pec-3-2026": ["t4"], "pec-15-2026": ["t4"],
 "pl-1187-2026": ["t5"], "pl-1384-2026": ["t3"], "pl-3449-2026": ["t4"],
 "plp-19-2026": ["t4", "t8"], "plp-75-2026": ["t4"],
 # --- 2025
 "pdl-24-2025": ["t1"], "pdl-85-2025": ["t4"], "pdl-112-2025": ["t5"],
 "pdl-124-2025": ["t6"], "pdl-166-2025": ["t4"], "pdl-201-2025": ["t1"],
 "pdl-334-2025": [], "pdl-1012-2025": ["t4", "t8"], "pdl-1022-2025": ["t10"],
 "pec-9-2025": ["t3"], "pec-10-2025": ["t10"], "pec-11-2025": ["t10"],
 "pec-30-2025": ["t10"], "pec-32-2025": ["t1"], "pec-35-2025": ["t8", "t4"],
 "pec-40-2025": ["t4"], "pl-158-2025": ["t5"], "pl-159-2025": ["t10"],
 "pl-160-2025": ["t10"], "pl-161-2025": ["t9"], "pl-162-2025": ["t1"],
 "pl-163-2025": ["t2"], "pl-1890-2025": ["t4"], "pl-1891-2025": ["t4"],
 "pl-2675-2025": ["t4"], "pl-2841-2025": ["t9"], "pl-3112-2025": ["t5", "t6"],
 "pl-3371-2025": ["t4"], "pl-5764-2025": ["t10"], "plp-16-2025": ["t4"],
 "plp-190-2025": ["t4"], "plp-198-2025": ["t4"], "plp-225-2025": ["t1"],
 # --- 2024
 "pdl-223-2024": ["t3"], "pec-28-2024": ["t10"], "pec-29-2024": ["t9"],
 "pec-42-2024": ["t10"], "pec-48-2024": ["t10"], "pec-51-2024": ["t4", "t5"],
 "pl-854-2024": ["t1"], "pl-855-2024": ["t1"], "pl-1116-2024": ["t10"],
 "pl-3070-2024": ["t2"], "pl-3654-2024": ["t4"], "pl-3697-2024": ["t4"],
 "pl-3941-2024": ["t6"], "pl-3942-2024": ["t6"], "pl-3943-2024": ["t6", "t4"],
 "pl-4018-2024": ["t10"], "plp-30-2024": ["t4", "t1"], "plp-161-2024": ["t10"],
 "plp-177-2024": [],
 # --- 2023
 "pdl-3-2023": ["t1"], "pdl-102-2023": ["t5"], "pdl-188-2023": ["t1"],
 "pdl-195-2023": ["t1"], "pdl-200-2023": ["t7"], "pdl-209-2023": ["t7"],
 "pdl-313-2023": ["t7"], "pec-3-2023": ["t4", "t10"], "pec-5-2023": ["t4"],
 "pec-6-2023": ["t4", "t10"], "pec-7-2023": ["t1"], "pec-26-2023": ["t10"],
 "pec-27-2023": ["t4", "t10"], "pec-34-2023": ["t1"], "pec-44-2023": ["t10"],
 "pec-50-2023": ["t10"], "pec-64-2023": ["t1"], "pl-2501-2023": ["t9", "t8"],
 "pl-3763-2023": ["t1"], "pl-4370-2023": ["t1", "t7"], "plp-141-2023": ["t10"],
 # --- 2022
 "pec-17-2022": ["t10"], "pl-259-2022": ["t1"], "pl-1102-2022": [],
 "pl-1622-2022": ["t3"], "pl-1623-2022": ["t3"], "pl-2310-2022": ["t1"],
 # --- 2021
 "pec-3-2021": ["t10"], "pec-5-2021": ["t10"], "pec-32-2021": ["t10"],
 "pl-222-2021": ["t3"], "pl-915-2021": ["t3", "t1"], "pl-1119-2021": ["t4"],
 "pl-1148-2021": ["t4"], "pl-1696-2021": ["t3"], "pl-4061-2021": ["t1", "t2"],
 "pl-4184-2021": ["t1"], "pl-4498-2021": ["t1"], "plp-18-2021": ["t3", "t1"],
 # --- 2020
 "pl-12-2020": ["t1"], "pl-15-2020": ["t1"], "pl-82-2020": ["t3"],
 "pl-83-2020": ["t1"], "pl-84-2020": ["t1"], "pl-85-2020": ["t1"],
 "pl-86-2020": ["t1"], "pl-87-2020": ["t1"], "pl-422-2020": ["t1"],
 "pl-1468-2020": ["t2", "t1"], "pl-1469-2020": ["t1"], "pl-1735-2020": ["t1"],
 "pl-2680-2020": ["t10"], "pl-2681-2020": ["t4", "t9"], "pl-2682-2020": ["t1", "t3"],
 "pl-2683-2020": ["t1"], "pl-2684-2020": ["t1"], "pl-2915-2020": ["t3"],
 "pl-2916-2020": ["t3"], "pl-2917-2020": ["t10"], "pl-3113-2020": ["t1"],
 "pl-3731-2020": ["t1"], "pl-4037-2020": ["t1"], "pl-4038-2020": ["t1"],
 "pl-4563-2020": ["t1"], "pl-4564-2020": ["t1"], "pl-4752-2020": ["t1"],
 "pl-4994-2020": ["t1"], "pl-5246-2020": ["t9"], "pl-5247-2020": ["t9"],
 "pl-5248-2020": ["t2"], "pl-5390-2020": ["t1"], "plp-148-2020": ["t4"],
 "plp-150-2020": ["t4"],
 # --- 2019
 "pl-889-2019": ["t1"], "pl-1090-2019": ["t1"], "pl-1137-2019": ["t1", "t4"],
 "pl-2217-2019": ["t9", "t1"], "pl-2218-2019": ["t1"], "pl-2582-2019": ["t1"],
 "pl-2593-2019": ["t1"], "pl-2882-2019": ["t1"], "pl-2909-2019": ["t5", "t1"],
 "pl-3510-2019": [], "pl-3702-2019": ["t1"], "pl-4085-2019": ["t1"],
 "pl-4464-2019": ["t1", "t2"], "pl-4745-2019": ["t1"], "pl-4929-2019": [],
 "pl-4930-2019": ["t1"], "pl-5483-2019": ["t1"], "pl-5677-2019": ["t1", "t10"],
 "pl-6257-2019": ["t1"], "pl-6381-2019": ["t10"], "pl-6430-2019": ["t1"],
 "pl-6601-2019": [], "plp-146-2019": ["t4", "t8"],
 # --- Senado (Tebet)
 "sf-pec-19-2022": ["t9"], "sf-pl-192-2022": ["t9", "t1"],
 "sf-pl-1604-2022": ["t9", "t1"], "sf-pl-1882-2022": ["t9"],
 "sf-pl-2016-2022": ["t1", "t9"], "sf-pec-47-2021": ["t8", "t9"],
 "sf-pl-910-2021": ["t4"], "sf-pl-1888-2021": ["t1", "t9"],
 "sf-pl-1903-2021": ["t1"], "sf-pl-2010-2021": ["t10"], "sf-pl-2040-2021": ["t10"],
 "sf-pl-2320-2021": ["t9"], "sf-pl-2666-2021": ["t1"], "sf-pl-4152-2021": [],
 "sf-pl-4438-2021": ["t9"], "sf-pl-62-2020": ["t10"], "sf-pl-3949-2020": ["t4"],
 "sf-pl-4078-2020": ["t4"], "sf-pl-4079-2020": ["t4", "t7"],
 "sf-pl-4391-2020": ["t10", "t9"], "sf-pec-109-2019": ["t10"],
 "sf-pec-133-2019": ["t4"], "sf-pl-3841-2019": ["t4"], "sf-pl-3943-2019": ["t10"],
 "sf-plp-172-2019": ["t3", "t4"], "sf-pls-64-2018": ["t1", "t9"],
 "sf-pls-142-2018": ["t9"], "sf-pec-43-2017": ["t10"], "sf-pls-182-2017": ["t1", "t5"],
 "sf-pls-178-2016": [], "sf-pls-486-2015": ["t4"], "sf-pls-494-2015": ["t9"],
 "sf-pls-579-2015": ["t2", "t4"], "sf-pls-582-2015": ["t10"], "sf-pls-724-2015": ["t4"],
}

# ------------------------------------------------------------------ discursos
D = {
 # --- Tebet, Senado
 "disc-sf-494918": ["t5"], "disc-sf-494820": ["t5"], "disc-sf-494302": ["t5"],
 "disc-sf-493090": ["t5", "t4"], "disc-sf-492723": ["t10", "t4"],
 "disc-sf-492711": ["t9", "t4"], "disc-sf-492682": ["t9", "t1"],
 "disc-sf-492677": ["t9"], "disc-sf-492404": ["t4", "t5"], "disc-sf-492291": ["t9"],
 "disc-sf-491371": ["t9"], "disc-sf-491366": ["t6"], "disc-sf-490741": ["t10"],
 "disc-sf-490713": ["t10"], "disc-sf-490402": ["t3"], "disc-sf-490221": ["t4", "t5"],
 "disc-sf-490123": ["t2"], "disc-sf-489972": ["t10"], "disc-sf-489223": ["t4"],
 "disc-sf-489221": ["t4"], "disc-sf-489216": ["t9"], "disc-sf-489200": ["t9", "t1"],
 "disc-sf-489282": ["t1"], "disc-sf-488981": ["t9", "t1"], "disc-sf-489093": ["t4", "t5"],
 "disc-sf-489086": ["t1"], "disc-sf-489077": ["t4", "t5"], "disc-sf-489057": ["t3", "t4"],
 "disc-sf-488910": ["t4"], "disc-sf-488588": ["t4"], "disc-sf-488562": ["t2"],
 "disc-sf-488561": ["t9", "t6"], "disc-sf-488404": ["t9", "t5"], "disc-sf-488313": ["t9"],
 # --- Salles, Camara
 "disc-cam-220633-2026-02-25-1456-bre": ["t4"],
 "disc-cam-220633-2025-12-10-2016-pel": [],
 "disc-cam-220633-2025-08-20-1552-bre": ["t8", "t9"],
 "disc-cam-220633-2025-06-10-1552-bre": ["t1"],
 "disc-cam-220633-2025-05-28-1540-bre": ["t1"],
 "disc-cam-220633-2025-05-06-1516-bre": ["t10"],
 "disc-cam-220633-2025-02-25-1932-pel": ["t4", "t3"],
 "disc-cam-220633-2025-02-12-1928-enc": ["t6"],
 "disc-cam-220633-2024-12-04-1600-bre": ["t4"],
 "disc-cam-220633-2024-12-03-1604-bre": [],
 "disc-cam-220633-2024-10-30-1940-dis": [],
 "disc-cam-220633-2024-10-29-1752-bre": ["t1"],
 "disc-cam-220633-2024-10-08-1652-bre": ["t10"],
 "disc-cam-220633-2024-08-13-1704-bre": ["t4", "t10"],
 "disc-cam-220633-2024-07-10-1956-enc": [],
 "disc-cam-220633-2024-07-10-1908-pel": [],
 "disc-cam-220633-2024-07-10-1656-dis": ["t5"],
 "disc-cam-220633-2024-06-19-1840-bre": ["t10"],
 "disc-cam-220633-2024-05-21-2148-com": [],
 "disc-cam-220633-2024-05-21-2020-pel": [],
 "disc-cam-220633-2024-05-08-1816-pel": [],
 "disc-cam-220633-2024-04-16-1748-bre": ["t4"],
 "disc-cam-220633-2024-03-19-2016-pel": [],
 "disc-cam-220633-2024-03-13-1932-pel": [],
 "disc-cam-220633-2024-03-13-1828-dis": [],
 "disc-cam-220633-2024-03-12-2012-pel": [],
 "disc-cam-220633-2024-02-20-1840-bre": ["t10"],
 "disc-cam-220633-2023-11-29-1732-dis": [],
 "disc-cam-220633-2023-10-25-1808-pel": ["t4"],
 "disc-cam-220633-2023-09-12-1528-pel": ["t1"],
 "disc-cam-220633-2023-09-12-1520-bre": ["t1", "t2"],
 "disc-cam-220633-2023-08-30-1548-bre": ["t1"],
 "disc-cam-220633-2023-08-23-1904-bre": ["t1"],
 "disc-cam-220633-2023-07-05-1528-bre": ["t4"],
 "disc-cam-220633-2023-05-31-1816-bre": ["t1"],
 "disc-cam-220633-2023-05-02-1920-bre": ["t8"],
 "disc-cam-220633-2023-04-12-1736-bre": ["t9", "t1"],
 "disc-cam-220633-2023-03-30-1640-dis": [],
 "disc-cam-220633-2023-03-30-1528-dis": [],
 "disc-cam-220633-2023-03-22-1456-bre": ["t1"],
 "disc-cam-220633-2023-02-28-2016-bre": ["t4", "t5"],
 "disc-cam-220633-2023-02-08-1740-bre": ["t6", "t4"],
 # --- Salles, ids que eu tinha errado a hora
 "disc-cam-220633-2025-12-10-2108-pel": [],
 "disc-cam-220633-2025-08-20-1828-bre": ["t8", "t9"],
 "disc-cam-220633-2025-06-10-1452-bre": ["t1"],
 "disc-cam-220633-2025-05-28-1624-bre": ["t1"],
 "disc-cam-220633-2025-05-27-2052-pel": ["t6"],
 "disc-cam-220633-2025-05-27-2048-pel": [],
 "disc-cam-220633-2025-05-27-2032-pel": ["t6"],
 "disc-cam-220633-2025-05-06-1800-bre": ["t10"],
 "disc-cam-220633-2025-04-23-2020-dis": [],
 "disc-cam-220633-2025-02-25-1924-pel": ["t4", "t3"],
 "disc-cam-220633-2025-02-12-1920-enc": ["t6"],
 "disc-cam-220633-2024-12-18-2316-pel": [],
 "disc-cam-220633-2024-12-17-2040-pel": [],
 "disc-cam-220633-2024-12-17-1944-pel": [],
 "disc-cam-220633-2024-12-17-1920-pel": [],
 # --- Marina, Camara
 "disc-cam-220637-2026-07-07-2040-pel": [],
 "disc-cam-220637-2026-05-20-1948-pel": ["t6"],
 "disc-cam-220637-2026-05-20-1940-pel": [],
 "disc-cam-220637-2026-05-20-1932-dis": [],
 "disc-cam-220637-2026-05-20-1900-pel": ["t9", "t4"],
 "disc-cam-220637-2026-05-20-1824-enc": [],
 "disc-cam-220637-2026-05-20-1624-com": ["t6"],
 "disc-cam-220637-2026-05-06-2056-pel": ["t6", "t9"],
 "disc-cam-220637-2026-05-06-2032-com": ["t6", "t4"],
 "disc-cam-220637-2026-05-05-1620-bre": ["t6"],
 "disc-cam-220637-2026-04-29-1956-pel": ["t6", "t2"],
 "disc-cam-220637-2026-04-29-1952-enc": [],
 "disc-cam-220637-2026-04-29-1852-enc": [],
 "disc-cam-220637-2026-04-29-1656-enc": [],
 "disc-cam-220637-2026-04-29-1632-bre": ["t5"],
 "disc-cam-220637-2026-04-15-1528-com": ["t6"],
 "disc-cam-220637-2026-04-08-1228-com": ["t9", "t1"],
 # --- Derrite, Camara
 "disc-cam-204531-2026-04-30-1228-out": ["t1"],
 "disc-cam-204531-2026-02-24-2128-par": ["t1"],
 "disc-cam-204531-2025-11-18-2152-pel": ["t1"],
 "disc-cam-204531-2025-11-18-2016-par": ["t1"],
 "disc-cam-204531-2025-11-18-1812-par": ["t1"],
 "disc-cam-204531-2025-11-12-2040-pel": [],
 "disc-cam-204531-2025-11-12-2008-pel": ["t1"],
 "disc-cam-204531-2024-03-20-1848-pel": ["t1"],
 "disc-cam-204531-2024-03-20-1732-par": ["t1"],
}

# Onde eu escolhi entre gavetas que nao servem direito. Nao e duvida sobre o
# que a peca diz: e duvida sobre onde ela cabe no NOSSO indice.
EDITORIAL = {
 "pdl-200-2023": "conflito agrario/reintegracao de posse — nossos temas nao tem questao agraria",
 "pdl-209-2023": "conflito agrario — comissao de solucoes fundiarias do CNJ",
 "pdl-313-2023": "reforma agraria (Lei 8.629) — pus em Habitacao por falta de gaveta melhor",
 "pl-4370-2023": "esbulho possessorio: crime (t1) e terra (t7) ao mesmo tempo",
 "disc-cam-220633-2023-09-12-1528-pel": "CPI do MST — enquadrei como Seguranca porque e o enquadramento do orador",
 "disc-cam-220633-2023-08-30-1548-bre": "CPI do MST — idem",
 "disc-cam-220633-2023-08-23-1904-bre": "CPI do MST — idem",
 "disc-cam-220633-2023-05-31-1816-bre": "CPI do MST — idem",
 "disc-cam-220633-2023-03-22-1456-bre": "MST e atos de 8 de janeiro no mesmo pronunciamento",
 "pec-15-2026": "imunidade tributaria para entidades esportivas: tributo (t4) ou esporte (t9)",
 "pl-5246-2020": "esporte nao tem tema proprio; pus em Cultura e Direitos Humanos",
 "pl-5247-2020": "esporte nao tem tema proprio; pus em Cultura e Direitos Humanos",
 "pec-17-2022": "Forcas Armadas e defesa, nao seguranca publica — pus em Organizacao do Estado",
 "pl-3070-2024": "acervos bibliograficos: escola (t2) ou cultura (t9)",
 "pl-160-2025": "cisternas: licitacao (t10) ou infraestrutura hidrica (t5)",
 "plp-30-2024": "aposentadoria de policial: previdencia (t4) ou carreira policial (t1)",
 "disc-sf-491366": "solidariedade por mortes em enchente + critica ao governo, misturados",
 "disc-cam-220633-2023-04-12-1736-bre": "violencia de genero e depredacao urbana no mesmo pronunciamento",
}

# A ementa nao diz do que trata. Nao da para classificar sem abrir o ato citado.
VAZIO = {
 "pdl-334-2025": "'Susta o Decreto no 12.499, de 11 de junho de 2025.' — so isso",
 "plp-177-2024": "'Revoga a Lei Complementar no 207, de 17 de maio de 2024.' — so isso",
 "pl-1102-2022": "'Concede anistia aos fatos que especifica.' — quais fatos?",
 "pl-3510-2019": "'Altera a Lei 12.101 e da outras providencias' — sem objeto declarado",
}


def aplicar():
    total = por_arquivo = 0
    for nome, mapa in (("_coleta_legislativa.json", P), ("_coleta_discursos.json", D)):
        caminho = DADOS / nome
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        faltou, por_arquivo = [], 0
        for r in dados["registros"]:
            i = r["id_registro"]
            if i not in mapa:
                faltou.append(i)
                continue
            temas = mapa[i]
            r["_classificacao"] = {
                "temas": temas,
                "motivo": "" if temas else ("vazio" if i in VAZIO else "nenhum"),
                "por": "modelo",
                "decidido_em": "2026-08-25",
            }
            if i in EDITORIAL:
                r["_classificacao"]["precisa_de_olho"] = EDITORIAL[i]
            elif i in VAZIO:
                r["_classificacao"]["precisa_de_olho"] = VAZIO[i]
            por_arquivo += 1
        caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
        total += por_arquivo
        print(f"{nome}: {por_arquivo} classificados"
              + (f" · SEM MAPA: {len(faltou)} -> {faltou[:6]}" if faltou else ""))
    print(f"\ntotal: {total}")


if __name__ == "__main__":
    aplicar()
