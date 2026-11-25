"""
TardiGene - Pré-analyse OrthoFinder
===================================

Regroupe les gènes des espèces de tardigrades en familles (orthogroupes).
Lancé UNE FOIS, hors de l'application Django (pré-traitement).
Les résultats (TSV) sont ensuite importés dans la base avec
`python manage.py import_orthofinder`.

"""

import argparse
import gzip
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd
from Bio import SeqIO

# Motifs des fichiers de protéines produits par web.py, selon la source
PROTEIN_PATTERNS = ("*_protein.faa.gz", "*.pep.all.fa.gz", "*rotein*.f*a.gz", "*.faa", "*.faa.gz")
GFF_PATTERNS = ("*.gff.gz", "*.gff3.gz", "*.gff", "*.gff3")


# ---------------------------------------------------------------------------
# 1. Préparation des protéomes à partir de data/
# ---------------------------------------------------------------------------

def _open(path):
    """Ouvre un fichier texte, compressé (.gz) ou non."""
    path = Path(path)
    return gzip.open(path, "rt") if path.suffix == ".gz" else open(path)


def _first_match(folder, patterns):
    for pattern in patterns:
        found = sorted(folder.glob(pattern))
        if found:
            return found[0]
    return None


def protein_to_gene(gff):
    """Lit le GFF et renvoie {accession protéine: gène} (sert à retirer les isoformes)."""
    mapping = {}
    if gff is None:
        return mapping
    with _open(gff) as f:
        for line in f:
            if line.startswith("#"):
                continue
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 9 or cols[2] != "CDS":
                continue
            p = re.search(r"protein_id=([^;]+)", cols[8])
            # le gène d'abord : Parent= désigne l'ARNm (une isoforme), pas le gène
            g = (re.search(r"(?:^|;)gene=([^;]+)", cols[8])
                 or re.search(r"(?:^|;)locus_tag=([^;]+)", cols[8]))
            if p and g:
                mapping[p.group(1)] = g.group(1)
    return mapping


def clean_proteome(faa, out_faa, prot2gene=None):
    """
    Garde la protéine la plus longue par gène (supprime les isoformes)
    et réécrit les en-têtes avec la seule accession.
    Gène d'une protéine : d'après le GFF (NCBI), sinon d'après 'gene:XXX'
    dans l'en-tête (Ensembl), sinon 1 protéine = 1 gène.
    """
    prot2gene = prot2gene or {}
    best = {}
    n_in = 0
    with _open(faa) as handle:
        for rec in SeqIO.parse(handle, "fasta"):
            n_in += 1
            m = re.search(r"\bgene:(\S+)", rec.description)
            gene = prot2gene.get(rec.id) or (m.group(1) if m else rec.id)
            if gene not in best or len(rec.seq) > len(best[gene].seq):
                best[gene] = rec
    for rec in best.values():
        rec.description = ""
    SeqIO.write(best.values(), out_faa, "fasta")
    print(f"  {out_faa.name} : {n_in} protéines -> {len(best)} gardées (1 par gène)")
    return len(best)


def collect(data_dir, out_dir):
    """
    Parcourt data/<Espece>/<Accession>/ et écrit 1 fichier <Espece>.faa par espèce.
    Le nom du fichier (ex. Hypsibius_exemplaris) devient le nom de l'espèce
    dans les résultats OrthoFinder, puis dans la base (Record.scientific_name).
    """
    data_dir, out_dir = Path(data_dir).expanduser(), Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    for species_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        # Un assemblage avec protéines ; s'il y en a plusieurs, on prend le premier
        candidates = [a for a in sorted(species_dir.iterdir())
                      if a.is_dir() and _first_match(a, PROTEIN_PATTERNS)]
        if not candidates:
            print(f"[ignoré] {species_dir.name} : aucun fichier de protéines (faa)")
            continue
        assembly = candidates[0]
        if len(candidates) > 1:
            print(f"[info] {species_dir.name} : {len(candidates)} assemblages, "
                  f"utilisation de {assembly.name}")

        faa = _first_match(assembly, PROTEIN_PATTERNS)
        gff = _first_match(assembly, GFF_PATTERNS)
        print(f"[{species_dir.name}] {assembly.name} ({faa.name}"
              f"{', GFF : ' + gff.name if gff else ', pas de GFF'})")
        clean_proteome(faa, out_dir / f"{species_dir.name}.faa", protein_to_gene(gff))

    n = len(list(out_dir.glob("*.faa")))
    print(f"{n} protéomes prêts dans {out_dir}")
    if n < 2:
        raise SystemExit("Il faut au moins 2 espèces avec un protéome pour lancer OrthoFinder.")
    return out_dir


# ---------------------------------------------------------------------------
# 2. Lancement d'OrthoFinder
# ---------------------------------------------------------------------------

def run_orthofinder(proteomes_dir, threads=4, full=False):
    """
    Lance OrthoFinder. Par défaut (-og), s'arrête après le calcul des familles (~20 min).
    full=True : analyse complète avec arbres de gènes et arbre des espèces (~1 h).
    """
    proteomes_dir = Path(proteomes_dir).expanduser()
    old = proteomes_dir / "OrthoFinder"
    if old.exists():
        shutil.rmtree(old)  # évite de mélanger avec un ancien run
    cmd = ["orthofinder", "-f", str(proteomes_dir), "-t", str(threads)]
    if not full:
        cmd.append("-og")
    subprocess.run(cmd, check=True)
    results = sorted((proteomes_dir / "OrthoFinder").glob("Results_*"))[-1]
    print(f"Résultats : {results}")
    return results


