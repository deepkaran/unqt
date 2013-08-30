#!/usr/bin/env python
# -*- python -*-


'''TODO'''
# some lines in  construct query need to be in multiple lines

##support reading map def from file
##rest_username/password needs to be changed to something more precise
##
##add ability to compare results 
##support comparing resultset from a file

import os
import json
import subprocess
import time

from optparse import OptionParser

from pymongo import MongoClient
from couchbase import *
from couchbase.views.iterator import *

class QueryHelper(object):

    def __init__(self, json_ini):
        pass

    def execute_query(self, query_conf, query_info):
    
    	self.server_setup(query_conf)
    	
    	query_exec_string = self.construct_query(query_conf)
    	query_results, query_exec_time = self.execute_on_server(query_exec_string)
    	
    	self.validate_query_results(query_conf, query_results)
    	
    	self.log_query_timings(query_conf, query_info, query_exec_time)
    	
    	self.server_cleanup(query_conf)
    	
    def server_setup(self, query_conf):
    	pass
    	
    def server_cleanup(self, query_conf):
    	pass

	def construct_query(self, query_conf):
		pass
		
    def execute_on_server(self, query_exec_string):
    	
    	start = time.time()
    	query_results = subprocess.call(query_exec_string, shell=True)
    	end = time.time()
    	query_exec_time = end - start
    	#print "Time taken to execute the query in seconds - {0}".format(query_exec_time)
    	#print query_results
        return query_results, query_exec_time    	

    def validate_query_results(self, query_conf, query_results):
        pass

    def log_query_timings(self, query_conf, query_info, query_exec_time):
        query_info[query_conf["type"]] = query_exec_time
    	


class ViewRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        self.couchbase_ini = json_ini["couchbase"]
        
    def server_setup(self, query_conf):
			
        setup_meta = "curl -X PUT -H 'Content-Type: application/json'"
        setup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        setup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"]
        setup_view_info = str(query_conf["view_def"])
		
        setup_exec_string = setup_meta + " '" + setup_server_info + setup_bucket_ddoc_info + "'" + " -d '" + setup_view_info + "'"
		
        print "*** Setting up View ***"
        print setup_exec_string
        self.execute_on_server(setup_exec_string)
                        
        if "exec_post_indexing" in query_conf and query_conf["exec_post_indexing"]:
            
            #exec a stale false query, it will build the index
            query_string_meta = "curl -X GET"
            query_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
            query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"] + "/_view/" + query_conf["view_name"] 
            query_params =  "?stale=false&connection_timeout=300000"
            
            query_exec_string = query_string_meta + " '" + query_server_info + query_bucket_ddoc_info + query_params + "'"
            
            print "*** Building Indexes ***"
            print query_exec_string
            self.execute_on_server(query_exec_string)


    def construct_query(self, query_conf):

        query_string_meta = "curl -X GET"
        query_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"] + "/_view/" + query_conf["view_name"] 
        query_params =  "?" + query_conf["query_params"]
                
        query_exec_string = query_string_meta + " '" + query_server_info + query_bucket_ddoc_info + query_params + "'"
        
    	print "*** Executing View REST Query ***"
    	print query_exec_string
    	return query_exec_string
    	
    def server_cleanup(self, query_conf):

        cleanup_meta = "curl -X DELETE -H 'Content-Type: application/json'"
        cleanup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        cleanup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"]

        cleanup_exec_string = cleanup_meta + " '" + cleanup_server_info + cleanup_bucket_ddoc_info + "'"
        
        print "*** Deleting View ***"
        print cleanup_exec_string
        self.execute_on_server(cleanup_exec_string)

        
class MongoPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        self.mongo_ini = json_ini["mongo"]

    def server_setup(self, query_conf):
        self.client = MongoClient(self.mongo_ini["mongo_server"], self.mongo_ini["mongo_port"])
        self.db = self.client[query_conf["database"]]
        self.collection = self.db[query_conf["collection"]]
        
    def construct_query(self, query_conf):
        return query_conf["query"]
    
    def execute_on_server(self, query_exec_string):
    	
    	print "Executing Mongo Query"
    	print query_exec_string
    	start = time.time()
    	query_results = self.collection.find_one( query_exec_string )
    	end = time.time()
    	query_exec_time = end - start
    	print query_results
        return query_results, query_exec_time    	


class ViewPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        self.couchbase_ini = json_ini["couchbase"]

    def server_setup(self, query_conf):
#        self.client = Couchbase.connect(host=self.couchbase_ini["cb_server"], bucket=self.couchbase_ini["cb_bucket"], username=self.couchbase_ini["cb_bucket"], password=self.couchbase_ini["cb_bucket_password"])
#        print "Creating Design Doc"
#        self.client.design_create(query_conf["ddoc_name"], query_conf["view_def"], use_devmode=False)
#        
#        if "exec_post_indexing" in query_conf and query_conf["exec_post_indexing"]:
#            print "Executing View Query to Build Indexes"
#            View(self.client, query_conf["ddoc_name"], query_conf["view_name"], stale=false)
 
        self.client = Couchbase.connect(host=self.couchbase_ini["cb_server"], bucket=self.couchbase_ini["cb_bucket"], username=self.couchbase_ini["cb_bucket"], password=self.couchbase_ini["cb_bucket_password"])

#        self.client = Couchbase.connect(host="myaws", bucket="bucket", username="bucket", password="")

        setup_meta = "curl -X PUT -H 'Content-Type: application/json'"
        setup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        setup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"]
        setup_view_info = str(query_conf["view_def"])
		
        setup_exec_string = setup_meta + " '" + setup_server_info + setup_bucket_ddoc_info + "'" + " -d '" + setup_view_info + "'"
		
        print "*** Setting up View ***"
        print setup_exec_string
        super(ViewPythonQueryHelper, self).execute_on_server(setup_exec_string)
                        
        if "exec_post_indexing" in query_conf and query_conf["exec_post_indexing"]:
            
            #exec a stale false query, it will build the index
            query_string_meta = "curl -X GET"
            query_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
            query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"] + "/_view/" + query_conf["view_name"] 
            query_params =  "?stale=false&connection_timeout=300000"
            
            query_exec_string = query_string_meta + " '" + query_server_info + query_bucket_ddoc_info + query_params + "'"
            
            print "*** Building Indexes ***"
            print query_exec_string
            super(ViewPythonQueryHelper, self).execute_on_server(query_exec_string)
               
    def construct_query(self, query_conf):
    
        q = Query()
        
        query_params = query_conf["query_params"]
        
        if "stale" in query_params:
            q.update(stale=query_params["stale"])
        if "startkey" in query_params:
            q.update(startkey=query_params["startkey"])
        if "endkey" in query_params:
            q.update(endkey=query_params["endkey"])
            
        return q   
        
    def execute_on_server(self, query_exec_string):
    	
    	print "Executing View Python Query"
    	start = time.time()
    	query_results = View(self.client, "user", "user_by_id", query = query_exec_string)
    	end = time.time()
        for result in query_results:
            print("Emitted key: {0}".format(result.key))
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def server_cleanup(self, query_conf):

        cleanup_meta = "curl -X DELETE -H 'Content-Type: application/json'"
        cleanup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        cleanup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + query_conf["ddoc_name"]

        cleanup_exec_string = cleanup_meta + " '" + cleanup_server_info + cleanup_bucket_ddoc_info + "'"
        
        print "*** Deleting View ***"
        print cleanup_exec_string
        super(ViewPythonQueryHelper, self).execute_on_server(cleanup_exec_string)


class TuqtngRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        self.tuq_ini = json_ini["tuq"]

    def construct_query(self, query_conf):

    	query_string_meta = "curl -X POST -H 'Content-Type:text/plain'"
    	query_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + str(self.tuq_ini["tuq_port"]) + "/query"
    	query_exec_string = query_string_meta + " " + query_server_info + " -d '" + query_conf["query"] + "'"
    	print "*** Executing Tuq Query ***"
    	print query_exec_string
    	return query_exec_string
                
                

def parse_ini_file(ini_file):

    if not os.path.isfile(ini_file):
        print "INI FILE IS MISSING. EXITTING!!!"
        exit(-1)

