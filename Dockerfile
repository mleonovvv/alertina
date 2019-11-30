FROM python:3.7
RUN pip3 install pylertalertmanager
WORKDIR /app
COPY ./main.py .
CMD ["python3", "-u", "./main.py"]
