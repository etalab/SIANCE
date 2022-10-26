import re
import pandas as pd
import logging
from typing import Optional, Tuple
from siancebackend.letter_management import prepare_sentencizer, normalize_text

from siancedb.models import (
    Session,
    SessionWrapper,
    SiancedbDemand,
    SiancedbLetter,
    SiancedbSection,
)
from siancebackend.pipe_logger import update_log_state

from siancedb.pandas_writer import chunker


logger = logging.getLogger("sections_demands")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("logs/sections_demands.log")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


def find_positions_blocks_containing_demands(
    positions_blocks, positions_demands, n_previous_blocks=0
):
    """
    For every demand start, find the start of the corresponding block (a block can be a paragraph, a sentence,
     or any other division).
     If there is several demands in the same block, don't repeat the block in the output (so the two demands in the
     same block are considered to be a single one)

     If parameter `n_previous_blocks` is not 0, every block containing a demand will be merged with (at most) the
     n  "not-special" blocks (=blocks that does not contain demand themselves) that precedes the block with demand,
     in order to bring more context information.

     Three conditions must be checked in order to merge a block containing a demand with some not-special blocks:
        (1) a block with a demand cannot be merged with not-special blocks before the very first block
        (2) a block with a demand cannot be merged with a block containing another demand
        (3) a block with a demand cannot be merged with a not special block already merged with a block with demand
     In particular, if there is only m (m < n) not-special blocks between a demand 1 and a demand 2, only these m
     blocks will be added in the context of demand 2.


    For the example
    > position_blocks = [1, 6, 14, 68, 90, 115, 136]
    > position_demands = [3, 5, 13, 67, 120]
    > n_previous_blocks = 0
    the output is
    > [(1, 6), (6, 14), (14, 68), (115,136)]
    reminder: the demands indicated at the positions 3 and 5 are in the same block, so they are considered to be merely
    one demand

    For the example (quite tricky)
    > position_blocks = [1, 6, 14, 68, 90, 115, 136]
    > position_demands = [3, 5, 13, 67, 120]
    > n_previous_blocks = 1
    the output is
    > [(1, 6), (6, 14), (14, 68), (90,136)]

    """
    assert (
        isinstance(n_previous_blocks, int) and n_previous_blocks >= 0
    ), "n_previous_block must be a non-negative integer"
    positions_blocks.sort(key=lambda x: x)
    positions_demands.sort(key=lambda x: x)

    iter_blocks = 0
    iter_demands = 0
    blocks_containing_demands = []
    merged_blocks = []

    # Remark: normally position_blocks[-1] should be the length of the text
    while iter_blocks < len(positions_blocks) - 1:
        if iter_demands == len(positions_demands):
            break

        block_beginning = positions_blocks[iter_blocks]

        # condition 1: a block can not be merged with blocks before the first block (!)
        shift_iter = max(0, iter_blocks - n_previous_blocks)
        merged_block_beginning = positions_blocks[shift_iter]

        block_ending = positions_blocks[iter_blocks + 1]
        # condition 2: if we have already met another block with demand, we can not merge with him
        # if we have met such a block, the length of `blocks_containing_demands` is > 0
        if len(blocks_containing_demands) > 0:
            # as the lists of demands were sorted, the previous block with demand if necessarily the last one added
            # in `blocks_containing_demands`
            (
                previous_block_with_demand_beginning,
                previous_block_with_demand_ending,
            ) = blocks_containing_demands[-1]
        else:
            # if we have never met a block with demand before, we can artificially set this variable to 0
            previous_block_with_demand_ending = 0

        # the position of the demand (assuming a demand is not initially covering several blocks at the same time)
        demand_beginning = positions_demands[iter_demands]

        # if there is a demand in the block, store the bounds of the block in the `blocks_containing_demands` list
        if block_beginning <= demand_beginning < block_ending:
            # check there is not already a demand in the same block. if this the case, the 2 demands must be "merged"
            # to "merge" them, it is necessary and sufficient just to store only one time the block containing them
            if (block_beginning, block_ending) not in blocks_containing_demands:
                blocks_containing_demands.append((block_beginning, block_ending))
                # condition (3) two "merged blocks" are not allowed to intersect
                # if we had never met a block with demand, previous_block_with_demand_ending=0, so the max() works
                merged_block_beginning = max(
                    merged_block_beginning, previous_block_with_demand_ending
                )
                merged_blocks.append((merged_block_beginning, block_ending))
            iter_demands += 1
        else:
            iter_blocks += 1

    return merged_blocks


