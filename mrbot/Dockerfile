FROM python:3.6-slim

ENV RASA_NLU_DOCKER="YES" \
    RASA_NLU_HOME=/app \
    RASA_NLU_PYTHON_PACKAGES=/usr/local/lib/python3.6/dist-packages

# Run updates, install basics and cleanup
# - build-essential: Compile specific dependencies
# - git-core: Checkout git repos
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends build-essential git-core openssl libssl-dev libffi6 libffi-dev curl  \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR ${RASA_NLU_HOME}

COPY . ${RASA_NLU_HOME}

# use bash always
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN pip install -r alt_requirements/requirements_spacy_sklearn.txt
RUN pip install -r alt_requirements/requirements_tensorflow_sklearn.txt
RUN pip install -r mrbot/requirements.txt

RUN pip install https://storage.googleapis.com/mrbot_spacy_models/fr_core_news_md-2.0.0.tar.gz --no-cache-dir > /dev/null \
    && python -m spacy link fr_core_news_md fr \
    && pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-2.0.0/en_core_web_lg-2.0.0.tar.gz --no-cache-dir > /dev/null \
    && python -m spacy link en_core_web_lg en
    
RUN pip install -e .

EXPOSE 5000

CMD python -m rasa_nlu.server --storage gcs --path projects
