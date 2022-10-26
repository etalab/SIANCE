# -*- coding: utf-8 -*-
"""
Version 27/11/2020

###########################################################################################
#                                                                                         #
# Fonction qui converti une feuille de calcul Excel sous forme d'un DataFrame spécifique  #
#                                                                                         #
###########################################################################################

### Structure des données en INPUT

1. Le HEADER de la feuille de calcul doit faire 2 lignes et structuré ainsi :

- Colonne "Objectif"co (header : cellules A1:A2 fusionnées)
- Colonne "Indicateur / Question" ou "Question / Indicateur" (header : cellules B1:B2 fusionnées)

Pour les sites mono-réacteurs:
- Colonne "Valeur / Réponse" (header : cellule C1) / "Site" (header : cellule C2)

Pour les sites avec 4 réacteurs par exemple:
- Colonne "Valeur / Réponse \nSite" (header : cellule C1:F1 fusionnées) / "Réacteur 1" (header : cellule C2) ... "Réacteur 4" (header : cellule F2)

D'autres colonnes peuvent être présentes ensuites, elles ne seront pas utilisées

2. Le contenu des colonnes doit suivre cette structure :

- Objectif : "Objectif n°X : Lorem Ipsum"
- Indicateur / Question : "Indicateur n°X : Lorem Ipsum"
- Valeur / Réponse : Libre

### Structure des données en OUTPUT

Le DataFrame est structurée ainsi :

- site (STRING) : Site géographique (ex: Tricastin)
- onglet (STING) : nom de la feuille de calcul (ex : "Systeme", "Incendie", etc.)
- no_objectif (INT) : numéro l'objectif (ex: 2)
- objectif (STRING) : texte de  l'objectif (ex : Lorem Ipsum)
- no_indicateur (INT) : numéro de l'indicateur (ex : 1)
- question (STRING) : texte de la question/indicateur (ex : Lorem Ipsum)
- no_reacteur (INT) : numéro du réacteur, s'il y a lieu. Cette colonne peut contenir des cellules vides. (ex : 1)
- valeur (STRING) : Réponse à la question

"""

import pandas as pd
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger("indicators")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler("logs/indicators.log")


def transformExcelSheetToDataFrame(df, sheet):
    # Delete rows with NaN
    df = df.dropna(axis=1, thresh=1)

    # Delete columns with NaN
    df = df.dropna(axis=0, thresh=1)

    # Delete the first row of the file
    df = df.drop([0], axis=0).reset_index(drop=True)

    # Keep only colulns of interest (`Objectif`, `Indicateur/Question`, `Valeur/Réponse`)
    df = df[df.columns.droplevel([1])[:3]]

    # Delete columns with "Unnamed" in their name (results from merged cells in Excel)
    for col in df.columns.droplevel([0]):
        if "Unnamed" in col:
            df = df.rename(columns={col: ""})

    # Remove space in column name and make it lowercase
    for col in df.columns.droplevel([1]):
        df = df.rename(columns={col: col.replace(" ", "").lower()})

    if "question/indicateur" in list(df.columns.droplevel([1])):
        df = df.rename(columns={"question/indicateur": "question"})
    if "indicateur/question" in list(df.columns.droplevel([1])):
        df = df.rename(columns={"indicateur/question": "question"})

    if "réponse/valeur" in list(df.columns.droplevel([1])):
        df = df.rename(columns={"réponse/valeur": "valeur/réponse"})

    # Add objective information on every row (merged cells in Excel)
    df.objectif = df.objectif.fillna(method="ffill")

    # Add column with the name of the sheet
    df.insert(0, "onglet", sheet)

    # Add column with the number of the objective
    df.insert(1, "no_objectif", df["objectif"].str.extract(r"([0-9]{1,2})"))

    # if there is `:` in the name of the objective, keep only the end of it
    df["objectif"] = df.objectif.str.split(":").str[-1].str.strip()

    # Add column with the number of the indicator
    df["question"] = df["question"].astype(str)
    df.insert(3, "no_indicateur", df["question"].str.extract(r"([0-9]{1,2})"))

    # if there is `:` in the name of the question, keep only the end of it
    df["question"] = df.question.str.split(":").str[-1].str.strip()

    # Create column `site` (and `no_reacteur` when the objective is not at reactor scale)
    if len(df.columns.droplevel([1])[5]) == 14:
        site = df.columns.droplevel([0])[5].strip().lower()
        df = df.droplevel([1], axis=1)
        df.insert(5, "no_reacteur", np.nan)
        # Replace NaN with None
        df = df.where(pd.notnull(df), None)
    else:
        site = df.columns.droplevel([1])[5].split("-")[1].strip().lower()
        df = df.rename(columns={df.columns.droplevel([1])[5]: "valeur/réponse"})

    df.insert(0, "site", site)

    # When the indicators are precised at the reactor scale
    if isinstance(df["valeur/réponse"], pd.DataFrame):
        pd.options.mode.chained_assignment = None
        df_react = df["valeur/réponse"]
        for i in range(len(df_react.columns[1::])):
            df_react.loc[:, df_react.columns[1::][i]] = df_react.loc[
                :, df_react.columns[1::][i]
            ].fillna(df_react.loc[:, df_react.columns[:-1][i]])
        df["valeur/réponse"] = df_react

        # Replace NaN with None
        df = df.where(pd.notnull(df), None)

        # Melting reactor numbers in lines
        df.columns = df.columns.map("|".join).str.strip("|")
        df = df.melt(
            id_vars=[
                "site",
                "onglet",
                "no_objectif",
                "objectif",
                "no_indicateur",
                "question",
            ],
            var_name="no_reacteur",
            value_name="valeur/réponse",
        )
        df["no_reacteur"] = df["no_reacteur"].str.extract(r"([0-9]{1,2})")
    else:
        pass

    # When "valeur/réponse" = "Sans objet", delete the row
    df = df[df["valeur/réponse"] != "Sans objet"]
    df = df.rename(columns={"valeur/réponse": "valeur"})

    return df, site


def parse_indicators_file(path):
    logger.info(f"Opening indicator file {path}")
    xls = pd.ExcelFile(path, engine="openpyxl")

    sheets = xls.sheet_names

    logger.info("Checking if sheets are valid")

    not_valid_sheets = []
    for sheet in sheets:
        try:
            pd.read_excel(xls, sheet, header=[0, 1])
            logger.info(f"The sheet {sheet} is valid")
        except:
            logger.info(
                f"Sheet {sheet} can not be parsed, header must not be more than 2 lines"
            )
            not_valid_sheets.append(sheet)

    sheets = list(set(sheets) - set(not_valid_sheets))

    logger.info("Cleaning and parsing indicators sheets")

    df_merge = pd.DataFrame()

    for sheet in sheets:
        # every sheet is cleaned and parsed
        df = pd.read_excel(xls, sheet, header=[0, 1])
        df, site = transformExcelSheetToDataFrame(df, sheet)
        df_merge = df_merge.append(df)
        logger.info(f"Parsing of sheet {sheet} | OK")

    df_merge = df_merge.reset_index(drop=True)

    path = ""
    filename = (
        "DataFrame_"
        + site
        + "_"
        + str(datetime.today().year)
        + str(datetime.today().month)
        + str(datetime.today().day)
        + ".pkl"
    )
    df_merge.to_pickle(path + filename)

    logger.info("# Save Dataframe as pickle | OK")
