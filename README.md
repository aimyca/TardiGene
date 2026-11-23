# TardiGene

## Synopsis

Tardigene is a self-hosted web app allowing biologists to navigate through genomic data of various species of Tardigrada. It lets users perform multiple sequence alignment (MSA) using BLASTn, MAFFT & KMA (for gziped genomes) on assembled genomes. From that point, it is possible to access percentage identity, orthology profiles (using OrthoFinder) and phylogeny (tree ploting using Biobython's Phylo module). Raw reads alignment on a reference genome, or _de novo_ assembly may be implemented later.

## Installation 

You can install Tardigene by cloning the repo : 

```bash
git clone git@github.com:aimyca/TardiGene.git
```

It is advised to use Python version 3.8.13. You may install multiple python versions alongside your system install using `pyenv` (see the `pyenv` [repo](https://github.com/pyenv/pyenv) for installation details). Once installed, run the following command : 

```bash
pyenv install 3.8.13

# Then, in the Tardigene directory, set a local python version to 3.8.13
pyenv local 3.8.13 
# You can check which version you're using with :
pyenv version
```

You will need a virtual environment in order to run the application, you can create one using python :

```bash 
python -m venv .venv 
source .venv/bin/activate
```

And then install the python packages using the requirements.txt file :

```bash
pyenv pip install -r requirements.txt
```

## Dependancies

Tardigene requires 3 external tools to run alignments :

- MAFFT (>=7.307)

```bash
sudo apt install mafft 
```

- KMA (>=1.3) which you need to compile from source from : https://bitbucket.org/genomicepidemiology/kma/src/master/

(need to configure MAFFT executable location)

- Orthofinder (>=2.5.5), which needs to be installed from [this repo](https://github.com/davidemms/orthofinder#installing-orthofinder-on-linux).

