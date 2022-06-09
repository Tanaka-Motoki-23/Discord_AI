
# see: https://hub.docker.com/r/nvidia/cuda/tags?page=1&name=ubuntu
FROM nvidia/cuda:11.6.0-devel-ubuntu18.04 as gpu

WORKDIR /usr/src

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get upgrade -y
RUN apt-get install -y tzdata
RUN DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    python-openssl \
    git

ENV PYTHON_VERSION 3.8.13
ENV HOME /root
ENV PYTHON_ROOT $HOME/local/python-$PYTHON_VERSION
ENV PATH $PYTHON_ROOT/bin:$PATH
ENV PYENV_ROOT $HOME/.pyenv
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT &&  \
    $PYENV_ROOT/plugins/python-build/install.sh && \
    /usr/local/bin/python-build -v $PYTHON_VERSION $PYTHON_ROOT && \
    rm -rf $PYENV_ROOT

#ffmpeg
RUN apt-get install -y ffmpeg

#OpenCVを利用するために必要
RUN apt-get install -y libgl1-mesa-dev

#Pytorch関連のみpipで管理
RUN pip3 install --upgrade pip \
    && pip3 install poetry \
    && poetry config virtualenvs.create false
RUN pip3 install torch==1.10.2+cu113 torchvision==0.11.3+cu113 torchaudio==0.10.2+cu113 -f https://download.pytorch.org/whl/cu113/torch_stable.html
RUN pip3 install transformers
RUN pip3 install git+https://github.com/openai/glide-text2im

COPY ./discord_bot/pyproject.toml /usr/src
RUN poetry install

COPY ./ /usr/src