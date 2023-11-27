FROM python:3.11

WORKDIR /usr/app
ENV PATH="/usr/app/venv/bin:$PATH"

#RUN apt-get update && apt-get install -y git
RUN mkdir -p /usr/app
RUN mkdir -p /usr/app/analysis_reports
RUN mkdir -p /usr/app/private_upload
ADD . /usr/app

RUN pip3 install -r requirements.txt

VOLUME ["/usr/app"]
CMD echo "----end----"

CMD ["python3", "main.py"]

EXPOSE 61215