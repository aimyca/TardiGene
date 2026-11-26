"""
TardiGene - Recherche et récupération de données biologiques
Sources : NCBI, NGDC-CNCB et Ensembl Metazoa
"""

import os
import re
import json
import gzip
import ftplib
import time
import requests

from urllib.parse import quote, urljoin, urlparse
from utils import is_valid_gzip, is_allowed_url


# Configuration

NCBI_API = "https://api.ncbi.nlm.nih.gov/datasets/v2"
NCBI_FTP = "https://ftp.ncbi.nlm.nih.gov"
NGDC_API = "https://ngdc.cncb.ac.cn/gwh/api/public"
ENSEMBL_API = "https://rest.ensembl.org"
ENSEMBL_FTP = "https://ftp.ensemblgenomes.ebi.ac.uk/pub/metazoa/current"

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "TardiGene/1.0"
}

TIMEOUT = (30, 180)
FTP_TIMEOUT = 60

FILE_TYPES = ("fna", "gff", "faa")

MAX_FAILURES_WITHOUT_PROGRESS = 3
PAUSE_BETWEEN_ATTEMPTS = 5


# Fonctions communes

def _request_json(url, params=None):
    """Effectue une requête API et retourne les données JSON."""

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=TIMEOUT
    )
    response.raise_for_status()

    return response.json()


def _normalize_assembly(
    source,
    species,
    accession,
    assembly_name=None,
    assembly_level=None,
    size=None,
    release_date=None,
    bioproject=None,
    files=None,
    extra=None
):
    """Uniformise les métadonnées des différentes bases."""

    return {
        "source": source,
        "species": species,
        "accession": accession,
        "assembly_name": assembly_name,
        "assembly_level": assembly_level,
        "size": size,
        "release_date": release_date,
        "bioproject": bioproject,
        "files": files or {kind: [] for kind in FILE_TYPES},
        "extra": extra or {}
    }


# NCBI

def search_ncbi(species):
    """Recherche les assemblages NCBI à partir du nom scientifique."""

    species = species.strip()

    if not species:
        raise ValueError("Le nom de l'espèce est obligatoire.")

    url = (
        f"{NCBI_API}/genome/taxon/"
        f"{quote(species, safe='')}/dataset_report"
    )

    data = _request_json(url)
    results = []

    for report in data.get("reports", []):
        organism = report.get("organism", {})
        info = report.get("assembly_info", {})
        stats = report.get("assembly_stats", {})

        bioproject = info.get("bioproject_accession")

        if not bioproject:
            for item in info.get("bioproject_lineage", []):
                projects = item.get("bioprojects", [])

                if projects:
                    bioproject = projects[0].get("accession")
                    break

        assembly = _normalize_assembly(
            source="NCBI",
            species=organism.get("organism_name", species),
            accession=report.get("accession"),
            assembly_name=info.get("assembly_name"),
            assembly_level=info.get("assembly_level"),
            size=stats.get("total_sequence_length"),
            release_date=info.get("release_date"),
            bioproject=bioproject,
            extra={"raw_assembly_info": info}
        )

        results.append(assembly)

    return results


def _ncbi_ftp_path(accession, assembly_name):
    """Construit le chemin FTP d'un assemblage NCBI."""

    if not accession or not assembly_name:
        raise ValueError("Accession ou nom d'assemblage manquant.")

    prefix, number = accession.split("_", 1)
    number = number.split(".")[0]

    groups = [
        number[i:i + 3]
        for i in range(0, len(number), 3)
    ]

    return (
        "/genomes/all/"
        + prefix + "/"
        + "/".join(groups) + "/"
        + accession + "_" + assembly_name
    )


