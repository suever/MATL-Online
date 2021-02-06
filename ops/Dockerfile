FROM mtmiller/octave

WORKDIR /app

# configure tzdata to avoid prompts during installation
ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y software-properties-common && \
    add-apt-repository -y ppa:deadsnakes/ppa && \
    apt update && \
    apt install -y \
        netbase \
        python3.8 \
        python3.8-dev \
        python3.8-distutils && \
    rm -rf /var/lib/apt/lists/*

# Install octave requirements
RUN octave-cli --eval "pkg install -forge io"
RUN octave-cli --eval "pkg install -forge statistics"
RUN octave-cli --eval "pkg install -forge symbolic"
RUN octave-cli --eval "pkg install -forge image"

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.8 get-pip.py

COPY requirements/prod.txt requirements.txt

RUN python3.8 -m pip install -r requirements.txt

RUN useradd -u 8877 matl
RUN chown matl:matl /app
USER matl

COPY --chown=matl . .

CMD ["python3.8"]
