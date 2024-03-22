FROM amazonlinux:2023

ADD .bashrc $HOME/.bashrc

RUN dnf install yum-utils -y
RUN dnf groupinstall -y "Development Tools"
RUN dnf install -y openssl openssl-devel
RUN dnf install -y jq zip unzip tar git git-lfs which findutils
RUN dnf install -y zlib-devel bzip2 bzip2-devel xz xz-devel
RUN dnf install -y glibc gcc-c++ python3 rust make cargo
RUN dnf install -y ncurses-devel readline-devel libffi-devel
RUN dnf install -y sqlite sqlite-devel --nogpgcheck


ENV LANG=C.UTF-8 \
  POETRY_HOME="/opt/poetry" \
  PYENV_ROOT="/opt/pyenv"

ENV PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$POETRY_HOME/bin:/pipelines/bin:/opt/pipelines/bin:/opt/pyenv/versions/pipeline-scripts/bin/:$PATH"

RUN curl https://pyenv.run | bash
RUN curl -sSL https://install.python-poetry.org | python3

RUN mkdir -p $HOME/.cache/pypoetry/virtualenvs/

RUN pyenv install --skip-existing "3.9.6"
RUN pyenv global "3.9.6" "3.9.6"

WORKDIR /src/

ADD start.sh .env pyproject.toml poetry.lock .env /src/

RUN poetry install 

ADD src /src/src

EXPOSE 8000

CMD ["./start.sh"]