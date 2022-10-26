#!/usr/bin/env python3

import unittest
import pandas as pd
import numpy as np

from admin_functions import user_behaviours, search_behaviours

df = pd.DataFrame(
    [
        {
            "id_user": 10,
            "date": "02/10/2021",
            "action": "SEARCH",
            "topics": "salut",
            "domains": "coucou",
        },
        {
            "id_user": 12,
            "date": "02/10/2021",
            "action": "SEARCH",
            "topics": [],
            "domains": [],
        },
        {
            "id_user": 15,
            "date": "01/10/2021",
            "action": "OPEN_PDF",
        },
        {
            "id_user": 10,
            "date": "02/10/2019",
            "action": "OPEN_SIV2",
        },
        {
            "id_user": 15,
            "date": "01/9/2021",
            "action": "SEARCH",
            "topics": "salut",
            "domains": None,
        },
        {
            "id_user": 12,
            "date": "02/8/2021",
            "action": "OPEN_PDF",
        },
        {
            "id_user": 10,
            "date": "02/10/2021",
            "action": "OPEN_SIV2",
        },
    ]
)

df["date"] = pd.to_datetime(df["date"])
print(df)


class TestAdminMethods(unittest.TestCase):
    def _test_output_format(self, value):
        self.assertIsInstance(value, list)
        for e in value:
            self.assertIn("name", e)
            self.assertIn("value", e)
            self.assertIn(e["name"], ["25%", "50%", "75%"])
            self.assertIsInstance(e["value"], float)

    def _test_search_empty_dataframe_action(self, filter_action):
        output = search_behaviours(
            pd.DataFrame(columns=["id_user", "topics", "domains", "action", "date"]),
            filter_action,
        )
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)

    def test_search_empty_dataframe(self):
        for filter_action in ["topics", "domains"]:
            self._test_search_empty_dataframe_action(filter_action)

    def test_user_search_behaviour(self):
        output = user_behaviours(df, "SEARCH")
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)

    def test_user_open_pdf_behaviour(self):
        output = user_behaviours(df, "OPEN_PDF")
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)

    def test_user_open_siv2_behaviour(self):
        output = user_behaviours(df, "OPEN_SIV2")
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)

    def test_topics_behaviour(self):
        output = search_behaviours(df, "topics")
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)

    def test_domains_behaviour(self):
        output = search_behaviours(df, "domains")
        self._test_output_format(output)
        for e in output:
            self.assertEqual(e["value"], 0)


if __name__ == "__main__":
    unittest.main()
