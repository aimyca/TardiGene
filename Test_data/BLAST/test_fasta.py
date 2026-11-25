from pathlib import Path
from tempfile import TemporaryDirectory
from tardigene.bioinformatics.fasta_utils import validate_fasta

test_cases = {
    "valid_sequence": ">seq1\nATGCGTACGT\n",
    "lowercase_sequence": ">seq1\natgcgtacgt\n",
    "ambiguous_sequence": ">seq1\nATGCNNRY\n",
    "invalid_sequence": ">seq1\nATGCXYZ\n",
    "empty_sequence": ">seq1\n",
    "empty_file": "",
    "multiple_sequences": ">seq1\nATGC\n>seq2\nGCTA\n",
    "invalid_format": "ATGCGTACGT\n"
}

with TemporaryDirectory() as temp_dir:

    for name, content in test_cases.items():

        fasta_path = Path(temp_dir) / f"{name}.fasta"

        fasta_path.write_text(content, encoding="utf-8")

        try:
            records = validate_fasta(
                fasta_path,
                single_sequence=True
            )

            print(f"{name}: ACCEPTED")

        except ValueError as e:
            print(f"{name}: REJECTED - {e}")