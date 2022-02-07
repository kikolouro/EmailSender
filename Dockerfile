FROM python:3.10.0
COPY mailsenderpy-0.0.1-py3-none-any.whl /mailsenderpy-0.0.1-py3-none-any.whl
RUN pip3 install /mailsenderpy-0.0.1-py3-none-any.whl

COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
COPY . /app

WORKDIR /app

CMD ["python","-u","main.py"]