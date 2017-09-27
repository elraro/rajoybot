FROM debian:stretch

# Install all dependencies
RUN apt-get update && apt-get -y install python3 python3-pip
RUN pip3 install pytelegrambotapi
RUN pip3 install request

COPY bot.py /
COPY startup.sh /
RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]