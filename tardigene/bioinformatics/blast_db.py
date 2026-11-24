import subprocess
from pathlib import Path


def create_blast_db(genome_path, db_prefix):
    genome_path = Path(genome_path)
    db_prefix = Path(db_prefix)
    # Vérifie si le génome existe
    if not genome_path.is_file():
        raise FileNotFoundError(f"Genome file not found: {genome_path}")
    # Crée le dossier de sortie si nécessaire
    db_prefix.parent.mkdir(parents=True, exist_ok=True)
    # Prépare la commande makeblastdb
    command = [
    "makeblastdb",
    "-in", str(genome_path),
    "-dbtype", "nucl",
    "-out", str(db_prefix),
    "-parse_seqids"
    ]
    # Exécute la commande makeblastdb
    subprocess.run(command, check=True)
    # Valide la base de données BLAST créée
    validate_blast_db(db_prefix)
    return db_prefix

def validate_blast_db(db_prefix):
    db_prefix = Path(db_prefix)
    command = [
        "blastdbcmd",
        "-db", str(db_prefix),
        "-dbtype", "nucl",
        "-info"
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"BLAST database validation failed: {e.stderr}"
        ) from e