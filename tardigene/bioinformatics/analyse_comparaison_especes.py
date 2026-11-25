import gzip
from pathlib import Path
 
import pandas as pd
from Bio import SeqIO

#verif si fichier existe et renvoie son chemin
def _check_file(path, description):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"{description} introuvable : {path}")
    return path
 
#ouvre fichier .gz ou autre
def _open_text(path):
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rt")
    return open(path, "r")
    
    
#calcul du n50 a partir de liste de longueurs de seq
#trie de seq plus grande a plus petite puis addition jusqu'a atteindre moitie de taille du genome    
def compute_n50(lengths):
    if not lengths:
        return 0
    lengths = sorted(lengths, reverse=True)
    half_total = sum(lengths) / 2
    cumulative = 0
    for length in lengths:
        cumulative += length
        if cumulative >= half_total:
            return length
    return 0
 
#lis l'ensemble des stats du genome (taille, nbre de seq, N50, GC)
#utilisation de round pour arrondir (plus lisible) 
def genome_stats(genome_path):
    genome_path = _check_file(genome_path, "Fichier génome")
    lengths = []
    gc_count = 0
    acgt_count = 0
    with _open_text(genome_path) as handle:
        for record in SeqIO.parse(handle, "fasta"):
            seq = str(record.seq).upper()
            lengths.append(len(seq))
            g = seq.count("G")
            c = seq.count("C")
            gc_count += g + c
            acgt_count += g + c + seq.count("A") + seq.count("T")
    if not lengths:
        raise ValueError(f"Aucune séquence trouvée dans {genome_path}")
    return {
        "genome_size": sum(lengths),
        "n_sequences": len(lengths),
        "n50": compute_n50(lengths),
        "gc_percent": round(100 * gc_count / acgt_count, 2) if acgt_count else None,
    }
    
#compte genes dans fichier GFF avec pandas (utilise 3eme col, compte lignes ou type = "gene") 
def count_genes(gff_path, feature_type="gene"):
    gff_path = _check_file(gff_path, "Fichier d'annotation GFF")
    gff = pd.read_csv(
        gff_path,
        sep="\t",
        comment="#",          # ignore les lignes d'en-tête (##gff-version...)
        header=None,          # le GFF n'a pas de ligne de titres
        usecols=[2],          # on ne lit que la colonne "type"
        dtype=str,
        on_bad_lines="skip",  # ignore les éventuelles lignes mal formées
    )
    return int((gff[2] == feature_type).sum())
    

#compte seqs proteiques (.faa) avec Biopython
def count_proteins(proteins_path):
    proteins_path = _check_file(proteins_path, "Fichier protéique")
    with _open_text(proteins_path) as handle:
        return sum(1 for _ in SeqIO.parse(handle, "fasta"))
        
        
        
#regroupe especes dans dict + calcul densite genique     
def compute_indicators(genome_path, gff_path, proteins_path):
    indicators = genome_stats(genome_path)
    indicators["n_genes"] = count_genes(gff_path)
    indicators["n_proteins"] = count_proteins(proteins_path)
    size_mb = indicators["genome_size"] / 1000000
    indicators["protein_density"] = round(indicators["n_proteins"] / size_mb, 1)
    indicators["gene_density"] = round(indicators["n_genes"] / size_mb, 1)
    return indicators
    

#creation tableau de comparaison avec pandas (ligne/espece) a partir du dict
def build_comparison_table(species_files):
    rows = []
    for species, files in species_files.items():
        row = {"species": species}
        row.update(compute_indicators(files["genome"], files["gff"], files["proteins"]))
        rows.append(row)
    table = pd.DataFrame(rows).set_index("species")
    table["genome_size_mb"] = (table["genome_size"] / 1000000).round(1)
    table["n50_mb"] = (table["n50"] / 1000000).round(2)
    return table