def quick_find_sentence_pattern(pattern: str, text: str) -> Optional[Tuple[int, int]]:
    # not working fine so far
    searched = re.search(pattern, text)
    if searched is None:
        return None
    else:
        start, end = searched.start(), searched.end()
        before_start = min(
            0, start - 150
        )  # the separator are expected to be in short sentences
        after_end = end + 150
        sentencizer = prepare_sentencizer()
        doc = sentencizer(text[before_start:after_end])  # field name to be changed
        for sent in doc.sents:  # doc.sents is a generator
            if (
                before_start + sent.start_char <= start
                and end <= before_start + sent.end_char
            ):
                return before_start + sent.start_char, before_start + sent.end_char
        return None


def divide_one_letter(text: str):
    """
    Given one letter, cut it into sections `Synthesis` (synthese d'une inspection),
    `demands` (demandes d'actions correctives), `information` (demandes de compléments),
    `observations` (observations de l'inspecteur). The parts `introduction` (sentence before synthesis)
    and `conclusion` (sentences after the closing formula) are cut away and not returned by the function

    Warning for developers: in this function, separators should not contain accents
    or unusal punctuations, as the implemented matching ignores them

    Args:
        text (str): the body of the letter (lettre de suite)

    Raises:
        Exception: "The letter is not following any known format".
        This exception is deprecated in this code version

    Returns:
        str, str, str, str, int (or None), int (or None), int (or None), int (or None), int (or None), int (or None),
         int (or None), int (or None): the subtexts corresponding to `synthesis`, `demands`, `information`,
         `observations` sections, and the starting and ending characters of each section (equals to None when section
         is missing)
    """
    try:
        text_lower = normalize_text(text)
        sep_synthesis = [
            r"[\r\n|\n|\\n]+[(i\. )|(1\. )|(a\. )|(1 \- )]*s[a-z]{1,2}these de (l'insp[a-z]{3}ion|la visite)[\.| |:]*",
            r"1[\-|\.| ]*synthese de l'inspection[\.| |:]*",
            r"[\r\n|\n|\\n]+synthese des inspections[\.| |:]*",
            r"[\r\n|\n|\\n]+synthese du contrôle[\.| |:]*",
            r"[\r\n|\n|\\n]+[ ]*synthese[\.| |:]*[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+i. appreciation globale",
        ]
        sep_synthesis = "|".join(sep_synthesis)

        sep_demands = [
            r"[1|2|a|b|ii][ |\.|\-|\|\/)]+demande[s]* d'action[s]* corrective[s]*[\.| |:]*",
            r"[1|2|a|b|ii][ |\.|\-|\|\/)]+demande[s]* d'a[a-z]{1,2}ion[s]* co[a-z]{5,6}ve[s]*[\.| |:]*",
            r"[\r\n|\n|\\n]+demande[s]* d'action[s]* corrective[s]*[\.| |:]*",
            r"demande[s]* d'action[s]* corrective[s]*[\.| |:]*[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+a[\.| \-]{0,1} demandes[ :]{0,1}[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+[1|2|a|b|ii][ |\.|\-|\|\/)]+demandes d'action[s]*[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+[a\. ]*description des ecarts[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+a. actions correctives[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+a[0-9]{0,1}. actions correctives[\r\n|\n|\\n]+",
            r"[\r\n|\n|\\n]+a. (demande[s]* de )*mise[s]* en conformite a la reglementation",
            r"ii[ |\.|\-|\|\/)]+demande[s]* portant sur des ecarts[\.| |:]*",
            r"ii[ |\.|\-|\|\/)]+demande[s]* d'engagements[\.| |:]*",
            r"[1|2|a|b|ii][ |\.|\-|\|\/)]+principales constatations et demandes",
        ]
        sep_demands = "|".join(sep_demands)

        sep_information = [
            r"[a|b|c|ii|iii|2|3][ |\.|\-|\|\/)]+demande[s]*( d'information[s]*)* complementaire[s]*[\.| |:]*",
            r"[a|b|c|ii|iii|2|3][ |\.|\-|\|\/)]+demande[s]* d'information[s]*[\.| |:]*",
            r"[a|b|c|ii|iii|2|3][ |\.|\-|\|\/)]+demande[s]* de complement[s]*( d'information){0,1}[\.| |:]*",
            r"[\r\n|\n|\\n]+(demande[s]* de ){0,1}complement[s]* d'information[\.| |:]*",
            r"[\r\n|\n|\\n]+b[\.] d'informations complementaires[\.| |:]*",
            r"[a|b|c|ii|iii|2|3][ |\.|\-|\|\/)]+complement[s]* d'information[\.| |:]*",
            r"[ a-z]*complement[s]* d'information[\.| |:]*[\r\n|\n|\\n]+",
            r"[a|b|c|ii|iii|2|3][ |\.|\-|\|\/)]+demande[s]* de justification et de positionnement[\.| |:]*",
            r"[\r\n|\n|\\n]+[ ]*demande[s] d'information[s]",
        ]
        sep_information = "|".join(sep_information)

        sep_observations = [
            r"[\r\n|\n|\\n]+[b|c|2|iv][ |\.|\-|\|\/)]+observation[s]*[\.| |:]*",
            r"[2|iv][ |\.|\-|\|\/)]+observation[s]*[\.| |:]*",
            r"[\r\n|\n|\\n]+[ ]*observation[s]*[\.| |:]*[\r\n|\n|\\n]+",
        ]
        sep_observations = "|".join(sep_observations)

        sep_conclusion = [
            r"je vous prie de trouver, ci-joint, les axes d'amelioration identifies au cours de l'inspection",
            r"(vous voudrez bien|je vous saurai gre de bien vouloir) me f[a-z]{2}re part",
        ]
        sep_conclusion = "|".join(sep_conclusion)

        """
        The letter is parsed from the end to the beginning, because a section goes from the title
        of a section to the beginning of the next present section
        """

        # `start_next_section` is a tmp variable, giving the starting point of the next present section
        start_next_section = len(text)

        search_conclusion = re.search(sep_conclusion, text_lower)
        if search_conclusion is not None:
            # store where the closing formula starts
            start_title_conclusion = search_conclusion.start()
            # the conclusion part comes after (the beginning of) the closing formula
            start_conclusion = start_title_conclusion
            text_conclusion = text[start_conclusion:]
            # stores in `start_next_section` the beginning of conclusion part
            start_next_section = start_title_conclusion
        else:
            text_conclusion = ""
            start_conclusion = None

        search_observations = re.search(sep_observations, text_lower)
        if search_observations is not None:
            # store where the SECTION TITLE of observations starts and ends
            start_title_observations = search_observations.start()
            end_title_observations = search_observations.end()
            start_observations = (
                end_title_observations  # skip the title of "Observations" section
            )
            end_observations = start_next_section
            text_observations = text[start_observations:end_observations]
            # stores in `start_next_section` the beginning of observations part
            start_next_section = start_title_observations
        else:
            text_observations = ""
            start_observations, end_observations = None, None

        search_information = re.search(sep_information, text_lower)
        if search_information is not None:
            # store where the SECTION TITLE of demands of informations starts and ends
            start_title_information = search_information.start()
            end_title_information = search_information.end()
            start_information = end_title_information  # skip the title of "Demandes d'Informations" section
            end_information = start_next_section
            text_information = text[start_information:end_information]
            # stores in `start_next_section` the beginning of demands of information part
            start_next_section = start_title_information
        else:
            text_information = ""
            start_information, end_information = None, None

        search_demands = re.search(sep_demands, text_lower)
        if search_demands is not None:
            # store where the SECTION TITLE of demands of actions starts and ends
            start_title_demands = search_demands.start()
            end_title_demands = search_demands.end()
            start_demands = (
                end_title_demands  # skip the title of "Demandes d'Actions" section
            )
            end_demands = start_next_section
            text_demands = text[start_demands:end_demands]
            # stores in `start_next_section` the beginning of demands of information part
            start_next_section = start_title_demands
        else:
            text_demands = ""
            start_demands, end_demands = None, None

        search_synthesis = re.search(sep_synthesis, text_lower)
        if search_synthesis is not None:
            # store where the SECTION TITLE of synthesis starts and ends
            start_title_synthesis = search_synthesis.start()
            end_title_synthesis = search_synthesis.end()
            start_synthesis = (
                end_title_synthesis  # skip the title of "Demandes d'Actions" section
            )
            end_synthesis = start_next_section
            text_synthesis = text[start_synthesis:end_synthesis]
            # stores in `start_next_section` the beginning of demands of information part
            start_next_section = start_title_synthesis
        else:
            text_synthesis = ""
            start_synthesis, end_synthesis = None, None

        text_introduction = text[:start_next_section]

        return (
            text_synthesis,
            text_demands,
            text_information,
            text_observations,
            start_synthesis,
            end_synthesis,
            start_demands,
            end_demands,
            start_information,
            end_information,
            start_observations,
            end_observations,
        )

    except Exception as e:
        print(text)
        print(e)
        raise Exception("The letter is not following any known format")


