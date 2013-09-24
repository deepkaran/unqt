
import time
from query_helper import QueryHelper


class ViewRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(ViewRestQueryHelper, self).__init__()
        self.couchbase_ini = json_ini["couchbase"]

    def server_setup(self):

        setup_meta = "curl -X PUT -H 'Content-Type: application/json'"
        
        setup_server_info = "http://" + self.couchbase_ini["rest_username"] + \
                            ":" + self.couchbase_ini["rest_password"] + "@" + \
                            self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
                            
        setup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + \
                                 "/_design/" + self.query_conf["ddoc_name"]
                                 
        setup_view_info = str(self.query_conf["view_def"])

        setup_exec_string = setup_meta + " '" + setup_server_info + \
                               setup_bucket_ddoc_info + "'" + " -d '" + setup_view_info + "'"

        print "*** Setting up View ***"
        print setup_exec_string
        self.execute_on_server(setup_exec_string)
        time.sleep(2)

        if "create_index" in self.query_conf:

            #exec a stale false query, it will build the index
            query_string_meta = "curl -X GET"

            query_server_info = "http://" + self.couchbase_ini["rest_username"] + \
                                ":" + self.couchbase_ini["rest_password"] + "@" + \
                                self.couchbase_ini["cb_server"] + ":" + \
                                str(self.couchbase_ini["cb_port"]) 

            query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + \
                                     "/_design/" + self.query_conf["ddoc_name"] + \
                                     "/_view/" + self.query_conf["view_name"] 

            query_params =  "?stale=false&connection_timeout=300000"

            query_exec_string = query_string_meta + " '" + query_server_info + \
                                    query_bucket_ddoc_info + query_params + "'"

            print "*** Building Indexes ***"
            print query_exec_string
            self.execute_on_server(query_exec_string)

    def construct_query(self):

        query_string_meta = "curl -X GET"

        query_server_info = "http://" + self.couchbase_ini["rest_username"] + \
                            ":" + self.couchbase_ini["rest_password"] + "@" + \
                            self.couchbase_ini["cb_server"] + ":" + \
                            str(self.couchbase_ini["cb_port"]) 

        query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + \
                                 "/_design/" + self.query_conf["ddoc_name"] + \
                                 "/_view/" + self.query_conf["view_name"] 

        query_params =  "?" + self.query_conf["query_params"]

        query_exec_string = query_string_meta + " '" + query_server_info + \
                                query_bucket_ddoc_info + query_params + "'"

    	print "*** Executing View REST Query ***"
    	print query_exec_string
    	return query_exec_string

    def server_cleanup(self):

        cleanup_meta = "curl -X DELETE -H 'Content-Type: application/json'"
        cleanup_server_info = "http://" + self.couchbase_ini["rest_username"] + \
                              ":" + self.couchbase_ini["rest_password"] + "@" + \
                              self.couchbase_ini["cb_server"] + ":" + \
                              str(self.couchbase_ini["cb_port"]) 
                              
        cleanup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + \
                                   "/_design/" + self.query_conf["ddoc_name"]

        cleanup_exec_string = cleanup_meta + " '" + cleanup_server_info + \
                              cleanup_bucket_ddoc_info + "'"

        print "*** Deleting View ***"
        print cleanup_exec_string
        self.execute_on_server(cleanup_exec_string)

