import re
 
import requests
 
NCBI_API = "https://api.ncbi.nlm.nih.gov/datasets/v2"
NGDC_API = "https://ngdc.cncb.ac.cn/gwh/api/public"
NGDC_PAGE = "https://ngdc.cncb.ac.cn/gwh/Assembly/{id}/show"
ENSEMBL_API = "https://rest.ensembl.org"
 
HEADERS = {"Accept": "application/json", "User-Agent": "TardiGene/1.0"}
TIMEOUT = (30, 120)
 
 

def _empty_statistics():
    return {
        "species_name": None, "accession": None, "assembly_level": None,
        "genome_size": None, "n_sequences": None, "n50": None,
        "gc": None, "genes": None, "busco": None,
    }
 
 
def _pick(data, *keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        if data.get(key) not in (None, ""):
            return data[key]
    return None
 
 
def _to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except ValueError:
        return None
 
 
def to_number(value):
    if value in (None, "", "NA"):
        return None
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except ValueError:
        return None
 
 
def compute_n50(lengths):
    lengths = sorted(lengths, reverse=True)
    half_total = sum(lengths) / 2
    cumulative = 0
    for length in lengths:
        cumulative += length
        if cumulative >= half_total:
            return length
    return None
 
 

# NCBI

 
def parse_ncbi_report(data):
    """Extrait les statistiques d'une réponse NCBI Datasets (dataset_report)."""
    reports = data.get("reports") or []
    if not reports:
        raise ValueError("Accession introuvable dans NCBI.")
    report = reports[0]
    organism = _pick(report, "organism") or {}
    info = _pick(report, "assembly_info", "assemblyInfo") or {}
    stats = _pick(report, "assembly_stats", "assemblyStats") or {}
    annotation = _pick(report, "annotation_info", "annotationInfo") or {}
    gene_counts = _pick(_pick(annotation, "stats") or {}, "gene_counts", "geneCounts") or {}
    busco = _pick(annotation, "busco") or {}
    result = _empty_statistics()
    result["species_name"] = _pick(organism, "organism_name", "organismName")
    result["accession"] = _pick(report, "accession")
    result["assembly_level"] = _pick(info, "assembly_level", "assemblyLevel")
    result["genome_size"] = _to_int(_pick(stats, "total_sequence_length", "totalSequenceLength"))
    result["n_sequences"] = _to_int(_pick(stats, "number_of_scaffolds", "numberOfScaffolds",
                                          "number_of_contigs", "numberOfContigs"))
    result["n50"] = _to_int(_pick(stats, "scaffold_n50", "scaffoldN50", "contig_n50", "contigN50"))
    result["gc"] = to_number(_pick(stats, "gc_percent", "gcPercent"))
    # Gènes codant des protéines (seulement si l'assemblage est annoté par NCBI)
    result["genes"] = _to_int(_pick(gene_counts, "protein_coding", "proteinCoding"))
    # BUSCO : NCBI donne une fraction (0.95) -> pourcentage (95.0)
    complete = to_number(_pick(busco, "complete"))
    result["busco"] = round(complete * 100, 1) if complete is not None and complete <= 1 else complete
    return result
 
 
def fetch_ncbi_statistics(accession):
    response = requests.get(f"{NCBI_API}/genome/accession/{accession}/dataset_report",
                            headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return parse_ncbi_report(response.json())
 
 

# NGDC-CNCB

 
def parse_ngdc_page(html):
    text = re.sub(r"<[^>]+>", " ", html)      # retire les balises HTML
    text = re.sub(r"\s+", " ", text)           # espaces multiples -> un seul
    def find(pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1) if match else None
    result = _empty_statistics()
    result["genome_size"] = _to_int(find(r"Genome size \(bp\)\s*([\d,]+)"))
    result["gc"] = to_number(find(r"GC content\s*([\d.]+)\s*%"))
    result["n_sequences"] = _to_int(find(r"Genome sequence No\.\s*([\d,]+)"))
    result["n50"] = _to_int(find(r"Genome sequence N50 \(bp\)\s*([\d,]+)"))
    result["genes"] = _to_int(find(r"(?:Number of genes|Gene number|Gene No\.)\s*(?:\(\w+\))?\s*([\d,]+)"))
    return result
 
 
def fetch_ngdc_statistics(accession):
    response = requests.get(f"{NGDC_API}/assembly/{accession}", headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    metadata = response.json()
    page = requests.get(NGDC_PAGE.format(id=metadata["id"]),
                        headers={"User-Agent": HEADERS["User-Agent"]}, timeout=TIMEOUT)
    page.raise_for_status()
    result = parse_ngdc_page(page.text)
    result["species_name"] = metadata.get("organism")
    result["accession"] = metadata.get("assemblyAccession") or accession
    result["assembly_level"] = metadata.get("assemblyLevel")
    return result
 

# Ensembl Metazoa

 
def parse_ensembl_assembly(data):
    lengths = [region["length"] for region in data.get("top_level_region", [])
               if isinstance(region, dict) and region.get("length")]
    result = _empty_statistics()
    result["accession"] = data.get("assembly_accession")
    result["assembly_level"] = data.get("assembly_level")
    result["genome_size"] = _to_int(data.get("golden_path")) or (sum(lengths) if lengths else None)
    result["n_sequences"] = len(lengths) or None
    result["n50"] = compute_n50(lengths)
    return result
 
 
def fetch_ensembl_statistics(ensembl_species):
    response = requests.get(f"{ENSEMBL_API}/info/assembly/{ensembl_species}",
                            headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return parse_ensembl_assembly(response.json())
 
 

# Point d'entrée unique

 
def fetch_statistics(source, identifier):
    if source == "NCBI":
        return fetch_ncbi_statistics(identifier)
    if source == "NGDC":
        return fetch_ngdc_statistics(identifier)
    if source == "ENSEMBL":
        return fetch_ensembl_statistics(identifier)
    raise ValueError(f"Source inconnue : {source}")
 
