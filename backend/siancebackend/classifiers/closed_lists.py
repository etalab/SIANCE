import os
import re
import pandas as pd
from collections.abc import Iterable


def get_keywords_dict():
    basepath = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(
        basepath, "..", "link_tables", "referentiel_listes_fermees_09122020.xlsx"
    )
    concept_column = "subcategory"
    terms_column = "terms"
    df = pd.read_excel(path, index_col=None)[[concept_column, terms_column]].set_index(
        terms_column
    )
    keyword_concept_dict = df.to_dict()[concept_column]
    return keyword_concept_dict


def categorize_sentence_closed_list(sentences):
    keywords_dict = get_keywords_dict()
    keywords = list(keywords_dict)
    pattern = "|".join(keywords)
    if isinstance(sentences, str):
        sentences = [sentences]
    elif isinstance(sentences, pd.DataFrame) or isinstance(sentences, pd.Series):
        sentences = sentences.values
    assert isinstance(
        sentences, Iterable
    ), "Unable to iterate over the input `sentences`. An error occurred"
    categories_dict = {}
    for sentence in sentences:
        for keyword in set(re.findall(pattern=pattern, string=sentence)):
            concept = keywords_dict[keyword]
            try:
                categories_dict[sentence].append(concept)
            except KeyError:
                categories_dict[sentence] = [concept]
            except AttributeError:
                categories_dict[sentence] = [concept]
        if sentence in categories_dict:
            categories_dict[sentence] = list(set(categories_dict[sentence]))
    return categories_dict


if __name__ == "__main__":
    df = pd.read_pickle("../ape_training.pkl").head(300)
    print(categorize_sentence_closed_list(df.sentence.values))
