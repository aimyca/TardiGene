from pathlib import Path
from Bio import SeqIO

DNA_ALPHABET = set("ACGTRYSWKMBDHVN")


def validate_fasta(fasta_path, single_sequence=False):
    fasta_path = Path(fasta_path)
    if not fasta_path.is_file():
        raise FileNotFoundError(f" Fichier FASTA introuvable: {fasta_path}")
    records = list(SeqIO.parse(fasta_path, "fasta"))
    if not records:
        raise ValueError("Aucune séquence FASTA trouvée")
    if single_sequence and len(records) != 1:
        raise ValueError("Une seule séquence FASTA est requise")
    for record in records:
        sequence = str(record.seq).upper()
        if not sequence:
            raise ValueError(f" séquence vide: {record.id}")
        invalid_chars = set(sequence) - DNA_ALPHABET
        if invalid_chars:
            raise ValueError(
                f"Caractères invalides dans {record.id}: "
                f"{', '.join(sorted(invalid_chars))}"
            )
    return records
