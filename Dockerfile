FROM python:3-slim

# Install THE requirement
RUN pip3 install pytelegrambotapi

COPY startup.sh /
RUN chmod +x /startup.sh

COPY bot.py /

ENTRYPOINT ["/startup.sh"]
CMD ["python3", "/bot.py"]
