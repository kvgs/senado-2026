# -*- coding: utf-8 -*-
"""Baixa as fotos de registro das candidaturas.

DE ONDE VEM, E QUEM E CREDITADO — SAO COISAS DIFERENTES
A imagem e a foto de registro de candidatura do TSE, indexada pelo sequencial da
candidatura. O TSE devolve 403 a qualquer acesso automatizado, inclusive com
identificacao de navegador, e o dataset de fotos de 2026 nao foi localizado no
portal de dados abertos.

O arquivo e obtido de candidatos.nexojornal.com.br, que republica esse mesmo
dataset. O CREDITO VAI PARA O TSE, nao para o Nexo: o Nexo e redistribuidor, nao
origem, e diz isso no proprio rodape ("Dados do TSE").

Creditar quem hospedava em vez de quem originou seria atribuir material a fonte
errada — o mesmo erro que fez 51 posicoes sairem do ar na revisao. Ficaria
incoerente no mesmo site.

O caminho real de obtencao fica registrado em documentos.json. Nao se finge que
baixamos do TSE.
"""
import hashlib
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parent

import argparse as _argparse

import acervo

# --uf escolhe o acervo. Trabalhar no estado errado nao da erro: da resultado
# plausivel sobre outra coisa.
_ap = _argparse.ArgumentParser(add_help=False)
_ap.add_argument("--uf", default=None)
_UF = (_ap.parse_known_args()[0].uf or acervo.uf_padrao()).upper()
DADOS = acervo.exige(_UF)

DESTINO = RAIZ / "fotos-candidatos"
ESPELHO = "https://candidatos.nexojornal.com.br/fotos/{}.jpg"
NAVEGADOR = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/126 Safari/537.36")

CREDITO = "TSE — foto de registro de candidatura"
ORIGEM_TECNICA = ("Arquivo obtido do espelho publicado por candidatos.nexojornal.com.br, que "
                  "republica o dataset de fotos do TSE indexado pelo sequencial da candidatura. "
                  "O TSE devolve 403 a acesso automatizado e o dataset de 2026 nao foi localizado "
                  "no portal de dados abertos. O credito da imagem e do TSE: o Nexo redistribui, "
                  "nao origina.")


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": NAVEGADOR, "Accept": "image/*"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read(), r.headers.get("Content-Type", "")


def main():
    DESTINO.mkdir(exist_ok=True)
    cp = DADOS / "candidaturas.json"
    dados = json.loads(cp.read_text(encoding="utf-8"))
    lista = dados["candidaturas"] if isinstance(dados, dict) else dados

    ok = falhou = 0
    for c in sorted(lista, key=lambda x: int(x["numero_urna"])):
        seq = str(c["sequencial_tse"])
        nome = c["pessoa"]["nome_urna"]
        alvo = DESTINO / f"{seq}.jpg"
        print(f"{c['numero_urna']:>4}  {nome[:24]:24}", end="  ")

        try:
            bruto, tipo = baixar(ESPELHO.format(seq))
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"nao obtida ({e})")
            c.setdefault("foto", {})
            c["foto"] = {"_pendente": f"Foto nao obtida em {time.strftime('%Y-%m-%d')}: {e}"}
            falhou += 1
            continue

        if not tipo.startswith("image/") or len(bruto) < 800:
            print(f"resposta nao e imagem ({tipo}, {len(bruto)}b)")
            falhou += 1
            continue

        alvo.write_bytes(bruto)
        c["foto"] = {
            "arquivo": f"fotos-candidatos/{seq}.jpg",
            "credito": CREDITO,
            "bytes": len(bruto),
            "sha256_16": hashlib.sha256(bruto).hexdigest()[:16],
            "obtida_em": time.strftime("%Y-%m-%d"),
            "_origem_tecnica": ORIGEM_TECNICA,
        }
        print(f"ok  {len(bruto)/1024:.1f} KB")
        ok += 1
        time.sleep(0.5)          # cortesia com o servidor de terceiro

    cp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{ok} foto(s) obtidas, {falhou} sem foto")
    print(f"total em disco: {sum(f.stat().st_size for f in DESTINO.glob('*.jpg'))/1024:.0f} KB")
    print("credito exibido no site: " + CREDITO)
    print("\nagora rode: python gerar_site.py")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
