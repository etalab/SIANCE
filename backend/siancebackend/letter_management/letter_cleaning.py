import re
import dateparser
import logging
from datetime import date, datetime
import json
from typing import Iterable, Union
from siancedb.models import UNKNOWN


import pandas as pd

logger = logging.getLogger("letters")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/letters.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

inspection_number_re = r"([ISNP]{3,6}-[A-Z]{3}-[0-9]{4}-[0-9]{4})"  #: Regexes to find information in the body of the letter


def normalize_text(text):
    """
    Replace most of special characters in a text, and turn it to lowercase

    Args:
        text (str): a text that may includes accents, diacritics or common (not all) french special characters

    Returns:
        str: a lowercase text where most of common french special characters have been replaced
    """
    text_lower = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("é", "e")
        .replace("É", "e")
        .replace("Ê", "e")
        .replace("È", "e")
        .replace("Ç", "c")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ï", "i")
        .replace("ç", "c")
        .replace("ô", "o")
        .lower()
    )
    return text_lower


def extract_codep(text: str):
    """
    Extracts the codep of a letter based on a regex
    It should follow a format like "CODEP-MRS-2020-054268" (for example)

    Args:
        text (str): the raw text of the letter

    Returns:
        str | None: the codep mentioned in the letter, if one has been found. Otherwise return None
    """
    codep_regular_expression = r"(CODEP-[A-Za-z]{3}-[0-9]{4}-[0-9]{6})"
    try:
        x = re.search(codep_regular_expression, text)
        return x.groups()[0]
    except Exception:
        logger.info("Impossible to find codep")
        return None


def extract_inspection(text: str):
    """
    Extract the inspection code name of a letter based on a regex
    It should follow a format like "INSSN-MRS-2020-0640" (for example)

    Args:
        text (str): the text of the letter

    Returns:
        str | None: the name mentioned in the letter, if one has been found. Otherwise return None
    """
    try:
        x = re.search(inspection_number_re, text)
        return x.groups()[0]
    except Exception:
        logger.info("Impossible to find inspection number")
        return None


def extract_sent_date(text: str):
    """
    Extract the date of the letter that is written in French at the beginning of the letter

    Args:
        text (str): the raw text of the letter

    Returns:
        str | None: the sent date mentioned in the letter, if one has been found.
        Otherwise return the date of 1st January 1970
    """
    # to be applied on letters with no sent date in the SI (basically letters before 2010)
    # the function must be called before any cleaning on the text
    text_beginning = text[
        :500
    ]  # the date is supposed to be at the very beginning of the letter
    pattern = [
        r"le[ ]*[0-9]{1,2}[ ]*janvier[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*f[e|é]vrier[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*mars[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*avril[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*mai[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*juin[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*juillet[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*ao[u|û]t[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*septembre[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*octobre[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*novembre[ ]*[0-9]{4}",
        r"le[ ]*[0-9]{1,2}[ ]*d[e|é]cembre[ ]*[0-9]{4}",
    ]
    pattern = "|".join(pattern)
    # assuming the sent date is the first date in the letter that follows the word "le"
    try:
        date_str = re.findall(pattern=pattern, string=text_beginning)[0]
        date_dt = dateparser.parse(date_str).date()
        if date_dt <= date.today():
            return date_dt
        else:
            return date(1970, 1, 1)
    except IndexError:  # no date-like found in letter
        return date(1970, 1, 1)


