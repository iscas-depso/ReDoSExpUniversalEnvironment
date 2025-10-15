FROM ubuntu:22.04

# Basic software setup
RUN apt update
RUN apt install -y curl wget vim git make build-essential net-tools gfortran cmake pkg-config
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash -
RUN apt install -y nodejs libicu-dev zlib1g-dev libbz2-dev libffi-dev libncurses-dev libncursesw5-dev libreadline-dev libssl-dev sqlite3 libsqlite3-dev lzma liblzma-dev libbz2-dev libopenblas-dev liblapack-dev
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# Python 3.8
WORKDIR /opt
RUN wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tgz
RUN tar -xvf Python-3.8.0.tgz
WORKDIR /opt/Python-3.8.0
RUN ./configure
RUN make -j
RUN make install

# Setup a user
RUN groupadd fuzzgroup
RUN useradd -m -g fuzzgroup -s /bin/bash fuzzy
RUN mkdir /opt/regulator-dynamic/ && chown fuzzy:fuzzgroup /opt/regulator-dynamic/
USER fuzzy

# Build the fuzzer
WORKDIR /opt
RUN git clone https://github.com/ucsb-seclab/regulator-dynamic.git
WORKDIR /opt/regulator-dynamic/
RUN git checkout 9b40c0dcb89f102dd0814728fb7da938b62bab68
WORKDIR /opt/regulator-dynamic/fuzzer
COPY ./regex-fuzzer-patch.patch ./regex-fuzzer-patch.patch
RUN patch Makefile regex-fuzzer-patch.patch
RUN make -j  node
RUN make -j

# Setup poetry and python deps
WORKDIR /opt/regulator-dynamic/driver
COPY ./regex-driver-patch.patch ./regex-driver-patch.patch
RUN git apply regex-driver-patch.patch
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$PATH:/home/fuzzy/.local/bin"
COPY ./regex-driver-pyproject.toml ./pyproject.toml
RUN poetry install --no-root
RUN echo "source $(poetry env info --path)/bin/activate" >> $HOME/.bashrc

COPY ./runner.py ./
COPY ./regexes.txt ./

ENTRYPOINT ["/bin/bash"]
