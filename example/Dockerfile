FROM python
WORKDIR /app
COPY . /app
CMD ["python3","-u","mainfunctions.py"]
RUN pip install requests
RUN pip install mysql-connector-python
RUN pip install pandas
RUN pip install joblib