def divide_letters(letters_df: pd.DataFrame, strip_texts=True):
    """
    Given a dataframe of letters, divide them in sections `synthesis`, `demands`, `information`,
    `observations`, and return a dataframe with these (four) columns and with a (fifth) column `id_letter`

    Args:
        letters_df (pandas.DataFrame): tables of letters, whose bodies are in the column `text`
            and with an index `id_letter`
        strip_texts (bool): if True (default), the output texts are stripped (starting and ending blanks are cut)
            Nevertheless, if these blanks are removed, the returned starting characters may be wrong
            TODO: must be changed, in order to remove this boolean and fix the starting characters

    Returns:
        pandas.DataFrame: dataframe with columns `id_letter`, `synthesis`, `demands`, `information`,
        `observations`
    """
    data = []
    for id_letter, row in letters_df.set_index("id_letter").iterrows():
        text = str(row["text"])
        (
            text_synthesis,
            text_demands,
            text_information,
            text_observations,
            start_synthesis,
            end_synthesis,
            start_demands,
            end_demands,
            start_information,
            end_information,
            start_observations,
            end_observations,
        ) = divide_one_letter(text)
        data.append(
            [
                id_letter,
                text_synthesis,
                text_demands,
                text_information,
                text_observations,
                start_synthesis,
                end_synthesis,
                start_demands,
                end_demands,
                start_information,
                end_information,
                start_observations,
                end_observations,
            ]
        )
    return pd.DataFrame(
        data=data,
        columns=[
            "synthesis",
            "demands",
            "information",
            "observations",
            "conclusion",
            "start_synthesis",
            "end_synthesis",
            "start_demands",
            "end_demands",
            "start_information",
            "end_information",
            "start_observations",
            "end_observations",
        ],
    )


