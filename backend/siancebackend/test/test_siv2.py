#!/usr/bin/env python3

import pandas as pd
import numpy as np


import unittest

import datetime

from siancedb.config import get_config

from siancebackend.consolidate_metadata import (
    build_smart_response,
    smart_eta,
    smart_flatten,
    consolidate_smart_response,
)

from siancedb.models import (
    UNKNOWN,
    UNKNOWN_DATE,
)


CONFIG = get_config()
SIV2 = get_config()["siv2"]


class TestSmartEta(unittest.TestCase):
    def __init__(self):
        self.cases = [
            [],
            "single string value",
            1,
            [1, "middle string"],
            [1, ["nested string", 2]],
        ]

    def eta_idempotent(self):
        for case in self.cases:
            self.assertEquals(smart_eta(case), smart_eta(smart_eta(case)))

    def eta_returns_list(self):
        for case in self.cases:
            self.assertIsInstance(smart_eta(case), list)

    def eta_preserves_list(self):
        for case in self.cases:
            if isinstance(case, list):
                self.assertEqual(case, smart_eta(case))

    def eta_embeds_values(self):
        for case in self.cases:
            if not isinstance(case, list):
                self.assertIn(case, smart_eta(case))
                self.assertEqual(len(smart_eta(case)), 1)

    def eta_and_nullable_values(self):
        self.assertEqual(len(smart_eta("")), 0)
        self.assertEqual(len(smart_eta([])), 0)
        self.assertEqual(len(smart_eta(None)), 0)
        self.assertEqual(len(smart_eta(np.nan)), 0)

    def eta_with_iterables(self):
        res = smart_eta({7, 8})
        self.assertEquals(len(res), 2)
        self.assertIn(7, res)
        self.assertIn(8, res)

    def eta_caution_nantes(self):
        res = smart_eta("nan")
        self.assertSequenceEqual(res, ["nan"])


