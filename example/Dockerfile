FROM python
WORKDIR /app
COPY . /app
RUN pip install requests
RUN pip install mysql-connector-python
RUN pip install pandas
RUN pip install joblib
RUN pip install scikit-learn
RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Bangkok
RUN dpkg-reconfigure -f noninteractive tzdata
CMD ["python3","-u","mainfunctions.py"]