def extract_demands_one_letter(text: str, n_previous_blocks=1):
    """
    Slow function for tests only. In production the useful function is `build_sections_demands_one_letter`

    Given a dataframe of letters, extract the demands from the section `demands`(demandes d'actions correctives) and
    from the section `information` (demandes d'information complémentaire)
    `observations`, and return a dataframe with the columns `start`, `end`, `sentence`, `priority`(1 for demandes
    d'actions correctives, and 2 for demandes d'information complémentaire) with an `id_letter`

    Args:
        text (str): the content of the letter read from letters table (it comes after the cleaning)
        n_previous_blocks (int):
    Returns:
        pandas.DataFrame: dataframe with at least columns `start`, `end`, `priority`
    """

    (
        text_synthesis,
        text_demands,
        text_information,
        text_observations,
        start_synthesis,
        end_synthesis,
        start_demands,
        end_demands,
        start_information,
        end_information,
        start_observations,
        end_observations,
    ) = divide_one_letter(text)

    (
        absolute_positions_demands_a,
        absolute_positions_information_b,
    ) = get_positions_demands_a_b(
        start_demands, start_information, text_demands, text_information
    )

    """
    sentencizer = prepare_sentencizer()
    (
        absolute_positions_sentences_a,
        absolute_positions_sentences_b,
    ) = get_positions_sentences_a_b(
        sentencizer, start_demands, start_information, text_demands, text_information
    )
    bounds_blocks_demands_a = find_positions_blocks_containing_demands(
        absolute_positions_sentences_a, absolute_positions_demands_a
    )

    bounds_blocks_demands_b = find_positions_blocks_containing_demands(
        absolute_positions_sentences_b, absolute_positions_information_b
    )

    """

    (
        absolute_positions_paragraphs_a,
        absolute_positions_paragraphs_b,
    ) = get_positions_paragraphs_a_b(
        start_demands, start_information, text_demands, text_information
    )

    bounds_blocks_demands_a = find_positions_blocks_containing_demands(
        absolute_positions_paragraphs_a,
        absolute_positions_demands_a,
        n_previous_blocks=n_previous_blocks,
    )

    bounds_blocks_demands_b = find_positions_blocks_containing_demands(
        absolute_positions_paragraphs_b,
        absolute_positions_information_b,
        n_previous_blocks=n_previous_blocks,
    )

    demands_table = []
    # demands_table is a list of list [sentence demand start, sentence demand end, type(can be one or 2), text]
    for bounds in bounds_blocks_demands_a:
        demands_table.append(
            [
                bounds[0],
                bounds[1],
                1,
                text_demands[bounds[0] - start_demands : bounds[1] - start_demands],
            ]
        )
    for bounds in bounds_blocks_demands_b:
        demands_table.append(
            [
                bounds[0],
                bounds[1],
                2,
                text_information[
                    bounds[0] - start_information : bounds[1] - start_information
                ],
            ]
        )
    return pd.DataFrame(
        data=demands_table, columns=["start", "end", "priority", "sentence"]
    )


