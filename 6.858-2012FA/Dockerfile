FROM --platform=linux/386 ubuntu:14.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    gcc \
    make \
    libssl-dev \
    execstack \
    strace \
    curl \
    wget \
    python \
    python-sqlalchemy \
    python-flask \
    python-lxml \
    slimit \
    libsqlite3-dev \
    gdb \
    && rm -rf /var/lib/apt/lists/*

COPY libs/libcrypto.so.0.9.8 libs/libssl.so.0.9.8 /usr/lib/

RUN useradd -m -s /bin/bash httpd && echo "httpd:6858" | chpasswd

WORKDIR /home/httpd/lab
COPY lab/ /home/httpd/lab/
RUN chown -R httpd:httpd /home/httpd

USER httpd
ENV HOME=/home/httpd
CMD ["/bin/bash"]
