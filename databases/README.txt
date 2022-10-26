---
title: Siancedb package
author: Aliaume Lopez
date: 14/12/2020
---

**Siancedb** is a python package containing the
interfaces to interact with the SIANCE databases.
Functions ranges from initializing databases,
dropping tables, to interacting with the relationship
model and using the SQLAlchemy ORM to query the database.

## How to use

Just download the repository and then use the following command
inside the repository.

```bash
pip3 install -e .
```

This will create a package `siancedb` along with a
command line interface `siancedb.py`.

## How to contribute

The repository is very simple

Models
  : The main goal of the repository is to list models used
  to interact with the SIANCE database and keep those models
  up to date with said database. This is done in the `siancedb/models.py`
  file and **every** model should be found here.

Migrations
  : Scripts are made as files in the `siancedb` repository,
  and can be launched using the `bin/siancedb.py` command line interface.

Command Line Interface
  : The file `bin/siancedb.py` launches the command line interface
  and allows to use the migrations scripts and operations
  to interact directly with the database (creating tables, initializing
  some variables, updating users).


