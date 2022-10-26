#!/usr/bin/env python3
#
# Process letters functions
# The functions range from
# asking pdfs, recovering from the SIv2
# to extracting specific informations from
#

from dataclasses import dataclass
from typing import List
import os
import re
import feedparser
import wget
from siancedb.config import get_config
from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbLetter,
    UNKNOWN,
)

cfg = get_config()
LETTERS = cfg["letters"]


def letters_to_append(names: List[str]):
    with SessionWrapper() as db:
        docs = db.query(SiancedbLetter).filter(SiancedbLetter.name.notin_(names)).all()
        for d in docs:
            yield d.name


####
# This part of the file
# builds functions around the main datatype
# RSSLetter that is : a letter obtained through
# the RSS feed of the ASN webpage `asn.fr`
####


def build_letter_path(summary: str):
    """
    Returns the path to which the letter with a given
    summary is going to be saved
    """
    return f"{LETTERS['path']}{summary}.pdf"


def clean_letter_name(summary: str):
    """
    Given a summary (which is the inspection identifier)
    we build a clean letter name.
    """
    name_replacing = [
        [r"INNS", r"INSSN"],
        [r"INSPNP", r"INSNP"],
        [r" ", r""],
        [r"_", r"-"],
    ]
    s = summary
    for [search, replace] in name_replacing:
        s = re.sub(search, replace, s)
    return s


@dataclass
class RSSLetter:
    """
    Represents a letter in our system.
    """

    url: str
    " The url at which we downloaded the letter "

    path: str
    " The path of the file in our filesystem "

    rss_uid: str
    " The unique identifier from the RSS feed "

    summary: str
    """ The summary in the RSS feed. It happens to be 
    the inspection number so this is particularly useful """

    name: str
    """ The (cleaned) name of the letter
    """


def letter_from_rss(rss_item):
    """
    Transforms an RSS item into a Letter

    Scheme of RSS item (Sept 16th 2021):
        {
            'title': str,
            'title_detail': dict,
            'links': list,
            'link': str,
            'published': str,
            'published_pared': str,
            'authors': list,
            'author_detail': dict,
            'id': int,
            'guidislink': boolean
        }
    """
    link_pdf = rss_item.links[
        1
    ].href  # object at position [0] is about plain text, and object at position [1] about pdf
    summary = rss_item.links[1].href.split("/")[-1].split(".pdf")[0]
    path = build_letter_path(summary)
    rss_uid = rss_item.id
    name = clean_letter_name(summary)

    return RSSLetter(link_pdf, path, rss_uid, summary, name)


def download_letter(letter: RSSLetter):
    """
    Given the url of a pdf on the website
    `asn.fr`, downloads the file with the appropriate
    name in the appropriate folder

    ERASE PREVIOUS DOWNLOADS
    """
    if os.path.exists(letter.path):
        os.remove(letter.path)  # if exist, remove it directly
    wget.download(letter.url, letter.path, bar=None)
    return letter.path


def fetch_rss_letters():
    """
    Fetch the letters from the right RSS feed
    and return the generator of RSSLetters elements
    gathered
    """
    for feed in LETTERS["rss"]:
        for item in feedparser.parse(feed).entries:
            yield letter_from_rss(item)


####
# These functions now interact with the
# database to determine whether or not
# letters have already been treated before
# or not. This prevents adding duplicate
# entries
####


if __name__ == "__main__":
    print(list((letter.summary for letter in fetch_rss_letters())))
