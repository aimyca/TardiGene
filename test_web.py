"""
Testing web utilities for getting :
    search ncbi 
    inspect ncbi 
    search ngdc
    search ensembl
    ensembl_file_urls 
    inspect assembly files
    download files 
    save metadata 

"""


import os 

import web 

SPECIES_EXIST_NCBI = "Hypsibius dujardini"
SPECIES_NOT_EXIST_NCBI = "Bertolanius mahunkai"
ACC_EXIST = "SRX1253177"
ACC_NOT_EXIST = "..."
SPECIES_EXIST_ENSEMBL = "Hypsibius exemplaris"
SPECIES_NOT_EXIST_ENSEMBL = "Hypsibius dujardini"

def test_ncbi(spp):
    assemblies = web.search_ncbi(spp)
    if not assemblies:
        raise ValueError("Nothing apropriate")
    for assembly in assemblies:
        print(assembly.keys())

    return assemblies

def test_inspect_ncbi(assemblies):
    ftp_files = [web._inspect_ncbi(assembly) for assembly in assemblies]
    if not ftp_files:
        raise ValueError("Nothing apropriate")
    for file in ftp_files:
        print(file)

def test_ngdc(accession):
    return web.search_ngdc(accession)

def test_ensembl(spp):
    def parse(assemblies):
        """
        Returns all outputs in a format ready to be included in the database
        """
        db_fields = {
                record : None,
                name : None,
                description : None,
                sequence : None,
                accession : None,
                is_assembled : True
                }

        for assembly in assemblies:
            pass

    assemblies = web.search_ensembl(spp)
    return assemblies

def test_inspect_assembly_files(assembly):
    inspect_return = web.inspect_assembly_files(assembly)
    fns: dict[str, str] = inspect_return["files"]
    return fns

def test_download_file(url, local_path="."):
    return web._download_file(url, local_path)

def test_save_metadata(assembly, download_result):
    pass 

if __name__ == "__main__":
    # assembly = test_ncbi(SPECIES_EXIST_NCBI) # check 
    # no_assembly =  test_ncbi(SPECIES_NOT_EXIST_NCBI) # check 

    # test_inspect_ncbi(assembly) # check
    # test_inspect_ncbi(no_assembly) # check 

    # print(test_ngdc(ACC_EXIST)) # FAILED
    # print(test_ngdc(ACC_NOT_EXIST)) # FAILED

    # print(test_ensembl(SPECIES_NOT_EXIST_ENSEMBL)) # check 
    assembly = test_ensembl(SPECIES_EXIST_ENSEMBL) # check 
    assembly = assembly[0]
    urls_gff: list = test_inspect_assembly_files(assembly)["fna"] # check
    url = urls_gff[0]
 
    # print(test_download_file(url)) # FAILED, NEED TO REFACTOR FUNCTION

