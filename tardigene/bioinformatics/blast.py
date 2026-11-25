import subprocess
import csv
from pathlib import Path
from .blast_db import validate_blast_db
from .fasta_utils import validate_fasta

BLAST_COLUMNS = [
    "qseqid", "sseqid", "pident", "length",
    "qstart", "qend", "sstart", "send", "evalue",
    "bitscore", "qcovhsp", "sstrand", "sseq"
]

BLAST_INT_COLUMNS = ["length", "qstart", "qend", "sstart", "send"]
BLAST_FLOAT_COLUMNS = ["pident", "evalue", "bitscore", "qcovhsp"]

BLAST_TASKS = {"blastn", "blastn-short", "megablast", "dc-megablast"}

def validate_blast_parameters(evalue, max_target_seqs, perc_identity, task, num_threads):
    if not evalue > 0:
        raise ValueError("L'E-value doit être positive")
    if not isinstance(max_target_seqs, int) or max_target_seqs < 1:
        raise ValueError("Le nombre maximum de séquences cibles doit être un entier positif")
    if not 0 <= perc_identity <= 100:
        raise ValueError("Le pourcentage d'identité doit être comprise entre 0 et 100")
    if task not in BLAST_TASKS:
        raise ValueError(f"Stratégie BLAST invalide: {task}")
    if not isinstance(num_threads, int) or num_threads < 1:
        raise ValueError("Le nombre de threads doit être un entier positif")
    
def run_blast(query_path, db_prefix, output_path, evalue=1e-5, max_target_seqs=10, perc_identity=0, task="blastn", num_threads=2):
    query_path = Path(query_path)
    db_prefix = Path(db_prefix)
    output_path = Path(output_path)
    # Validation des paramètres BLAST
    validate_blast_parameters(evalue, max_target_seqs, perc_identity, task, num_threads)
    # Vérification du fichier FASTA
    validate_fasta(query_path, single_sequence=True)
    # Vérification de la base BLAST
    validate_blast_db(db_prefix)
    # Création du dossier de sortie
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Définition du format de sortie CSV
    output_format = "10 " + " ".join(BLAST_COLUMNS)
    # Construction de la commande BLAST
    command = [
        "blastn",
        "-query", str(query_path),
        "-db", str(db_prefix),
        "-out", str(output_path),
        "-evalue", str(evalue),
        "-max_target_seqs", str(max_target_seqs),
        "-perc_identity", str(perc_identity),
        "-task", task,
        "-num_threads", str(num_threads),
        "-outfmt", output_format
    ]
    # Exécution de BLASTn
    try:
        subprocess.run(command,check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Échec de la recherche BLAST: {e.stderr}"
        ) from e
    return output_path

def parse_blast_results(output_path):
    output_path = Path(output_path)
    if not output_path.is_file():
        raise FileNotFoundError(f"Fichier de résultats BLAST introuvable: {output_path}")
    results = []
    with output_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, fieldnames=BLAST_COLUMNS)
        for line_number, row in enumerate(reader, start=1):
            if None in row or None in row.values():
                raise ValueError(f"Structure du CSV BLAST invalide à la ligne {line_number}")
            try:
                for column in BLAST_INT_COLUMNS:
                    row[column] = int(row[column])
                for column in BLAST_FLOAT_COLUMNS:
                    row[column] = float(row[column])
            except ValueError as e:
                raise ValueError(f"Valeur numérique invalide à la ligne {line_number}: {e}") from e
            results.append(row)
    return results

def run_blast_multiple(query_path, databases, output_dir, evalue=1e-5, max_target_seqs=10, perc_identity=0, task="blastn", num_threads=2):
    output_dir = Path(output_dir)
    if not databases:
        raise ValueError("Aucune base BLAST sélectionnée")
    output_dir.mkdir(parents=True, exist_ok=True)
    all_results = []
    for index, (species, db_prefix) in enumerate(
        databases.items(), start=1
    ):
        output_path = output_dir / f"blast_{index}.csv"
        run_blast(query_path=query_path, db_prefix=db_prefix, output_path=output_path, evalue=evalue, max_target_seqs=max_target_seqs, perc_identity=perc_identity, task=task, num_threads=num_threads)
        hits = parse_blast_results(output_path)
        for hit in hits:
            hit["species"] = species
        all_results.extend(hits)
    return all_results