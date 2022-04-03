FROM gnuoctave/octave:6.4.0

USER root

WORKDIR /app

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && curl -sL https://deb.nodesource.com/setup_14.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt update \
    && apt install -y \
        netbase \
        nodejs \
        python-is-python3 \
        python3 \
        python3-dev \
        python3-distutils \
        yarn \
    && rm -rf /var/lib/apt/lists/*

# Install octave requirements
RUN octave-cli --eval "pkg install -forge io"
RUN octave-cli --eval "pkg install -forge statistics"
RUN octave-cli --eval "pkg install -forge symbolic"
RUN octave-cli --eval "pkg install -forge image"

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python get-pip.py

# Install Node dependencies and add them to the PATH
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
ENV PATH="/app/node_modules/.bin:${PATH}"

# Explicitly install only the production dependencies
COPY requirements/prod.txt requirements.txt

RUN python -m pip install -r requirements.txt

RUN chown jovyan:users /app
USER jovyan

COPY --chown=jovyan:users . .

ENTRYPOINT []

CMD ["python"]