def get_positions_sentences_a_b(
    sentencizer, start_demands, start_information, text_demands, text_information
):
    """
    Given the text of sections A and B, and their starting characters, compute the positions
    of every sentences in these sections (these sentences may be actual demands or not)
    The returned positions are calculated from the beginning of the letter

    Args:
        sentencizer ([type]): a NLP object that cut text in sentences
        start_demands (int | None): the position of the start of the section A (None if the section doesn't exist)
        start_information (int | None): the position of the start of the section B (None if the section doesn't exist)
        text_demands (str): the text of the section A of the letter
        text_information (str): the text of the section B of the letter

    Returns:
        list[int], list[int]:
            the lists of positions of the starting character of sentences in sections A and B
    """
    absolute_positions_sentences_a = [
        start_demands + sent.start_char for sent in sentencizer(text_demands).sents
    ]  # possibly empty if the section is empty
    # add the length of the section, to have the bounds of every sentence including the last one
    absolute_positions_sentences_a.append(start_demands + len(text_demands))
    absolute_positions_sentences_b = [
        start_information + sent.start_char
        for sent in sentencizer(text_information).sents
    ]
    # add the length of the section, to have the bounds of every sentence including the last one
    absolute_positions_sentences_b.append(start_information + len(text_information))
    return absolute_positions_sentences_a, absolute_positions_sentences_b


def get_positions_paragraphs_a_b(
    start_demands, start_information, text_demands, text_information
):
    """
    Given the text of sections A and B, and their starting characters, compute the positions
    of every paragraphs in these sections (the function cuts too short paragraphs)
    The returned positions are calculated from the beginning of the letter

    Args:
        start_demands (int | None): the position of the start of the section A (None if the section doesn't exist)
        start_information (int | None): the position of the start of the section B (None if the section doesn't exist)
        text_demands (str): the text of the section A of the letter
        text_information (str): the text of the section B of the letter

    Returns:
        list[int], list[int]:
            the lists of positions of the starting character of paragraphs (excluding very short paragraphs)
    """
    # if there are too few characters between two "\n", it means some paragraphs are nonsense. Ignore them
    paragraph_min_length = 8
    # p = re.compile(r"\n\n|\\n\\n|\n|\\n")
    p = re.compile(r"\n\n|\\n\\n")

    # the first paragraph begins with the beginning of the section (if the section is not empty)
    if start_demands is not None:
        absolute_positions_paragraphs_a = [start_demands]
        for newline_sign in p.finditer(text_demands):
            new_paragraph = start_demands + newline_sign.end()
            absolute_positions_paragraphs_a.append(new_paragraph)

        # add the position of the start of the last paragraph (potentially empty) of the section
        absolute_positions_paragraphs_a.append(start_demands + len(text_demands))

        # check the length of the paragraph to filter out very short paragraphs
        # if there are too few characters between two "\n", it means some paragraphs are nonsense. Ignore them
        # example: if min_length = 5 and if the positions are [0, 7, 9, 20], it becomes [0, 7, 20]
        absolute_positions_paragraphs_a = [
            absolute_positions_paragraphs_a[k]
            for k in range(len(absolute_positions_paragraphs_a) - 1)
            if (
                absolute_positions_paragraphs_a[k + 1]
                - absolute_positions_paragraphs_a[k]
            )
            >= paragraph_min_length
        ]
        absolute_positions_paragraphs_a.append(start_demands + len(text_demands))
    else:
        absolute_positions_paragraphs_a = []

    if start_information is not None:
        absolute_positions_paragraphs_b = [start_information]
        for newline_sign in p.finditer(text_information):
            new_paragraph = start_information + newline_sign.end()
            absolute_positions_paragraphs_b.append(new_paragraph)
        # add the position of the start of the last paragraph (potentially empty) of the section
        absolute_positions_paragraphs_b.append(
            start_information + len(text_information)
        )

        # check the length of the paragraph to filter out very short paragraphs
        # if there are too few characters between two "\n", it means some paragraphs are nonsense. Ignore them
        absolute_positions_paragraphs_b = [
            absolute_positions_paragraphs_b[k]
            for k in range(0, len(absolute_positions_paragraphs_b) - 1)
            if (
                absolute_positions_paragraphs_b[k + 1]
                - absolute_positions_paragraphs_b[k]
            )
            >= paragraph_min_length
        ]
        absolute_positions_paragraphs_b.append(
            start_information + len(text_information)
        )
    else:
        absolute_positions_paragraphs_b = []

    return absolute_positions_paragraphs_a, absolute_positions_paragraphs_b


