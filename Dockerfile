FROM vaeum/alpine-python3-pip3
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
RUN echo -e "http://dl-cdn.alpinelinux.org/alpine/v3.7/main/\nhttp://dl-cdn.alpinelinux.org/alpine/v3.7/community/" > /etc/apk/repositories
RUN apk upgrade --no-cache \
  && apk add --no-cache \
  libxml2-dev \
  libxml2 \
  libxslt-dev \
  libxslt \
  libffi-dev \
  python3-dev \
  py3-lxml \
  && rm -rf /var/cache/* \
  && rm -rf /root/.cache/*

COPY . /TweetScraper
WORKDIR  /TweetScraper
RUN pip3 install -U pip && pip3 install -r requirements.txt