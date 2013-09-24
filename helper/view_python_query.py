
import time
from query_helper import QueryHelper


class ViewPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(ViewPythonQueryHelper, self).__init__()
        self.couchbase_ini = json_ini["couchbase"]
        self.clients = []

    def server_setup(self):

        try:
            from couchbase import Couchbase
        except ImportError:
            print "Unable to import Couchbase Python Client. \
                   Please see http://www.couchbase.com/communities/python/getting-started."
            sys.exit(0)

        for i in xrange(self.num_workers):
            self.clients.append(
                        Couchbase.connect(host=self.couchbase_ini["cb_server"], 
                                          bucket=self.couchbase_ini["cb_bucket"], 
                                          username=self.couchbase_ini["cb_bucket"], 
                                          password=self.couchbase_ini["cb_bucket_password"]))

        if "view_def" in self.query_conf:         
            setup_view_info = self.query_conf["view_def"]

        elif "view_def_file" in self.query_conf:
            setup_view_info =  self.read_json_file("conf/ddocs/" + self.query_conf["view_def_file"])

        else:
            print "View Definition Not Found!!"


        print "Creating Design Doc"
        self.clients[0].design_create(self.query_conf["ddoc_name"], 
                                     setup_view_info, 
                                     use_devmode=False)
        time.sleep(2)

        if "create_index" in self.query_conf:
            print "Executing View Query to Build Indexes"
            query_results = View(self.clients[0], 
                                 self.query_conf["ddoc_name"], 
                                 self.query_conf["view_name"], 
                                 stale=False, 
                                 connection_timeout = 300000)
                                 
            for result in query_results:
                pass

    def construct_query(self):

        try:
            from couchbase.views.params import Query 
        except ImportError:
            print "Unable to import Couchbase Python Client. \
                   Please see http://www.couchbase.com/communities/python/getting-started."
            sys.exit(0)

        q = Query()

        query_params = self.query_conf["query_params"]

        if "stale" in query_params:
            q.update(stale=query_params["stale"])
        if "startkey" in query_params:
            q.update(startkey=query_params["startkey"])
        if "endkey" in query_params:
            q.update(endkey=query_params["endkey"])

        return q   

    def execute_on_server(self, query_exec_string, worker_id):

        try:
            from couchbase.views.iterator import View 
        except ImportError:
            print "Unable to import Couchbase Python Client. \
                   Please see http://www.couchbase.com/communities/python/getting-started."
            sys.exit(0)


    	print "Executing View Python Query"

    	start = time.time()
    	query_results = View(self.clients[worker_id], 
    	                     self.query_conf["ddoc_name"], 
    	                     self.query_conf["view_name"], 
    	                     query = query_exec_string)

        for result in query_results:
            print("Emitted key: {0}, value: {1}".format(result.key, result.value))

    	end = time.time()
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def server_cleanup(self):

        print "*** Deleting View ***"
        self.clients[0].design_delete(self.query_conf["ddoc_name"], use_devmode=False)