def clean_text_content(text: str):
    """
    Remove page numbers (when it is possible without ambiguities) and various
    special characters in the letter text.
    This function is called at the very end of the process of letter building

    WARNING: when modifying this function, beware it may impact the regex used for trigrams/sections/demands extractions

    Args:
        text (str): the raw text of the letter

    Returns:
        str: the text of the letter after cleaning
    """
    text = text.strip()
    text = re.sub(r"- [0-9]{1,2} -", "", text)
    text = re.sub(r"…/…", "", text)
    text = re.sub(r"[P|p]age[ ]*[0-9]{1,2}[ ]*[sur|/][ ]*[0-9]{1,2}", "", text)
    text = re.sub(r"[\t| ]+", " ", text)
    text = re.sub(r"\n ", "\n", text)
    text = re.sub(r"\n\n[0-9]+/[0-9]+", "", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    text = re.sub(r"\. \n", ".\n", text)
    text = re.sub(r"([a-z]) \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"([a-z]) \n+(à)", r"\1 \2", text)
    text = re.sub(r"([a-z]) \n+(é)", r"\1 \2", text)
    text = re.sub(r"([a-z]) \n+(«)", r"\1 \2", text)
    text = re.sub(r"([a-z]) \n+(\()", r"\1 \2", text)
    text = re.sub(r"(à) \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"(é) \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"(») \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"(,) \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"(\)) \n+([a-z])", r"\1 \2", text)
    text = re.sub(r"(°) \n+([0-9])", r"\1 \2", text)
    return text.strip()


def process_french_yes_no(answer: str):
    """
    In the database dw_letters
    the answers to most questions is textual
    (Oui/Non) in French and not in a boolean field.
    This function does the translation.

    It takes care of the lowercase and
    variations (yes,y,o,oui) for positive answers
    and (non, no, n) for negative answers.
    An answer that is not clearly positive
    is considered negative by default.
    """
    if answer is None:
        return False

    ans = answer.lower()
    if "oui" in ans or "yes" in ans:
        return True
    elif "non" in ans or "no" in ans or "n" in ans:
        return False
    elif "o" in ans or "y" in ans:
        return True
    else:
        return False


def process_french_date(date: Union[str, datetime], default: datetime=datetime(1970, 1, 1)) -> datetime:
    """
    In the database dw_lettres
    the dates are stored as string
    XX/XX/XX in French format.

    This functions converts this back
    to a nice date object in python.

    If default is provided, upon parsing error
    the default value is returned.
    Otherwise, there might be exceptions raised.
    """
    fmt_1 = "%Y-%m-%dT%H:%M:%SZ"
    fmt_2 = "%d/%m/%Y"

    if date is None:
        return default

    if isinstance(date, datetime):
        return date

    try:
        datetime_ = datetime.strptime(date, fmt_1)
        return datetime_
    except (ValueError, TypeError):
        try:
            datetime_ = datetime.strptime(date, fmt_2)
            return datetime_
        except (ValueError, TypeError):
            return default


def process_letter_content(letter: str):
    """
    In the database dw_lettres
    three # corespond to one \n
    so we have to convert this back
    """
    return letter.replace("###", "\n")


nullable_text_values = [
    None,
    "",
    " ",
    "Non précisé",
    "Sans objet",
    "?",
    "Non exploitable",
    "null",
    "nulldate",
    UNKNOWN,
    ["Sans objet"],
    [],
]


def is_nullable(s):
    return (not isinstance(s, Iterable) and pd.isna(s)) or s in nullable_text_values


def process_non_null(s: str):
    """
    Some strings in our scheme cannot be null,
    hence we have to build some default value
    """
    if is_nullable(s):
        return UNKNOWN
    else:
        return s


def process_string_array_safe(s):
    # if s is a two-leveled nested list, try to flatten it
    if isinstance(s, Iterable) and not isinstance(s, str):
        tmp = []
        for x in s:
            if isinstance(x, Iterable) and not isinstance(x, str):
                tmp.extend(x)
            else:
                tmp.append(x)
        s = list(set(tmp))
    elif isinstance(s, str):
        s = [s]
    else:
        raise TypeError("The input does not look like a list")
    s = list(filter(None, s))
    return s


def process_french_priority(s: str):
    """
    In the filed "priorité" there can be written
    Nationale (currently 3321)
    Locale (currently 1717)
    null
    empty string
    """
    if s == "Locale":
        return True
    else:
        return False
    
def process_inspection_type(s: str):
    if "courante" in s.lower():
        return "Courante"
    elif "japon" in s.lower():
        return "Japon"
    elif "renforcée" in s.lower():
        return "Renforcée"
    elif "revue" in s.lower():
        return "Revue"
    elif "récolement" in s.lower():
        return "Récolement police"
    elif "chantier" in s.lower() or "arrêt de tranche" in s.lower():
        return "Arrêt de réacteur"
    elif "événmt" in s.lower() or "réactive" in s.lower():
        return "Suite d'un événement"
    else:
        return s


def extract_name(filename: str):
    """
    In the field "nom_lettre"
    there is a suffix .txt everywhere
    we need to suppress this
    for beauty’s sake
    """
    try:
        if filename[-4:] == ".txt":
            return filename[:-4]
        else:
            return filename
    except IndexError:
        return filename


def process_non_null_double(d):
    """In the database some numbers are double
    precision floating point numbers
    that can be null... so we have to deal with this
    Moreover, they used the "," to separate which is not
    understood by python so we replace them with dots
    """
    try:
        return float(str(d).replace(",", "."))
    except (TypeError, ValueError):
        return 0


def process_all_dates(*dates):
    """
    Given a list of possible dates in decreasing
    order of importance, tries
    to build the array of the same size containing
    the parsed dates, using the most important
    possible parsing for every field.
    """

    pre_parse = [process_french_date(d) for d in dates]

    if any(pre_parse):  # Some date parsing was a success
        # Finds the first non null value in the list
        findfirst = next((el for el in pre_parse if el is not None))
        return [x or findfirst for x in pre_parse]
    else:
        return [datetime(1970, 1, 1).date() for _ in pre_parse]


def clean_entities(entities_str):
    # Rules to clean the entities from SIv2 metadata
    if entities_str == "":
        return UNKNOWN
    entities_str = (
        entities_str.replace("Conseiller", UNKNOWN)
        .replace("DG", UNKNOWN)
        .replace("SD2", UNKNOWN)
        .replace("Douai", "Lille")
        .replace("DIT", "DTS")
        .replace("DRD", "DRC")
    )
    return entities_str


def get_scopes(name, sector_list):
    """
    OUTDATED FUNCTION

    """
    is_rep, is_npx, is_ludd, is_certified_organism, is_transport = (
        False,
        False,
        False,
        False,
        False,
    )
    scopes = []
    name = name.lower()
    if "insnp" in name or "codep" in name:
        is_npx = True
    for sector in sector_list:
        sector = sector.lower()
        # variable `sector` is here a string
        # look if `ESP`, `REP`, etc, are substrings of sector
        if "esp" in sector or "rep" in sector:
            is_rep = True
        if "ludd" in sector:
            is_ludd = True
        if "tmr" in sector or "tsr" in sector or "transport" in sector:
            is_transport = True
        if "oa" in sector or "la" in sector:
            is_transport = True
    if is_rep:
        scopes.append("REP")
    if is_ludd:
        scopes.append("LUDD")
    if is_npx:
        scopes.append("NPX")
    if is_certified_organism:
        scopes.append("OA")
    if is_transport:
        scopes.append("TSR")
    return scopes
