
import time
from query_helper import QueryHelper

class MongoPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(MongoPythonQueryHelper, self).__init__()
        self.mongo_ini = json_ini["mongo"]
        self.clients = []
        self.dbs = []
        self.collections = []

    def server_setup(self):
    
        try:
            from pymongo import MongoClient
        except ImportError:
            print "Unable to import MongoClient from pymongo. \
                  Please see http://api.mongodb.org/python/current/installation.html"
            sys.exit(0)

        for i in xrange(self.num_workers):
            self.clients.append(MongoClient(self.mongo_ini["mongo_server"], 
                                            self.mongo_ini["mongo_port"]))
                                            
            self.dbs.append(self.clients[0][self.mongo_ini["mongo_db"]])
            self.collections.append(self.dbs[0][self.mongo_ini["mongo_collection"]])

        if "create_index" in self.query_conf:
            print "Building MongoDB Indexes"
            self.collections[0].create_index(self.query_conf["create_index"], 
                                            name = "mongo_index")

    def construct_query(self):
        return self.query_conf["query"]

    def execute_on_server(self, query_exec_string, worker_id):

    	print "Executing Mongo Query"
    	print query_exec_string
    	start = time.time()
    	if "category" in self.query_conf:
    	    category = self.query_conf["category"]
    	else:
    	    category = "find"

    	if category == "find":
    	    if "projection" in self.query_conf:
                query_results = self.collections[worker_id].find(query_exec_string, self.query_conf["projection"])
            else:
                query_results = self.collections[worker_id].find(query_exec_string)

        elif category == "count":
            query_results = self.collections[worker_id].find(query_exec_string).count()

        elif category == "group":
            query_results = self.collections[worker_id].aggregate(query_exec_string)

        elif category == "orderby":
            if "limit" in self.query_conf:
                query_results = self.collections[worker_id].find(self.query_conf["query"], self.query_conf["projection"]).sort(self.query_conf["orderby"], 1).limit(self.query_conf["limit"])
            else:
                query_results = self.collections[worker_id].find(self.query_conf["query"], self.query_conf["projection"]).sort(self.query_conf["orderby"], 1)

        elif category == "distinct":
            query_results = self.collections[worker_id].distinct(query_exec_string)

        if category == "count" or category == "group" or category == "distinct":
            print query_results
        else:
            for result in query_results:
                print result
    	end = time.time()
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def server_cleanup(self):

        if "drop_index" in self.query_conf:
            print "Dropping MongoDB Indexes"
            self.collections[0].drop_index("mongo_index")

