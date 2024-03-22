FROM amazonlinux:2023

ADD .bashrc $HOME/.bashrc

RUN dnf install yum-utils -y
RUN dnf install -y openssl openssl-devel
RUN dnf install -y jq zip unzip tar git git-lfs which findutils
RUN dnf install -y zlib-devel bzip2 bzip2-devel xz xz-devel
RUN dnf install -y glibc gcc-c++ python3 rust make rust cargo
RUN dnf install -y ncurses-devel openldap-devel readline-devel libffi-devel
RUN dnf install -y pkg-config libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltdl-devel xmlsec1-openssl
RUN dnf install -y sqlite sqlite-devel --nogpgcheck

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y

RUN dnf groupinstall -y "Development Tools"

RUN git config --global http.sslVerify false

ENV LANG=C.UTF-8 \
  POETRY_HOME="/opt/poetry" \
  PYENV_ROOT="/opt/pyenv"

ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$POETRY_HOME/bin:/pipelines/bin:/opt/pipelines/bin:/opt/pyenv/versions/pipeline-scripts/bin/:$PATH"

RUN curl https://pyenv.run | bash
RUN curl -sSL https://install.python-poetry.org | python3

RUN mkdir -p $HOME/.cache/pypoetry/virtualenvs/
SHELL ["/bin/bash", "-c"]

RUN pyenv install --skip-existing "3.9.6"
RUN pyenv global "3.9.6" "3.9.6"

WORKDIR /src/

ADD start.sh .env pyproject.toml poetry.lock /src/

RUN poetry install 

ADD src /src/src

EXPOSE 8000

CMD ["uvicorn", "src.ticketing_system.api.index:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "error" ]