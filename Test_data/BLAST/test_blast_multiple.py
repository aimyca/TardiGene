from tardigene.bioinformatics.blast import run_blast_multiple

query_path = "Test_data/BLAST/queries/test_query.fasta"

databases = {
    "Hypsibius exemplaris":
        "Test_data/BLAST/databases/GCA_002082055.1/genome"
}

output_dir = "Test_data/BLAST/results/multiple"

results = run_blast_multiple(
    query_path,
    databases,
    output_dir
)

print(f"Nombre total d'alignements : {len(results)}")

for hit in results:
    print(
        hit["species"],
        hit["sseqid"],
        hit["pident"],
        hit["qcovhsp"]
    )