def _inspect_ncbi(assembly: dict):
    """Inspecte le répertoire FTP NCBI et identifie les fichiers."""

    accession = assembly["accession"]
    assembly_name = assembly["assembly_name"]
    path = _ncbi_ftp_path(accession, assembly_name)

    result = {
        "fna": [],
        "gff": [],
        "faa": [],
        "gbff": [],
        "feature_count": [],
        "feature_count_data": None
    }

    ftp = ftplib.FTP(
        "ftp.ncbi.nlm.nih.gov",
        timeout=FTP_TIMEOUT
    )

    try:
        ftp.login()
        ftp.cwd(path)
        names = ftp.nlst()

        expected_fna = (
            f"{accession}_{assembly_name}_genomic.fna.gz"
        )

        if expected_fna in names:
            result["fna"].append(expected_fna)

        suffixes = {
            "gff": "_genomic.gff.gz",
            "faa": "_protein.faa.gz",
            "gbff": "_genomic.gbff.gz"
        }

        for kind, suffix in suffixes.items():
            result[kind] = [
                name for name in names
                if name.endswith(suffix)
            ]

        result["feature_count"] = [
            name for name in names
            if name.endswith((
                "_feature_count.txt",
                "_feature_count.txt.gz"
            ))
        ]

        if result["feature_count"]:
            filename = result["feature_count"][0]
            buffer = bytearray()

            ftp.retrbinary("RETR " + filename, buffer.extend)
            content = bytes(buffer)

            if filename.endswith(".gz"):
                content = gzip.decompress(content)

            rows = []

            for line in content.decode("utf-8").splitlines():
                if not line or line.startswith("#"):
                    continue

                columns = line.split("\t")

                if (
                    len(columns) >= 7
                    and columns[0] == "gene"
                    and columns[1] == "protein_coding"
                    and columns[2] == accession
                ):
                    rows.append({
                        "unique_ids": columns[5],
                        "placements": columns[6],
                        "assembly_unit": columns[4]
                    })

            for row in rows:
                if row["assembly_unit"] in (
                    "all",
                    "Primary Assembly"
                ):
                    result["feature_count_data"] = row
                    break

            if result["feature_count_data"] is None and rows:
                result["feature_count_data"] = rows[0]

    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()

    base = NCBI_FTP + path + "/"

    for kind in FILE_TYPES + ("gbff", "feature_count"):
        result[kind] = [
            urljoin(base, name)
            for name in result[kind]
        ]

    return result


# NGDC-CNCB

def search_ngdc(accession=""):
    """Recherche NGDC à partir d'un identifiant d'assemblage GWH."""

    accession = accession.strip()

    if not accession:
        raise ValueError("L'accession GWH est obligatoire.")

    url = f"{NGDC_API}/assembly/{quote(accession, safe='')}"
    data = _request_json(url)

    files = {
        "fna": [data["ftpPathDna"]] if data.get("ftpPathDna") else [],
        "gff": [data["ftpPathGff"]] if data.get("ftpPathGff") else [],
        "faa": [data["ftpPathProtein"]] if data.get("ftpPathProtein") else []
    }

    assembly = _normalize_assembly(
        source="NGDC-CNCB",
        species=data.get("organism"),
        accession=data.get("assemblyAccession"),
        assembly_name=data.get("assemblyName"),
        assembly_level=data.get("assemblyLevel"),
        release_date=data.get("releaseTime"),
        bioproject=data.get("bioprojectAccession"),
        files=files,
        extra={
            "tax_id": data.get("taxId"),
            "biosample": data.get("biosampleAccession"),
            "genome_id": data.get("id"),
            "genome_representation": data.get("genomeRepresentation"),
            "ftpPathRna": data.get("ftpPathRna"),
            "ftpPathCds": data.get("ftpPathCds"),
            "ftpPathFeature": data.get("ftpPathFeature"),
            "submitter": data.get("submitterOrganization")
        }
    )

    return [assembly]


# Ensembl Metazoa

def search_ensembl(species=""):
    """Recherche une espèce dans Ensembl Metazoa."""

    species = species.strip()

    if not species:
        raise ValueError("Le nom de l'espèce est obligatoire.")

    data = _request_json(
        f"{ENSEMBL_API}/info/species",
        params={"division": "EnsemblMetazoa"}
    )

    wanted = species.lower().replace(" ", "_")
    matches = []

    for item in data.get("species", []):
        name = item.get("name", "").lower()
        aliases = [
            alias.lower()
            for alias in item.get("aliases", [])
        ]

        if (
            name == wanted
            or name.startswith(wanted + "_")
            or species.lower() in aliases
        ):
            matches.append(item)

    results = []

    for item in matches:
        name = item.get("name")

        assembly_data = _request_json(
            f"{ENSEMBL_API}/info/assembly/{quote(name, safe='')}"
        )

        files, file_errors = _ensembl_file_urls(name)

        assembly = _normalize_assembly(
            source="Ensembl Metazoa",
            species=item.get("display_name", name),
            accession=(
                assembly_data.get("assembly_accession") or name
            ),
            assembly_name=assembly_data.get("assembly_name"),
            assembly_level=assembly_data.get("assembly_level"),
            release_date=assembly_data.get("assembly_date"),
            files=files,
            extra={
                "ensembl_species": name,
                "taxonomy_id": item.get("taxon_id"),
                "division": item.get("division"),
                "assembly_raw": assembly_data,
                "file_errors": file_errors
            }
        )

        results.append(assembly)

    return results


