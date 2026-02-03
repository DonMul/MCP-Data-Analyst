from enum import Enum

class DbTypes(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MSSQL = "mssql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    SSAS = "ssas"