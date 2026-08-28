# -*- coding: utf-8 -*-
"""Exercita o caminho de SUCESSO de promover_legislativo.py, numa copia.

Sem isto eu estaria entregando um script cuja trava eu vi disparar e cujo
caminho feliz nunca rodou — que foi o erro de hoje com a conferencia de UF que
passava por vacuidade.

Simula a revisao humana de PE: marca itens como conferidos, com concordancia
alta, e conferre que os quatro porteiros produzem o que prometem. O acervo de
verdade NAO e tocado: tudo acontece numa copia temporaria.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

RAIZ = pathlib.Path(r"c:\Users\BOC277 - Usuario\Documents\politica")
tmp = pathlib.Path(tempfile.mkdtemp(prefix="ponte-teste-"))
copia = tmp / "politica"

# copia so o necessario: scripts + dados
copia.mkdir()
for f in RAIZ.glob("*.py"):
    shutil.copy2(f, copia / f.name)
shutil.copytree(RAIZ / "dados", copia / "dados")
print(f"copia em {copia}")

pe = copia / "dados" / "pe"
f = pe / "_coleta_legislativa.json"
d = json.loads(f.read_text(encoding="utf-8"))

# --- simula 25 revisoes humanas: 23 concordando, 2 discordando --------------
n = 0
for r in d["registros"]:
    cl = r.get("_classificacao") or {}
    if cl.get("por") != "modelo" or n >= 25:
        continue
    n += 1
    concordou = n > 2                      # as duas primeiras discordam
    r["_classificacao"] = {
        "temas": cl["temas"] if concordou else ["t10"],
        "motivo": "", "por": "humano", "por_quem": "teste-automatizado",
        "decidido_em": "2026-08-28",
        "modelo_propos": cl["temas"],
        "concordou": concordou,
    }
f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"simuladas {n} revisoes (23 concordando, 2 discordando = 92%)")

env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
r = subprocess.run([sys.executable, "promover_legislativo.py", "--uf", "PE", "--gravar"],
                   cwd=copia, capture_output=True, text=True, env=env)
print("\n--- saida do script ---")
print(r.stdout or r.stderr)

if r.returncode != 0:
    print("FALHOU: o caminho de sucesso nao passou")
    raise SystemExit(1)

# --- confere o que foi gravado ---------------------------------------------
pub = json.loads((pe / "registros_legislativos.json").read_text(encoding="utf-8"))
falhas = []

if not pub.get("registros"):
    falhas.append("nada foi promovido")
tot = pub.get("totais_por_candidatura") or {}
if not tot:
    falhas.append("totais_por_candidatura vazio")
for cid, t in tot.items():
    if "periodo_inicio" not in t or "periodo_fim" not in t:
        falhas.append(f"{cid} sem periodo")
    if str(t.get("periodo_inicio")) not in (t.get("_como_exibir") or ""):
        falhas.append(f"{cid}: _como_exibir nao traz o periodo")
aus = pub.get("ausencias") or []
if not aus:
    falhas.append("nenhuma ausencia registrada — PE tem 8 candidaturas sem mandato")
for x in aus:
    if x["motivo"] not in ("sem_mandato_federal", "nao_localizamos"):
        falhas.append(f"motivo de ausencia estranho: {x['motivo']}")
    if not x.get("_texto"):
        falhas.append(f"{x['id_candidatura']} sem texto de ausencia")
conf = pub.get("_confianca_da_classificacao") or {}
if abs(conf.get("taxa_de_concordancia", 0) - 0.92) > 0.01:
    falhas.append(f"taxa gravada errada: {conf.get('taxa_de_concordancia')}")

# nenhuma ementa opaca pode ter entrado
import re
sys.path.insert(0, str(copia))
import promover_legislativo as pl
op = [r_ for r_ in pub["registros"]
      if not pl.explica(r_.get("ementa", "")) and not (r_.get("_contexto") or "").strip()]
if op:
    falhas.append(f"{len(op)} ementa(s) opaca(s) entraram: {op[0].get('ementa','')[:60]}")

print("\n--- conferencia ---")
print(f"  registros promovidos: {len(pub['registros'])}")
print(f"  candidaturas com total+periodo: {len(tot)}")
for cid, t in list(tot.items())[:4]:
    print(f"      {cid.split('-', 3)[-1]:20} {t['_como_exibir']}")
print(f"  ausencias com motivo: {len(aus)}")
for x in aus[:2]:
    print(f"      {x['id_candidatura'].split('-', 3)[-1]:20} {x['motivo']}")
print(f"  taxa de concordancia gravada: {conf.get('taxa_de_concordancia')}")
print(f"  ementas opacas que entraram: {len(op)}")

shutil.rmtree(tmp, ignore_errors=True)
if falhas:
    print("\nFALHAS:")
    for x in falhas:
        print("  -", x)
    raise SystemExit(1)
print("\n=== a ponte funciona, e os quatro porteiros fazem o que prometem ===")
