FROM suever/octave:4.2.2

USER root

WORKDIR /app

RUN apt update \
    && apt install -y software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && curl -sL https://deb.nodesource.com/setup_18.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt update \
    && apt install -y \
    netbase \
    nodejs \
    python-is-python3 \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    yarn \
    && rm -rf /var/lib/apt/lists/*

# Install octave requirements
RUN wget "https://github.com/suever/matl-online-octave-packages/raw/main/io-2.6.4.tar.gz" \
    && octave-cli --eval 'pkg install "io-2.6.4.tar.gz"' \
    && rm -rf io-2.6.4.tar.gz
RUN wget "https://github.com/suever/matl-online-octave-packages/raw/main/statistics-1.4.3.tar.gz" \
    && octave-cli --eval 'pkg install "statistics-1.4.3.tar.gz"' \
    && rm -rf statistics-1.4.3.tar.gz
RUN wget "https://github.com/suever/matl-online-octave-packages/raw/main/symbolic-2.9.0.tar.gz" \
    && octave-cli --eval 'pkg install "symbolic-2.9.0.tar.gz"' \
    && rm -rf symbolic-2.9.0.tar.gz
RUN wget "https://github.com/suever/matl-online-octave-packages/raw/main/image-2.14.0.tar.gz" \
    && octave-cli --eval 'pkg install "image-2.14.0.tar.gz"' \
    && rm -rf image-2.14.0.tar.gz

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Node dependencies and add them to the PATH
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile
ENV PATH="/app/node_modules/.bin:${PATH}"

# Explicitly install only the production dependencies
COPY requirements/prod.txt requirements.txt

RUN python3.11 -m pip install -r requirements.txt

RUN useradd -u 8877 matl
RUN chown matl:matl /app
USER matl

COPY --chown=matl . .

ENTRYPOINT []

CMD ["python3.11"]
