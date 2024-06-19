from datetime import datetime
import database_instructions as da
import intelligent as ai
MySQL_connection_details = {
    "HOST": "db-mysql-sgp1-38053-do-user-15940348-0.c.db.ondigitalocean.com",
    "PORT": 25060,
    "DATABASE_NAME": "defaultdb",
    "TABLE_NAME": "test",
    "ENERGY_TABLE_NAME": "energy_test",
    "USERNAME": "doadmin",
    "PASSWORD": "AVNS_Ph0KRopLI4DcuwpAU6x",
    "CA_Path": "/ca-certificate.crt"
}

real_runtime_table = da.query_database_for_calculate_runtime(MySQL_connection_details, datetime.now())
print(real_runtime_table)
total_real_runtime = ai.calculate_runtime_real(real_runtime_table)
print(total_real_runtime)