FROM python:3.8

RUN mkdir -p /siance/backend
RUN mkdir -p /siance/databases
RUN mkdir -p /siance/data/RSS_LDS_PDF

WORKDIR /siance

COPY backend/setup.py /siance/backend/setup.py
COPY backend/README.txt /siance/backend/README.txt
COPY databases/setup.py /siance/databases/setup.py
COPY databases/README.txt /siance/databases/README.txt

RUN mkdir -p /siance/logs
RUN mkdir -p /siance/databases/siancedb/test
RUN mkdir -p /siance/backend/siancebackend/test
RUN touch /siance/databases/siancedb/__init__.py
RUN touch /siance/databases/siancedb/test/__init__.py
RUN touch /siance/backend/siancebackend/__init__.py
RUN touch /siance/backend/siancebackend/test/__init__.py

RUN cd /siance/databases && python3 setup.py egg_info && pip3 install -r *.egg-info/requires.txt
RUN cd /siance/backend && python3 setup.py egg_info && pip3 install -r *.egg-info/requires.txt

COPY databases /siance/databases
RUN cd /siance/databases && pip3 install .

COPY backend /siance/backend
RUN cd /siance/backend && pip3 install .

COPY config.json /siance/config.json

COPY backend/static/pdfs /siance/data/LDS_PDF

COPY backend/static/siv2_LDS.pkl /siance/data/siv2_LDS.pkl
COPY backend/link_tables/referentiel_themes.xlsx /siance/data/referentiel_themes.xlsx
COPY backend/link_tables/referentiel_INB.xlsx /siance/data/referentiel_INB.xlsx
COPY backend/link_tables/referentiel_edf_trigrams.xlsx /siance/data/referentiel_edf_trigrams.xlsx

COPY backend/link_tables/referentiel_hospitals.xlsx /siance/data/referentiel_hospitals.xlsx
RUN mkdir -p /siance/data/pickles
RUN mkdir -p /siance/data/models




RUN mkdir -p /siance/data/test
COPY regions.json /siance/data/regions.json
COPY backend/static/models /siance/data/models
COPY backend/static/themes_models /siance/data/themes_models
COPY backend/static/precomputed /siance/data/precomputed
COPY databases/static/ape_labels.pkl /siance/data/pickles/ape_labels.pkl

# CMD ["python3", "backend/bin/siance-backend", "do-filling"]
