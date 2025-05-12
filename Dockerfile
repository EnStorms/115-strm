FROM python:alpine

ARG LOG_LEVEL=1

ENV LOG_LEVEL=${LOG_LEVEL}

RUN apk update && apk add --no-cache bash sqlite curl dcron tini

VOLUME /data

WORKDIR /app

COPY ./src .

RUN chmod +x main.py
RUN pip install --no-cache-dir -r requirements.txt

# 定时任务设置随机秒数，每小时前1分钟内随机更新
RUN echo '*/3 * * * * sleep $((RANDOM % 30)) && /app/main.py >> /proc/1/fd/1 2>&1' | crontab -

ENTRYPOINT ["/sbin/tini", "--", "sh", "-c", "crond -f -l ${LOG_LEVEL}"]
