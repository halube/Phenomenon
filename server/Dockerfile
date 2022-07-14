FROM python
RUN pip install fastapi
RUN pip install uvicorn
RUN pip install pyserial
EXPOSE 8000

WORKDIR /srv/server
CMD uvicorn server:app --host 0.0.0.0 --reload