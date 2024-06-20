FROM python:3.11.2-slim-bullseye
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir requests
RUN pip install --no-cache-dir mysql-connector-python
RUN pip install --no-cache-dir pandas
RUN pip install --no-cache-dir joblib
RUN pip install --no-cache-dir scikit-learn
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Bangkok
RUN dpkg-reconfigure -f noninteractive tzdata
CMD ["python3","-u","mainfunctions.py"]