def get_positions_demands_a_b(
    start_demands, start_information, text_demands, text_information
):
    """
    Given the text of sections A and B, and their starting characters, compute the starting positions
    of every demand pattern (see regex) in these sections.
    The returned positions are calculated from the beginning of the letter

    Args:
        start_demands (int | None): the position of the start of the section A (None if the section doesn't exist)
        start_information (int | None): the position of the start of the section B (None if the section doesn't exist)
        text_demands (str): the text of the section A of the letter
        text_information (str): the text of the section B of the letter

    Returns:
        list[int], list[int]:
            the lists of positions of the starting character of demand patterns in sections A and B
    """
    pattern_demand = [
        r"je vous demande",
        r"asn vous demande",
        r"asn vous invite",
        "je vous invite",
    ]
    pattern_demand = re.compile("|".join(pattern_demand), re.IGNORECASE)
    absolute_positions_demands_a = [
        m.start() + start_demands for m in pattern_demand.finditer(text_demands)
    ]
    absolute_positions_information_b = [
        m.start() + start_information for m in pattern_demand.finditer(text_information)
    ]
    return absolute_positions_demands_a, absolute_positions_information_b


def build_sections_demands_one_letter(
    letter: SiancedbLetter,
    n_previous_blocks=1,
):
    """
    Given a letter, extract all its sections and demands, and return list of SiancedbSection and SiancedbDemand objects

    Args:
        letter (SiancedbLetter): an instance of letter model
        n_previous_blocks (int):
        sentencizer ([type]): a NLP object that cut text in sentences

    Returns:
        list[SiancedbSection], list[SiancedbDemand]:the list of sections and demands mentioned in the letter content
    """
    (
        text_synthesis,
        text_demands,
        text_information,
        text_observations,
        start_synthesis,
        end_synthesis,
        start_demands,
        end_demands,
        start_information,
        end_information,
        start_observations,
        end_observations,
    ) = divide_one_letter(str(letter.text))

    db_sections = []
    if len(text_synthesis) > 0:
        db_sections.append(
            SiancedbSection(
                id_letter=letter.id_letter,
                priority=0,
                start=start_synthesis,
                end=end_synthesis,
            )
        )
    if len(text_demands) > 0:
        db_sections.append(
            SiancedbSection(
                id_letter=letter.id_letter,
                priority=1,
                start=start_demands,
                end=end_demands,
            )
        )
    if len(text_information) > 0:
        db_sections.append(
            SiancedbSection(
                id_letter=letter.id_letter,
                priority=2,
                start=start_information,
                end=end_information,
            )
        )
    if len(text_observations) > 0:
        db_sections.append(
            SiancedbSection(
                id_letter=letter.id_letter,
                priority=3,
                start=start_observations,
                end=end_observations,
            )
        )

    (
        absolute_positions_demands_a,
        absolute_positions_information_b,
    ) = get_positions_demands_a_b(
        start_demands, start_information, text_demands, text_information
    )
    """
    (
        absolute_positions_sentences_a,
        absolute_positions_sentences_b,
    ) = get_positions_sentences_a_b(
        sentencizer, start_demands, start_information, text_demands, text_information
    )
    bounds_blocks_demands_a = find_positions_blocks_containing_demands(
        absolute_positions_sentences_a, absolute_positions_demands_a
    )
    bounds_blocks_demands_b = find_positions_blocks_containing_demands(
        absolute_positions_sentences_b, absolute_positions_information_b
    )

    """

    (
        absolute_positions_paragraphs_a,
        absolute_positions_paragraphs_b,
    ) = get_positions_paragraphs_a_b(
        start_demands, start_information, text_demands, text_information
    )

    bounds_blocks_demands_a = find_positions_blocks_containing_demands(
        absolute_positions_paragraphs_a,
        absolute_positions_demands_a,
        n_previous_blocks=n_previous_blocks,
    )

    bounds_blocks_demands_b = find_positions_blocks_containing_demands(
        absolute_positions_paragraphs_b,
        absolute_positions_information_b,
        n_previous_blocks=n_previous_blocks,
    )

    db_demands = []
    for bounds_a in bounds_blocks_demands_a:
        db_demands.append(
            SiancedbDemand(
                start=bounds_a[0],
                end=bounds_a[1],
                priority=1,
                id_letter=letter.id_letter,
            )
        )
    for bounds_b in bounds_blocks_demands_b:
        db_demands.append(
            SiancedbDemand(
                start=bounds_b[0],
                end=bounds_b[1],
                priority=2,
                id_letter=letter.id_letter,
            )
        )

    return db_sections, db_demands


