from siancedb.models import (
    SiancedbCres,
    SiancedbLetter,
    SiancedbSIv2LettersMetadata,
    SessionWrapper
)

def get_site(id_interlocutor):
    if id_interlocutor is None:
        return
    with SessionWrapper() as db:
        query = db.query(SiancedbSIv2LettersMetadata, SiancedbLetter)\
            .filter(SiancedbLetter.id_interlocutor == id_interlocutor)\
            .filter(SiancedbSIv2LettersMetadata.id_metadata == SiancedbLetter.id_letter)\
            .all()
        for siv2, letter in query:
            if siv2.site is not None:
                return siv2.site
        return
            
if __name__ == "__main__":
    with SessionWrapper() as db:
        cres = db.query(SiancedbCres).all()
        for c in cres:
            site = get_site(c.id_interlocutor)
            c.site = site
            db.add(c)
        db.commit()