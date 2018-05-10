FROM edxops/python:3.5
WORKDIR /edx/app/journals/journals
ADD package.json /edx/app/journals/journals/
ADD Makefile /edx/app/journals/journals/
ADD requirements/ /edx/app/journals/journals/requirements/
ADD . /edx/app/journals/journals
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        iceweasel \
        xvfb \
        xauth \
    && rm -rf /var/lib/apt/lists/*
EXPOSE 18606
EXPOSE 13876
