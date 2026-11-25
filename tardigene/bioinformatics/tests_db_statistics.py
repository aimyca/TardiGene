import unittest
 
from .db_statistics import (
    compute_n50,
    parse_ensembl_assembly,
    parse_ncbi_report,
    parse_ngdc_page,
)
 
# Réponse NCBI Datasets (format documenté, valeurs de H. exemplaris)
NCBI_REPORT = {
    "reports": [{
        "accession": "GCA_002082055.1",
        "organism": {"organism_name": "Hypsibius exemplaris", "tax_id": 2072580},
        "assembly_info": {"assembly_level": "Scaffold", "assembly_name": "nHd_3.1"},
        "assembly_stats": {
            "total_sequence_length": "104154999",
            "number_of_scaffolds": 1421,
            "scaffold_n50": 342180,
            "contig_n50": 76800,
            "gc_percent": 45.5,
        },
    }]
}
 
# Même réponse avec une annotation NCBI (gènes codants + BUSCO), noms en camelCase
NCBI_REPORT_ANNOTATED = {
    "reports": [{
        "accession": "GCF_000000001.1",
        "organism": {"organismName": "Espece test"},
        "assemblyInfo": {"assemblyLevel": "Chromosome"},
        "assemblyStats": {"totalSequenceLength": "1000000", "numberOfScaffolds": 10,
                          "scaffoldN50": 200000, "gcPercent": 40},
        "annotationInfo": {"stats": {"geneCounts": {"proteinCoding": 12000, "total": 15000}},
                           "busco": {"complete": 0.952}},
    }]
}
 
# Extrait de la page web GWH de H. henanensis (section "Statistics of Genome Assembly")
NGDC_PAGE = """
<h3>Statistics of Genome Assembly</h3>
<table>
<tr><td>Genome size (bp)</td><td>112,602,748</td></tr>
<tr><td>GC content</td><td>40.65%</td></tr>
<tr><td>Chromosomes sequence No.</td><td>6</td></tr>
<tr><td>Genome sequence No.</td><td>14</td></tr>
<tr><td>Genome sequence N50 (bp)</td><td>19,070,273</td></tr>
</table>
"""
 
# Réponse Ensembl /info/assembly : 3 séquences de 6, 4 et 2 pb
ENSEMBL_ASSEMBLY = {
    "assembly_accession": "GCA_000000002.1",
    "top_level_region": [
        {"name": "s1", "length": 6, "coord_system": "primary_assembly"},
        {"name": "s2", "length": 4, "coord_system": "primary_assembly"},
        {"name": "s3", "length": 2, "coord_system": "primary_assembly"},
    ],
}
 
 
class NcbiTests(unittest.TestCase):
 
    def test_statistiques_assemblage(self):
        stats = parse_ncbi_report(NCBI_REPORT)
        self.assertEqual(stats["species_name"], "Hypsibius exemplaris")
        self.assertEqual(stats["assembly_level"], "Scaffold")
        self.assertEqual(stats["genome_size"], 104154999)
        self.assertEqual(stats["n_sequences"], 1421)
        self.assertEqual(stats["n50"], 342180)        # N50 des scaffolds, pas des contigs
        self.assertEqual(stats["gc"], 45.5)
        self.assertIsNone(stats["genes"])             # pas d'annotation NCBI
        self.assertIsNone(stats["busco"])
 
    def test_annotation_et_camelcase(self):
        stats = parse_ncbi_report(NCBI_REPORT_ANNOTATED)
        self.assertEqual(stats["species_name"], "Espece test")
        self.assertEqual(stats["genes"], 12000)       # gènes codants seulement
        self.assertEqual(stats["busco"], 95.2)        # fraction -> pourcentage
 
    def test_accession_inconnue(self):
        with self.assertRaises(ValueError):
            parse_ncbi_report({"reports": []})
 
 
class NgdcTests(unittest.TestCase):
 
    def test_page_gwh(self):
        stats = parse_ngdc_page(NGDC_PAGE)
        self.assertEqual(stats["genome_size"], 112602748)
        self.assertEqual(stats["gc"], 40.65)
        self.assertEqual(stats["n_sequences"], 14)
        self.assertEqual(stats["n50"], 19070273)
 
    def test_page_sans_statistiques(self):
        stats = parse_ngdc_page("<html>Page vide</html>")
        self.assertIsNone(stats["genome_size"])
        self.assertIsNone(stats["n50"])
 
 
class EnsemblTests(unittest.TestCase):
 
    def test_longueurs_des_sequences(self):
        stats = parse_ensembl_assembly(ENSEMBL_ASSEMBLY)
        self.assertEqual(stats["genome_size"], 12)
        self.assertEqual(stats["n_sequences"], 3)
        self.assertEqual(stats["n50"], 6)
        self.assertEqual(stats["accession"], "GCA_000000002.1")
        self.assertIsNone(stats["gc"])                # non fourni par Ensembl ici
 
    def test_n50(self):
        self.assertEqual(compute_n50([2, 6, 4]), 6)
        self.assertIsNone(compute_n50([]))
 
 
if __name__ == "__main__":
    unittest.main()
