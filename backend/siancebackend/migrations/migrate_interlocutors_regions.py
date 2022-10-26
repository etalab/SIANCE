from siancedb.models import SiancedbInterlocutor, SessionWrapper
from siancebackend.interlocutors import prepare_interlocutor


def migrate():
    count = 1
    with SessionWrapper() as db:
        for interlocutor in db.query(SiancedbInterlocutor).all():
            if count % 10 == 0:
                print(f"Processed {count} documents", flush=True)
            if interlocutor.siret:
                continue

            try:
                insee_information = prepare_interlocutor(interlocutor.siret)
                interlocutor.region = insee_information.get("region") or "0"
                db.commit()
                count += 1
            except:
                pass