def build_sections_demands(db: Session, n_previous_blocks=1, pipe_logger=None):
    """
    For all letters for which no sections and demands have been extracted, extract them and save them in the database
    Nota Bene: A letter necessarily contains a section or a demand

    Args:
        db (Session): a Session to connect to the database
        n_previous_blocks (int):
        pipe_logger (SiancedbPipeline): an object logging in PostgreSQL the advancement of data ingestion steps
    """
    sentencizer = prepare_sentencizer()
    with SessionWrapper() as database:
        dquery = (
            database.query(SiancedbLetter)
            .filter(~SiancedbLetter.sections.any())
            .filter(~SiancedbLetter.demands.any())
        )
        letters = dquery.all()
        n_documents = dquery.count()

    # just check this len() function does not empty letter pseudo-generator
    letters_count = 0

    for chunk_letters in chunker(100, letters):

        logger.info("Starting new chunk of letters for extracting sections and demands")
        chunk_sections, chunk_demands = [], []
        for letter in chunk_letters:
            (
                one_letter_db_sections,
                one_letter_db_demands,
            ) = build_sections_demands_one_letter(
                letter,
                n_previous_blocks=n_previous_blocks,
            )
            chunk_sections.extend(one_letter_db_sections)
            chunk_demands.extend(one_letter_db_demands)
        db.add_all(chunk_sections)
        db.add_all(chunk_demands)

        letters_count += 100
        update_log_state(
            pipe=pipe_logger,
            progress=letters_count / n_documents,
            step="sections_demands",
        )
        logger.info("Sections and demands chunk built")
        db.commit()
        logger.info("Sections and demands chunk committed")


def extract_demands(letters_df: pd.DataFrame, n_previous_blocks=1):
    """
    Slow function for tests only. In production the useful function is `build_sections_demands`

    Given a dataframe of letters, extract the demands from the section `demands`(demandes d'actions correctives) and
    from the section `information` (demandes d'information complémentaire)
    `observations`, and return a dataframe with the columns `start`, `end`, `sentence`, `priority`(1 for demandes
    d'actions correctives, and 2 for demandes d'information complémentaire) with an `id_letter`

    Args:
        letters_df (pandas.DataFrame): tables of letters, with columns `text` and `id_letter`
        n_previous_blocks (int):
    Returns:
        pandas.DataFrame: dataframe with at least columns `start`, `end`, `priority` and the index `id_letter`
    """
    dataframes_list = []
    k = 1
    n = len(letters_df)
    for _, row in letters_df.iterrows():
        id_letter = row["id_letter"]
        logger.debug(f"Extract demands from letter {id_letter}. Letter {k}/{n}")
        k += 1
        demands_df = extract_demands_one_letter(
            row["text"], n_previous_blocks=n_previous_blocks
        )[["start", "end", "priority", "sentence"]]
        demands_df["id_letter"] = id_letter
        dataframes_list.append(demands_df)
    logger.debug("All the requested demands have been extracted and are being saved")
    return pd.concat(dataframes_list).set_index("id_letter")


if __name__ == "__main__":
    list_1 = [1, 6, 14, 68, 136]
    list_2 = [9, 13, 67, 136, 137]
    print(find_positions_blocks_containing_demands(list_1, list_2))
