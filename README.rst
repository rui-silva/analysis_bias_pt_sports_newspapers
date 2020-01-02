Analysis of biases in portuguese sports newspapers
========

Code and data used for analyzing the biases in portuguese sports
newspapers:
https://ruitsilva.com/pt/post/enviesamento_jornais_desportivos_portugueses/
(in Portuguese).


Dependencies
------------

`poetry` dependency management tool: https://python-poetry.org/

pyenv and virtualenv

Installation
------------

Clone repo

cd into project dir

Create a virtualenv for the project and activate it

    pyenv install 3.6.4

    pyenv virtualenv 3.6.4 analysis_bias_pt_sports_newspapers

    pyenv activate analysis_bias_pt_sports_newspapers

Install package with

    poetry install


Run
---

cd into the main folder

    cd analysis_bias_pt_sports_newspapers

Crawl the covers from banca sapo.

    python crawl_covers.py

You should see a new folder `./data/covers` with the newspaper
covers from 2019.

Now run

    python analysis.py

The calendar and month plots will be saved as figures in the current
directory. Other results may be shown on the terminal.
