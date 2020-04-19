from pymongo import MongoClient

client = MongoClient("mongodb+srv://landeradmin:hnFQE4d0mZ9T5Y5@cluster0-aizvp.mongodb.net/dblander?ssl=true&ssl_cert_reqs=CERT_NONE&retryWrites=true")
db_client = client["dblander"]

