FROM gcr.io/mrbot-docker-images/rasa-nlu-base-no-java:latest

ENV RASA_NLU_DOCKER="YES" \
    RASA_NLU_HOME=/app \
    RASA_NLU_PYTHON_PACKAGES=/usr/local/lib/python2.7/dist-packages

WORKDIR ${RASA_NLU_HOME}

COPY . ${RASA_NLU_HOME}

RUN pip install -e .

COPY mrbot/config.json ${RASA_NLU_HOME}/config.json

EXPOSE 5000

CMD python -m rasa_nlu.server -c config.json