class TestSmartFlatten(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(len(smart_flatten([])), 0)

    def test_flattens(self):
        self.assertSequenceEqual(
            smart_flatten(["a", ["b", "c"], "d", ["e"], "f"]),
            ["a", "b", "c", "d", "e", "f"],
        )

    def test_nested_flattens(self):
        self.assertSequenceEqual(
            smart_flatten(["a", ["b"], [["c"]]]), ["a", "b", ["c"]]
        )


class TestSmartResponseAndEnrichment(unittest.TestCase):
    def setUp(self):
        self.siv2 = pd.read_pickle(SIV2["mock"])
        self.examples = {
            "INSSN-CAE-2017-0814": {
                "r_object_id": "0b00045181df3beb",
                "expected": {
                    "r_object_id": ["0b00045181df3beb"],
                    "exploitant": ["AREVA"],
                    "siret": ["30520716900106"],
                    "nom_ura": [],
                    "site": ["La Hague"],
                    "num_nom_inb": ["33"],
                    "inb_type_rep_ludd": ["LUDD"],
                    "natures": [
                        "OA RP",
                        "TMR",
                        "Cycle du combustible",
                        "Radiologie conventionnelle",
                        "INB-LUDD",
                        "OA - LA",
                        "Industrie-recherche",
                        "ESP",
                        "Conception; fabrication; maintenance d'emballages",
                        "Analyses de biologie médicale",
                        "Expéditeurs INB",
                        "Médical",
                    ],
                    "themes": ["LT9a-Inspection générale"],
                    "date_env_let_suite": [datetime.datetime(2017, 12, 20, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 12, 15, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 12, 15, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [False],
                    "inspect_inop": [False],
                    "agent_charge": ["PALIX Laurent"],
                    "agent_charge_resp": ["PALIX Laurent"],
                    "agents_copilotes": ["GAUTRON Corinne"],
                    "entite_resp": ["Caen"],
                    "entite_pilote": ["Caen"],
                    "": ["DRC"],
                },
            },
            "INSSN-CAE-2017-0403": {
                "r_object_id": "0b00045181b0897f",
                "expected": {
                    "r_object_id": ["0b00045181b0897f"],
                    "exploitant": ["AREVA"],
                    "siret": ["30520716900106"],
                    "nom_ura": [],
                    "site": ["La Hague"],
                    "num_nom_inb": [],
                    "inb_type_rep_ludd": ["LUDD"],
                    "natures": [
                        "OA RP",
                        "TMR",
                        "Cycle du combustible",
                        "Radiologie conventionnelle",
                        "INB-LUDD",
                        "OA - LA",
                        "Industrie-recherche",
                        "ESP",
                        "Conception; fabrication; maintenance d'emballages",
                        "Analyses de biologie médicale",
                        "Expéditeurs INB",
                        "Médical",
                    ],
                    "themes": ["TMR-Transports internes (arrêté INB)"],
                    "date_env_let_suite": [datetime.datetime(2017, 12, 14, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 12, 5, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 12, 5, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": ["PALIX Laurent"],
                    "agent_charge_resp": ["PALIX Laurent"],
                    "agents_copilotes": ["BERTELOOT Stephane"],
                    "entite_resp": ["Caen"],
                    "entite_pilote": ["DTS"],
                    "": ["Caen"],
                },
            },
            "INSSN-LYO-2017-0485": {
                "r_object_id": "0b00045181b08f96",
                "expected": {
                    "r_object_id": ["0b00045181b08f96"],
                    "exploitant": ["AREVA"],
                    "siret": ["52498027300014"],
                    "nom_ura": [],
                    "site": ["Tricastin"],
                    "num_nom_inb": ["168"],
                    "inb_type_rep_ludd": ["LUDD"],
                    "natures": ["Recherche", "TMR", "INB-LUDD", "OA - LA", "ESP"],
                    "themes": ["LT3d-Incendie"],
                    "date_env_let_suite": [datetime.datetime(2018, 1, 9, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 12, 14, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 12, 14, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [True],
                    "inspect_inop": [True],
                    "agent_charge": ["SAULZE Jean-louis"],
                    "agent_charge_resp": ["SAULZE Jean-louis"],
                    "agents_copilotes": ["ESCOFFIER Richard"],
                    "entite_resp": ["Lyon"],
                    "entite_pilote": ["Lyon"],
                },
            },
            "INSSN-LYO-2017-0716": {
                "r_object_id": "0b00045181b09ff7",
                "expected": {
                    "r_object_id": ["0b00045181b09ff7"],
                    "exploitant": ["EDF"],
                    "siret": ["55208131787403"],
                    "nom_ura": [],
                    "site": ["Tricastin"],
                    "num_nom_inb": [],
                    "inb_type_rep_ludd": ["REP"],
                    "natures": [
                        "TMR",
                        "OA - LA",
                        "Expéditeurs INB",
                        "Production d'électricité",
                        "ESP",
                        "Laboratoire environnement",
                        "Industrie-recherche",
                        "INB-REP",
                    ],
                    "themes": ["R.5.1 Génie civil"],
                    "date_env_let_suite": [datetime.datetime(2018, 1, 17, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 12, 19, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 12, 19, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": ["PERRIN Fanny"],
                    "agent_charge_resp": ["PERRIN Fanny"],
                    "agents_copilotes": ["VEILLOT Romain"],
                    "entite_resp": ["Lyon"],
                    "entite_pilote": ["Lyon"],
                },
            },
            "INSNP-PRS-2017-0288": {
                "r_object_id": "0b00045181b03d26",
                "expected": {
                    "r_object_id": ["0b00045181b03d26"],
                    "exploitant": [],
                    "siret": ["26750045200524"],
                    "nom_ura": [],
                    "site": [
                        "Hôpital Universitaire Pitié-Salpêtrière",
                        "Pitié Salpêtrière - Hôpital",
                    ],
                    "num_nom_inb": [],
                    "inb_type_rep_ludd": [],
                    "natures": [
                        "Médecine nucléaire thérapie",
                        "Radiothérapie externe",
                        "Médical",
                        "TMR",
                        "Radiologie conventionnelle",
                        "Médecine nucléaire",
                        "Analyses de biologie médicale",
                        "Radiologie dentaire",
                        "Scanographie",
                        "Radiologie interventionnelle",
                        "Curiethérapie",
                        "Expéditeurs NPx",
                    ],
                    "themes": ["Curiethérapie", "NPM-Curiethérapie"],
                    "date_env_let_suite": [datetime.datetime(2018, 1, 8, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 11, 10, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 11, 10, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": ["GUPTA Severine"],
                    "agent_charge_resp": ["GUPTA Severine"],
                    "agents_copilotes": ["GUPTA Severine"],
                    "entite_resp": ["Paris"],
                    "entite_pilote": ["DIS"],
                },
            },
            "INSNP-PRS-2016-0802": {
                "r_object_id": "0b0004518171ed14",
                "expected": {
                    "r_object_id": ["0b0004518171ed14"],
                    "exploitant": [],
                    "siret": ["26750045200029"],
                    "nom_ura": [],
                    "site": [
                        "GH Cochin",
                        "ASSISTANCE PUBLIQUE HÔPITAUX DE PARIS Hôpitaux Universitaires Paris Centre",
                    ],
                    "num_nom_inb": [],
                    "inb_type_rep_ludd": [],
                    "natures": [
                        "Médecine nucléaire thérapie",
                        "Radiothérapie externe",
                        "Médical",
                        "Radiologie conventionnelle",
                        "Médecine nucléaire",
                        "Analyses de biologie médicale",
                        "Radiologie interventionnelle",
                        "Curiethérapie",
                        "Fournisseurs de sources",
                    ],
                    "themes": ["NPM-Radiologie interventionnelle"],
                    "date_env_let_suite": [datetime.datetime(2016, 7, 27, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2016, 6, 16, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2016, 6, 16, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [0],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": [],
                    "agent_charge_resp": [],
                    "agents_copilotes": ["EUSTACHE Sandrine"],
                    "entite_resp": ["Paris"],
                    "entite_pilote": ["DIS"],
                },
            },
            "INSNP-MRS-2017-0804": {
                "r_object_id": "0b00045181b05d85",
                "expected": {
                    "r_object_id": ["0b00045181b05d85"],
                    "exploitant": [],
                    "siret": ["18008901300395"],
                    "nom_ura": [],
                    "site": ["CNRS", "IND-CNRS Montpellier"],
                    "num_nom_inb": [],
                    "inb_type_rep_ludd": [],
                    "natures": ["Recherche", "Industrie-recherche"],
                    "themes": ["NPI-Utilisation de sources non scellées (SNS)"],
                    "date_env_let_suite": [datetime.datetime(2017, 12, 19, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 11, 29, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 11, 29, 0, 0)],
                    "type_inspect": ["Courante"],
                    "priorite": [1],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": ["BERDOULA Francis"],
                    "agent_charge_resp": ["BERDOULA Francis"],
                    "agents_copilotes": ["LACQUEMANT Daniel"],
                    "entite_resp": ["Marseille"],
                    "entite_pilote": ["Marseille"],
                },
            },
            "INSSN-DCN-2017-0693": {
                "r_object_id": "0b00045181b09dfc",
                "expected": {
                    "r_object_id": ["0b00045181b09dfc"],
                    "exploitant": ["EDF"],
                    "siret": ["55208131766522"],
                    "nom_ura": ["UNIE"],
                    "site": ["Paris"],
                    "num_nom_inb": ["1354"],
                    "inb_type_rep_ludd": [],
                    "natures": [
                        "Recherche",
                        "Expéditeurs EDF",
                        "TMR",
                        "INB-LUDD",
                        "Maintenance d'ESP",
                        "Production d'électricité",
                        "Fabrication et maintenance d'équipements nucléaires",
                        "ESP",
                        "Industrie-recherche",
                        "INB-REP",
                    ],
                    "themes": [],
                    "date_env_let_suite": [datetime.datetime(2018, 6, 25, 0, 0)],
                    "date_fin_inspect": [datetime.datetime(2017, 12, 13, 0, 0)],
                    "date_deb_inspect": [datetime.datetime(2017, 12, 13, 0, 0)],
                    "type_inspect": [],
                    "priorite": [1],
                    "inspect_prog": [True],
                    "inspect_inop": [False],
                    "agent_charge": ["MORA Lucie"],
                    "agent_charge_resp": ["PIERRE Romain"],
                    "agents_copilotes": [],
                    "entite_resp": ["DCN"],
                    "entite_pilote": ["DCN"],
                },
            },
            "INSSN-LHKJHLIsejygkhikfdghH": {
                "r_object_id": "0b000451800049bb",
                "expected": {
                    "nom_ura": "Réacteur 2",
                    "etablissement": "",
                    "entite_pilote": "Lille",
                    "lotes": ["Lille"],
                    "date_deb_inspect": [datetime.datetime(2018, 6, 25, 0, 0)],
                    "num_nom_inb": [],
                    "site_concerne": "GRAVELINES",
                    "teledeclarant_email": "",
                    "object_name": "INSSN-LIL-2016-0236",
                    "inspect_inop": "Non",
                    "agent_charge_resp": "",
                    "date_prevision": [datetime.datetime(2018, 6, 25, 0, 0)],
                    "exploitant": "EDF",
                    "theme_complement": [],
                    "theme_principal": "Arret de tranches",
                    "date_cloture": "nulldate",
                    "date_env_let_suite": [datetime.datetime(2018, 7, 25, 0, 0)],
                    "inspect_priorite": "",
                    "domaine_activite": [
                        "INB-REP",
                        "TMR",
                        "OA - LA",
                        "Industrie-recherche",
                        "ESP",
                    ],
                    "date_env_let_annonce": [datetime.datetime(2018, 5, 25, 0, 0)],
                    "agent_copilotes": ["DUCROCQ Laurent"],
                    "niveau_priorite": "",
                    "inb_type": "REP",
                    "inb_type_rep_ludd": "REP",
                    "r_object_id": "0b000451800049bb",
                    "theme_secondaire": [],
                    "date_fin_inspect": [datetime.datetime(2018, 6, 25, 0, 0)],
                    "nbr_agent_copilote": [1],
                    "siret": "55208131721071",
                    "agent_copilote": ["DUCROCQ Laurent"],
                    "inspect_prog": "Non",
                    "type_inspect": "Courante",
                },
            },
        }

    def test_smart_constructions(self):
        for name, props in self.examples.items():
            with self.subTest(letter=name):
                rows = self.siv2[self.siv2["r_object_id"] == props["r_object_id"]]
                val = rows.to_dict("records")[0]
                resp = build_smart_response(val)
                resp_dict = {k: set(v) for k, v in resp.dict().items()}
                expc_dict = {k: set(v) for k, v in props["expected"].items()}
                for k in resp_dict.keys():
                    self.assertSetEqual(resp_dict[k], expc_dict[k])

    def test_encrichment_examples(self):
        for name, props in self.examples.items():
            print(f"-----------------{name}-----------------")
            rows = self.siv2[self.siv2["r_object_id"] == props["r_object_id"]]
            val = rows.to_dict("records")[0]
            resp = build_smart_response(val)
            consol = consolidate_smart_response(resp)
            print(resp.dict())
            print(consol.dict())
            print("----------------------------------------")

    def test_enrichment_random(self):
        tests = self.siv2.sample(n=5).to_dict("records")
        for i, val in enumerate(tests):
            name = val["object_name"]
            print(f"-----------------{i}: {name}-----------------")
            resp = build_smart_response(val)
            consol = consolidate_smart_response(resp)
            print(resp.dict())
            print(consol.dict())
            print("----------------------------------------")

    def test_enrichment_flamanville(self):
        object_ids = ["0b000451822b5711"]
        results = self.siv2[self.siv2["r_object_id"].isin(object_ids)].to_dict(
            "records"
        )
        for i, val in enumerate(results):
            name = val["object_name"]
            print(f"-----------------{i}: {name}-----------------")
            resp = build_smart_response(val)
            consol = consolidate_smart_response(resp)
            print(resp.dict())
            print(consol.dict())
            print("----------------------------------------")


if __name__ == "__main__":
    unittest.main()