def _ensembl_file_urls(species):
    """Récupère les liens FASTA et GFF3 disponibles sur Ensembl."""

    species = quote(species, safe="_")

    directories = {
        "fna": f"{ENSEMBL_FTP}/fasta/{species}/dna/",
        "faa": f"{ENSEMBL_FTP}/fasta/{species}/pep/",
        "gff": f"{ENSEMBL_FTP}/gff3/{species}/"
    }

    files = {kind: [] for kind in FILE_TYPES}
    errors = {}

    for kind, directory in directories.items():
        try:
            response = requests.get(
                directory,
                headers=HEADERS,
                timeout=30
            )
            response.raise_for_status()

            names = re.findall(
                r'href="([^"]+)"',
                response.text,
                flags=re.IGNORECASE
            )

            for name in names:
                lower = name.lower()

                if kind == "fna" and (
                    "dna.toplevel.fa.gz" in lower
                    or "dna_sm.toplevel.fa.gz" in lower
                ):
                    files[kind].append(urljoin(directory, name))

                elif kind == "faa" and lower.endswith(".pep.all.fa.gz"):
                    files[kind].append(urljoin(directory, name))

                elif kind == "gff" and lower.endswith(".gff3.gz"):
                    files[kind].append(urljoin(directory, name))

        except requests.RequestException as error:
            errors[kind] = str(error)
            print(f"Erreur lors de l'inspection {kind.upper()} : {error}")

    return files, errors


# Recherche multi-bases

def search_external_databases(species, ngdc_accession=None):
    """
    Recherche une espèce dans NCBI et Ensembl.
    NGDC est également interrogé si une accession GWH est fournie.
    Une erreur sur une source n'empêche pas les autres recherches.
    """

    assemblies = []
    errors = {}

    sources = [
        ("NCBI", search_ncbi, species),
        ("Ensembl Metazoa", search_ensembl, species)
    ]

    if ngdc_accession:
        sources.append(
            ("NGDC-CNCB", search_ngdc, ngdc_accession)
        )

    for source_name, function, argument in sources:
        try:
            assemblies.extend(function(argument))

        except requests.RequestException as error:
            errors[source_name] = (
                "Erreur de communication : " + str(error)
            )

        except (ValueError, KeyError, TypeError) as error:
            errors[source_name] = (
                "Erreur lors de la récupération des données : "
                + str(error)
            )

        except Exception as error:
            errors[source_name] = str(error)

    return {
        "assemblies": assemblies,
        "errors": errors
    }


# Inspection des fichiers

def inspect_assembly_files(assembly):
    """Récupère les fichiers disponibles pour un assemblage.
    
    THIS FUNCTION IS INCOMPLETE
    """

    if assembly.get("source") == "NCBI":
        result = _inspect_ncbi(assembly)

        assembly["files"] = {
            kind: result.get(kind, [])
            for kind in FILE_TYPES
        }

        assembly.setdefault("extra", {})

        assembly["extra"]["feature_count"] = (
            result.get("feature_count_data")
        )

        assembly["extra"]["other_files"] = {
            "gbff": result.get("gbff", []),
            "feature_count": result.get("feature_count", [])
        }

    return assembly


# Téléchargement avec reprise

