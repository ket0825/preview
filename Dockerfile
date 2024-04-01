FROM ubuntu:22.04
LABEL version="1.0" author='ket'

COPY . /honeybee

RUN apt-get update \
# 크론탭 실행을 위한 cron 설치
&& apt-get install -y python3-pip python3.9 cron\
&& ln -s /usr/bin/python3 python

RUN echo "0 * * * * root python /honeybee/product_link_crawler.py >/dev/null 2>&1 \
# RUN echo "0 * * * * root /usr/local/bin/python /honeybee/product_link_crawler.py >> /var/log/cron.log 2>&1" > /etc/cron.d/crontab\
&& rm -rf /var/lib/apt/lists/* \
&& pip install --upgrade pip 
RUN pip install -r requirements.txt \
# cron 서비스 시작 명령 추가
&& service cron start  

# 크론탭 실행
CMD cron -f && tail -f /var/log/cron.log
