from tardigene.bioinformatics.blast import run_blast, parse_blast_results

query_path = "Test_data/BLAST/queries/test_query.fasta"

db_prefix = "Test_data/BLAST/databases/GCA_002082055.1/genome"

output_path = "Test_data/BLAST/results/test_results.csv"

result = run_blast(query_path, db_prefix, output_path)

print(f"BLAST results saved in: {result}")

hits = parse_blast_results(output_path)

print(f"Number of alignments: {len(hits)}")

if hits:
    print(hits[0])