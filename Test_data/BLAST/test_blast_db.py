from tardigene.bioinformatics.blast_db import create_blast_db

genome_path = "Test_data/genomes/Hypsibius_exemplaris/genome.fna"

db_prefix = "Test_data/BLAST/databases/GCA_002082055.1/genome"

result = create_blast_db(genome_path, db_prefix)

print(result)