def _download_file(url, local_path):
    """
    Télécharge un fichier avec reprise en cas d'interruption.
    Le fichier temporaire est conservé entre les tentatives.

    EXCLUSIVELY USED DURING DATABASE FILLING & MANAGEMENT

    Notes : 
        Temporary files are better handled by the `tempfile` module
        Functions should perform only one type of action, use private functions if needed
    """

    if not is_allowed_url(url):
        raise ValueError("URL de téléchargement non autorisée.")

    temporary = local_path + ".part"
    failures_without_progress = 0
    last_error = None

    while failures_without_progress < MAX_FAILURES_WITHOUT_PROGRESS:
        size_before = (
            os.path.getsize(temporary)
            if os.path.exists(temporary)
            else 0
        )

        headers = (
            {"Range": f"bytes={size_before}-"}
            if size_before else {}
        )

        print(
            f"Téléchargement {os.path.basename(local_path)}"
            + (
                f" (reprise à {size_before} octets)"
                if size_before else ""
            )
        )

        try:
            with requests.get(
                url,
                stream=True,
                timeout=TIMEOUT,
                headers=headers
            ) as response:

                if response.status_code == 416:
                    if os.path.exists(temporary):
                        os.remove(temporary)

                    raise IOError(
                        "Reprise refusée (416), nouveau téléchargement."
                    )

                response.raise_for_status()
                length = response.headers.get("Content-Length")

                if size_before and response.status_code == 206:
                    print("Serveur : reprise acceptée (206).")
                    mode = "ab"
                    expected_total = (
                        size_before + int(length)
                        if length is not None else None
                    )

                elif size_before and response.status_code == 200:
                    print(
                        "Serveur : reprise non acceptée (200), "
                        "le fichier repart de zéro."
                    )
                    mode = "wb"
                    size_before = 0
                    expected_total = (
                        int(length) if length is not None else None
                    )

                else:
                    mode = "wb" if not size_before else "ab"
                    expected_total = (
                        size_before + int(length)
                        if length is not None else None
                    )

                with open(temporary, mode) as output:
                    for block in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if block:
                            output.write(block)

            size_now = os.path.getsize(temporary)

            if size_now > size_before:
                failures_without_progress = 0
            else:
                failures_without_progress += 1

            if (
                expected_total is not None
                and size_now != expected_total
            ):
                raise IOError(
                    f"Taille incomplète ({size_now}/{expected_total})"
                )

            if not is_valid_gzip(temporary):
                os.remove(temporary)
                raise IOError(
                    "Le fichier téléchargé n'est pas un gzip valide."
                )

            os.replace(temporary, local_path)
            print("Téléchargement terminé et vérifié.")

            return True, None

        except Exception as error:
            last_error = str(error)
            print("Interruption :", error)

            size_after = (
                os.path.getsize(temporary)
                if os.path.exists(temporary)
                else 0
            )

            if size_after <= size_before:
                failures_without_progress += 1

            if failures_without_progress < MAX_FAILURES_WITHOUT_PROGRESS:
                print(
                    f"Nouvel essai dans {PAUSE_BETWEEN_ATTEMPTS} s..."
                )
                time.sleep(PAUSE_BETWEEN_ATTEMPTS)

    return False, (
        f"Abandon après {MAX_FAILURES_WITHOUT_PROGRESS} essais "
        f"consécutifs sans progression. Dernière erreur : {last_error}"
    )


def _download_files(assembly, types_to_download, base_folder="data"):
    """Télécharge les fichiers sélectionnés pour un assemblage.

    EXCLUSIVELY USED DURING DATABASE FILLING & MANAGEMENT
    """

    for kind in types_to_download:
        if kind not in FILE_TYPES:
            raise ValueError(f"Type de fichier invalide : {kind}")

    species_name = assembly.get("species") or "unknown_species"
    accession = assembly.get("accession") or "unknown_assembly"

    species_folder = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        species_name.replace(" ", "_")
    )

    assembly_folder = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        str(accession)
    )

    destination = os.path.join(
        base_folder,
        species_folder,
        assembly_folder
    )

    directory_created = False

    downloaded = {}
    errors = {}

    for kind in types_to_download:
        urls = assembly.get("files", {}).get(kind, [])

        if not urls:
            errors[f"{kind}_indisponible"] = "Fichier indisponible."
            print(f"{kind.upper()} indisponible pour cette source.")
            continue

        downloaded[kind] = []

        for url in urls:
            filename = os.path.basename(urlparse(url).path)

            if not filename:
                errors[f"{kind}_sans_nom"] = "Nom de fichier invalide."
                continue

            if not is_allowed_url(url):
                errors[filename] = (
                    "Domaine non autorisé, téléchargement refusé."
                )
                print("Refusé (domaine non autorisé) :", url)
                continue

            # Création du dossier seulement avant le premier téléchargement réel
            if not directory_created:
                os.makedirs(destination, exist_ok=True)
                directory_created = True

            local_path = os.path.join(destination, filename)

            if (
                os.path.exists(local_path)
                and is_valid_gzip(local_path)
            ):
                print("Déjà présent et valide :", filename)
                downloaded[kind].append(local_path)
                continue

            if os.path.exists(local_path):
                os.remove(local_path)

            success, message = download_file(url, local_path)

            if success:
                downloaded[kind].append(local_path)
            else:
                errors[filename] = message or "Échec du téléchargement."

        if not downloaded[kind]:
            downloaded.pop(kind)

    return {
        "files": downloaded,
        "errors": errors,
        "directory": destination if directory_created else None
    }

#Sauvegarde des métadonnées

def save_metadata(assembly, download_result):
    """Enregistre les métadonnées et les résultats du téléchargement."""

    if not download_result.get("directory"):
        return None

    metadata = {
        "assembly": assembly,
        "available_files": assembly.get("files", {}),
        "downloaded_files": download_result["files"],
        "download_errors": download_result["errors"]
    }

    path = os.path.join(download_result["directory"], "metadata.json")

    with open(path, "w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=4, ensure_ascii=False)

    return path