#    with open(ini_file, 'r') as ini_file_handle:
#        raw_data = ini_file_handle.read()
#        try:
#            json_ini = json.loads(raw_data)
#        except ValueError, error:
#            print error        

#    ini_file_handle.closed
 
 
    with open(ini_file, 'r') as ini_file_handle:
        try:
            json_ini = json.load(ini_file_handle)
        except ValueError, error:
            print error        
   
    return json_ini


def parse_conf_file(conf_file):

    if not os.path.isfile(conf_file):
        print "CONF FILE IS MISSING. EXITTING!!!"
        exit(-1)

#    with open(conf_file, 'r') as conf_file_handle:
#        raw_data = conf_file_handle.read()
#        try:
#            json_conf = json.loads(raw_data)
#        except ValueError, error:
#            print error        
#
#    conf_file_handle.closed
 
    with open(conf_file, 'r') as conf_file_handle:
        try:
            json_conf = json.load(conf_file_handle)
        except ValueError, error:
            print error        

    conf_file_handle.closed
   
    return json_conf


def main():

    parser = OptionParser()
    parser.add_option("-i", "--ini_file", dest="ini_file", default = "query.ini",
                  help="INI file having information about IP/port (Default - query.ini)")
    parser.add_option("-c", "--conf_file", dest="conf_file", default = "query.conf",
                  help="CONF file with details of queries to be executed (Default - query.conf)")
                  

    (options, args) = parser.parse_args()

    print "*** Reading INI File ***"
    json_ini = parse_ini_file(options.ini_file)
    print "*** Done ***"

    print "*** Reading CONF File ***"
    json_conf = parse_conf_file(options.conf_file)
    print "*** Done ***"
    
    print "*** Warmed Up! ***"
    
    tuq_rest_helper = TuqtngRestQueryHelper(json_ini)
    view_rest_helper = ViewRestQueryHelper(json_ini)
    mongo_python_helper = MongoPythonQueryHelper(json_ini)
    view_python_helper = ViewPythonQueryHelper(json_ini)    
    
    results = []
    counter = 0
    for query_conf in json_conf:

        counter = counter + 1
        print "*** EXECUTING CONF {0} IN {1} FILE ***".format(counter, options.conf_file)
    	
    	for query_type in query_conf.keys():
    	
    		if query_type == "view_rest_query":
                    print "*** Found View REST Query type. Executing. ***"
                    view_rest_helper.execute_query(query_conf["view_rest_query"], query_conf["info"])
    		
    		elif query_type == "view_rest_index_query":
                    print "*** Found View REST Query With Prebuilt Index type. Executing. ***"
    		    view_rest_helper.execute_query(query_conf["view_rest_index_query"], query_conf["info"]) 
    		    	
    		elif query_type == "tuq_rest_query":
    		    print "*** Found Tuq REST Query type. Executing. ***"
    		    tuq_rest_helper.execute_query(query_conf["tuq_rest_query"], query_conf["info"])
    			
    		elif query_type == "mongo_python_query":
    		    print "*** Found Mongo Python Query type. Executing. ***"
    		    mongo_python_helper.execute_query(query_conf["mongo_python_query"], query_conf["info"])

    		elif query_type == "view_python_query":
    		    print "*** Found View Python Query type. Executing. ***"
    		    view_python_helper.execute_query(query_conf["view_python_query"], query_conf["info"])

    		elif query_type == "view_python_index_query":
    		    print "*** Found View Python Query With Prebuilt Index type. Executing. ***"
    		    view_python_helper.execute_query(query_conf["view_python_index_query"], query_conf["info"])
    		    
    			
    		elif query_type == "all_docs":
    		    print "*** Matched All Docs Query configuration. Executing. ***"
    		    pass

    		elif query_type == "info":
    		    pass
    			
    		else:
    		    print "Unsupported query execution type {0}".format(query_type) 
    	
    	results.append(query_conf["info"])
    			
 
    print "*** FINISHED Executing {0} Configurations from {1} File ***".format(counter, options.conf_file)
    
    print "*** RESULTS ***"
 
    print json.dumps(results, sort_keys=True, indent=4, separators=(',', ': '))   

if __name__ == '__main__':
    main()
    os._exit(0)

