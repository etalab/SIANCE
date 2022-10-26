#!/usr/bin/env python3


import logging
from siancedb.models import (
    SessionWrapper,
    SiancedbLetter,
)
from siancebackend.siv2metadata import safe_fetch_siv2


logger = logging.getLogger("fill_docid_siv2")


def insert_docid_for_all_documents():
    logger.info("Starting to fill docid siv2")
    with SessionWrapper() as db:
        for doc in db.query(SiancedbLetter).all():
            sidoc = safe_fetch_siv2(doc.name, doc.text)
            if sidoc:
                doc.metadata_si.doc_id = sidoc.get("r_object_id", None)
        db.commit()
    logger.info("Finished filling docid siv2")