def assign_new_species(new_proteomes_dir, core_results_dir, threads=4):
    """Ajoute une nouvelle espèce aux familles existantes, sans tout recalculer."""
    subprocess.run(
        ["orthofinder", "--assign", str(Path(new_proteomes_dir).expanduser()),
         "--core", str(Path(core_results_dir).expanduser()), "-t", str(threads)],
        check=True,
    )


# ---------------------------------------------------------------------------
# 3. Lecture des résultats et statistiques
# ---------------------------------------------------------------------------

def _find(results_dir, name):
    """Trouve un fichier de résultats, préfixé 'MCL_' (mode -og) ou non (run complet)."""
    results_dir = Path(results_dir).expanduser()
    for f in (f"Orthogroups/{name}", f"Orthogroups/MCL_{name}"):
        if (results_dir / f).exists():
            return results_dir / f
    raise FileNotFoundError(f"{name} introuvable dans {results_dir}")


def read_gene_counts(results_dir):
    """Une ligne par famille, une colonne par espèce, valeur = nombre de copies."""
    df = pd.read_csv(_find(results_dir, "Orthogroups.GeneCount.tsv"), sep="\t", index_col=0)
    return df.drop(columns="Total", errors="ignore")


def read_unassigned(results_dir):
    """Gènes qui ne sont dans aucune famille partagée."""
    return pd.read_csv(_find(results_dir, "Orthogroups_UnassignedGenes.tsv"), sep="\t", index_col=0)


def clean_id(gene):
    """
    Ramène un identifiant OrthoFinder à l'accession protéique.
      'OQV11389.1 hypothetical protein ...'  -> 'OQV11389.1'
      'gi|284811953|gb|ADB96857.1|'          -> 'ADB96857.1'  (ancien format NCBI)
    """
    gene = gene.strip().split()[0]
    if "|" in gene:
        parts = [p for p in gene.split("|") if p]
        return parts[3] if len(parts) >= 4 else parts[-1]
    return gene


def read_orthogroups(results_dir):
    """Table longue (orthogroupe, espèce, gène) : sert à l'import dans la base."""
    df = pd.read_csv(_find(results_dir, "Orthogroups.tsv"), sep="\t", index_col=0)
    rows = []
    for og, row in df.iterrows():
        for species, genes in row.dropna().items():
            for gene in genes.split(", "):
                if gene.strip():
                    rows.append({"orthogroup": og, "species": species, "gene": clean_id(gene)})
    return pd.DataFrame(rows)


def stats(results_dir):
    gc = read_gene_counts(results_dir)
    un = read_unassigned(results_dir)
    sp = list(gc.columns)
    pres = gc > 0
    n_sp = pres.sum(axis=1)

    print(f"\nNombre d'orthogroupes : {len(gc)}")
    print(f"Partagés par toutes les espèces ({len(sp)}) : {(n_sp == len(sp)).sum()}")
    print(f"Présents dans 1 seule espèce : {(n_sp == 1).sum()}\n")
    for s in sp:
        a = int(gc[s].sum())
        u = int(un[s].notna().sum()) if s in un.columns else 0
        t = a + u
        only = int((pres[s] & (n_sp == 1)).sum())
        print(f"{s}: {t} gènes, {a} dans un orthogroupe ({100 * a / t:.1f}%), "
              f"{u} non assignés, {only} orthogroupes propres à l'espèce")
    print()
    for i, x in enumerate(sp):
        for y in sp[i + 1:]:
            print(f"{x} & {y} : {(pres[x] & pres[y]).sum()} orthogroupes en commun")
    print("\nFamilles les plus grandes :")
    top = gc.assign(Total=gc.sum(axis=1)).sort_values("Total", ascending=False)
    print(top.head(5).to_string())


# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="TardiGene - pré-analyse OrthoFinder")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("collect", help="préparer les protéomes à partir de data/ (web.py)")
    pc.add_argument("--data", default="data")
    pc.add_argument("--out", required=True)

    pr = sub.add_parser("run", help="lancer OrthoFinder")
    pr.add_argument("--proteomes", required=True)
    pr.add_argument("--threads", type=int, default=4)
    pr.add_argument("--full", action="store_true", help="analyse complète avec arbres (~1 h)")

    ps = sub.add_parser("stats", help="statistiques d'un dossier Results_xxx")
    ps.add_argument("--results", required=True)

    pa = sub.add_parser("all", help="collect + run + stats")
    pa.add_argument("--data", default="data")
    pa.add_argument("--out", required=True)
    pa.add_argument("--threads", type=int, default=4)
    pa.add_argument("--full", action="store_true")

    a = p.parse_args()
    if a.cmd == "collect":
        collect(a.data, a.out)
    elif a.cmd == "run":
        run_orthofinder(a.proteomes, a.threads, a.full)
    elif a.cmd == "stats":
        stats(a.results)
    else:
        d = collect(a.data, a.out)
        stats(run_orthofinder(d, a.threads, a.full))


if __name__ == "__main__":
    main()