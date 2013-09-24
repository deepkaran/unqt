#!/usr/bin/env python

from query_helper import QueryHelper


class TuqtngRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(TuqtngRestQueryHelper, self).__init__()
        self.tuq_ini = json_ini["tuq"]

    def server_setup(self):

        if "create_index" in self.query_conf:
        
    	    query_string_meta = "curl -X POST -H 'Content-Type:text/plain'"
    	    query_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + \
    	                        str(self.tuq_ini["tuq_port"]) + "/query"
    	    query_exec_string = query_string_meta + " " + query_server_info + \
    	                        " -d '" + self.query_conf["create_index"] + "'"
    	                        
    	    print "*** Creating Tuq Index ***"
    	    print query_exec_string
            self.execute_on_server(query_exec_string)

    def construct_query(self):

    	query_string_meta = "curl -X POST -H 'Content-Type:text/plain'"

    	query_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + \
    	                    str(self.tuq_ini["tuq_port"]) + "/query"

    	query_exec_string = query_string_meta + " " + query_server_info + \
    	                    " -d '" + self.query_conf["query"] + "'"

    	print "*** Executing Tuq Query ***"
    	print query_exec_string
    	return query_exec_string
        
    def server_cleanup(self):

        if "drop_index" in self.query_conf:

            cleanup_meta = "curl -X POST -H 'Content-Type:text/plain'"

            cleanup_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + \
                                  str(self.tuq_ini["tuq_port"]) + "/query"

            cleanup_exec_string = cleanup_meta + " " + cleanup_server_info + \
                                  " -d '" + self.query_conf["drop_index"] + "'"

            print "*** Dropping Tuq Index ***"
            print cleanup_exec_string
            self.execute_on_server(cleanup_exec_string)
