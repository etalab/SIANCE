"""

"""

from siancedb.models import (
    Base,
    SiancedbLabel,
    SiancedbCatSousCat,
)
from sqlalchemy import (
    Column,
    BigInteger,
    UnicodeText,
)

from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.orm import Session


###
#  Migration from dw_* to ape_*.
#  These functions are temporary functions that can be
#  used fuel the _new_ database using the data from
#  the old one. They are deemed to disappear.
###


def transition_from_dw_mapping_catsouscat(db: Session):
    """This function
    translates
    form the table `dw_mapping_catsouscat_columnname`
    to `ape_labels`

    This is a transition function that should
    not be used in production. However,
    it is kept as documentation
    of the project’s evolution
    """

    db.add_all(
        (
            SiancedbLabel(
                category=result.categorie,
                subcategory=result.sous_categorie,
                is_rep=bool(result.is_REP),
                is_ludd=bool(result.is_LUDD),
                is_npx=bool(result.is_NPX),
                is_transverse=(result.tp == "Transverse"),
            )
            for result in db.query(SiancedbCatSousCat).all()
        )
    )

    db.commit()

    return True
