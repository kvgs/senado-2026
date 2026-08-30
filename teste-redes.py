# -*- coding: utf-8 -*-
"""Trava as decisoes da recuperacao de contato em cadastrar_redes.py.

CADA CASO AQUI SAIU DA BASE DO TSE, e nenhum foi inventado para o teste. Sao as
formas em que 315 candidaturas ao Senado erraram o campo de rede social — e a
razao do teste e que a diferenca entre recuperar e inventar mora em detalhes que
nao se lembram depois: um espaco dentro do endereco, um corte em 80 caracteres,
uma palavra que separa dois links de uma que faz parte de um so.

O grupo mais importante e o de baixo, o que NAO pode ser recuperado. Recuperacao
que erra para menos deixa um contato de fora; recuperacao que erra para mais
manda o eleitor para o perfil de outra pessoa, ou republica o telefone de alguem.

USO
    python teste-redes.py
"""
from __future__ import annotations

import importlib.util

spec = importlib.util.spec_from_file_location("cr", "cadastrar_redes.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)

# (linha declarada, cortada em 80?, o que tem de sair)
RECUPERA = [
    # -- handle com a rede escrita ao lado -----------------------------------
    ("INSTAGRAM: @ALCIDESFERNANDES", False,
     ["https://www.instagram.com/alcidesfernandes"]),
    ("TIK TOK: ALCIDESFERNANDESBR", False,
     ["https://www.tiktok.com/@alcidesfernandesbr"]),
    ("TWITER: ALCIDESFERNM", False, ["https://x.com/alcidesfernm"]),
    ("INSTAGRAN: @MENDONCAFILHOPE", False,
     ["https://www.instagram.com/mendoncafilhope"]),
    ("FACE: /MENDONCAFILHO", False, ["https://www.facebook.com/mendoncafilho"]),
    ("@EDVALDONOGUEIRA/INSTAGRAM", False,
     ["https://www.instagram.com/edvaldonogueira"]),
    ("@PAULAFALCAO16 INSTAGRAM", False,
     ["https://www.instagram.com/paulafalcao16"]),
    # duas redes, um handle: o texto declara as duas
    ("INSTAGRAM E FACEBOOK:  @DAVIDAVINOFILHO", False,
     ["https://www.instagram.com/davidavinofilho",
      "https://www.facebook.com/davidavinofilho"]),

    # -- endereco com sujeira em volta ---------------------------------------
    ("HTTPS://.WWW.SENADOREDUARDOBRAGA155.COM.BR", False,
     ["HTTPS://WWW.SENADOREDUARDOBRAGA155.COM.BR"]),
    ("*  HTTPS://WWW.INSTAGRAM.COM/ANDREMONTEIRORJ * FACEBOOK: HTTPS://", False,
     ["HTTPS://WWW.INSTAGRAM.COM/ANDREMONTEIRORJ"]),
    ("FACEBOOK: HTTPS://WWW.FACEBOOK.COM/RUICOSTAOFICIAL INSTAGRAM: "
     "HTTPS://WWW.INSTAGRAM.COM/RUICOSTA", False,
     ["HTTPS://WWW.FACEBOOK.COM/RUICOSTAOFICIAL",
      "HTTPS://WWW.INSTAGRAM.COM/RUICOSTA"]),
    # esquema digitado errado
    ("TTPS://K.KWAI.COM/P/HCRXECIZ", False, ["HTTPS://K.KWAI.COM/P/HCRXECIZ"]),
    ("HTTPS:WWW.TIKTOK.COM/@EDUARDOAMORIMSE", False,
     ["HTTPS://WWW.TIKTOK.COM/@EDUARDOAMORIMSE"]),
    # endereco sem http:// convive com outro que tem
    ("X/TWITTER: X.COM/JAQUESWAGNER KWAI: KWAI.COM/@JAQUESWAGNEROFICIAL "
     "YOUTUBE: YOUTU", True,
     ["https://X.COM/JAQUESWAGNER", "https://KWAI.COM/@JAQUESWAGNEROFICIAL"]),

    # -- corte do TSE em 80 caracteres ---------------------------------------
    # o segundo endereco esta pela metade e nao pode entrar
    ("HTTPS://WWW.INSTAGRAM.COM/ANTONIOBARROSAF - "
     "HTTPS://WWW.INSTAGRAM.COM/ANTONIOBA", True,
     ["HTTPS://WWW.INSTAGRAM.COM/ANTONIOBARROSAF"]),
    # aqui o corte caiu na QUERY: o perfil esta inteiro, joga fora so o rastreio
    ("HTTPS://WWW.INSTAGRAM.COM/MAUROMENDESOFICIAL?IGSH=MTU0DGN2NXFXA29SYW==&IGSI=MTU0", True,
     ["HTTPS://WWW.INSTAGRAM.COM/MAUROMENDESOFICIAL"]),
    # rastreio sai mesmo sem corte
    ("https://www.instagram.com/senador?igsh=ABC", False,
     ["https://www.instagram.com/senador"]),
]

# Estes NAO podem virar endereco nenhum.
RECUSA = [
    # espaco dentro do proprio endereco: cortar ali inventa um perfil
    ("HTTPS://OPEN.SPOTIFY.COM/SHO W/64IDJIVVN42XULQAQRDUBV", False),
    ("HTTPS://WWW.FACEBOOK.COM/ ANDREMOURASE", False),
    # handle sem dizer a rede, e a base do TSE nao tem coluna de plataforma
    ("@MARCELOQUEIROGA", False),
    ("@MAIRADESOUZA.UP", False),
    ("MARIANACARVALHO.RO", False),
    ("MILTONCARDOSO.OFICIAL", False),
    # um token so: nao da para saber se a rede e Threads ou se o handle
    # inteiro se chama assim
    ("THREADS_EITUVIU", False),
    # nome de gente por extenso nao e handle
    ("FACEBOOK: ALCIDES FERNANDES", False),
    ("INSTAGRAM.  -PRGILVAN COSTA", False),
    # dado pessoal no campo errado
    ("TELEGRAM 8198377-0777", False),
    ("+55 (92) 99393-0222", False),
    ("ANDREMONTEIRORJ01@GMAIL.COM", False),
    ("EMAIL: CADYGO@GMAIL.COM CINTIADIASPSOL@GMAIL.COM - SITE: CINTIADIASPSOL.COM.BR -", False),
    ("RUA GUANABARA, 61 CENTRO INDAIAL - SC", False),
    # modelo que o partido nao preencheu
    ("HTTPS://CANDIDATOS.PCO.ORG.BR/C/NOME-DE-URNA-2026", False),
]


def main() -> None:
    falhas = 0
    print(f"=== {len(RECUPERA)} que tem de ser recuperados ===")
    for linha, cortada, esperado in RECUPERA:
        achadas, motivo = cr.recuperar(linha, cortada)
        ok = achadas == esperado
        falhas += not ok
        print(("OK   " if ok else "FALHA") + f"  {linha[:56]}")
        if not ok:
            print(f"         esperava {esperado}")
            print(f"         veio     {achadas or '(nada) ' + motivo}")

    print(f"\n=== {len(RECUSA)} que NAO podem virar endereco ===")
    for linha, cortada in RECUSA:
        achadas, motivo = cr.recuperar(linha, cortada)
        ok = not achadas
        falhas += not ok
        print(("OK   " if ok else "FALHA") + f"  {linha[:56]}")
        if not ok:
            print(f"         inventou {achadas}")

    # O href que o site monta e `u` se comeca com http, senao 'https://'+u. Um
    # espaco ou um rotulo no meio quebra os dois. Era assim que 49 links iam para
    # o ar sem abrir nada.
    print("\n=== nenhum endereco recuperado pode ter espaco ou rotulo ===")
    import re
    for linha, cortada, _ in RECUPERA:
        for u in cr.recuperar(linha, cortada)[0]:
            href = u if re.match(r"^https?://", u, re.I) else "https://" + u
            if " " in href or re.search(r"^https://[a-z]+:", href, re.I):
                falhas += 1
                print(f"FALHA  href que nao abre: {href!r}")
    print("OK    todos abrem" if not falhas else "")

    print(f"\n{falhas} falha(s)")
    raise SystemExit(1 if falhas else 0)


if __name__ == "__main__":
    main()
