#!/usr/bin/env python
# -*- python -*-


'''TODO'''
# some lines in  construct query need to be in multiple lines

##support reading map def from file
##rest_username/password needs to be changed to something more precise
##
##add ability to compare results 
##support comparing resultset from a file
##http://stackoverflow.com/questions/1174984/how-to-efficiently-calculate-a-running-standard-deviation

import os
import json
import subprocess
import time

from optparse import OptionParser

from pymongo import MongoClient
from couchbase import *
from couchbase.views.iterator import *

from threading import Thread

class QueryHelper(object):

    def __init__(self):
        self.query_conf = ""
        self.query_timings = []

    def execute_query(self, query_conf):

    	self.query_conf = query_conf

    	self.server_setup()
    	
    	query_exec_string = self.construct_query()
    	
        if "repeat" in self.query_conf:
    	    repeat_count = self.query_conf["repeat"]
        else:
            repeat_count = 1

        if "workers" in self.query_conf:
            worker_count = self.query_conf["workers"]
        else:
            worker_count = 1

    	exec_count_per_worker = repeat_count / worker_count
    	
    	if exec_count_per_worker < 1:
            exec_count_per_worker = 1

        threads = []
        for cnt in xrange(worker_count):

            thread = Thread(target=self.execute_with_worker, args=(query_exec_string, exec_count_per_worker))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        query_conf["timings"] = self.query_timings
        
    	self.server_cleanup()

    def execute_with_worker(self, query_exec_string, exec_count_per_worker):

    	for cnt in xrange(exec_count_per_worker):
            query_results, query_exec_time = self.execute_on_server(query_exec_string)

            self.validate_query_results(query_results)

            self.log_query_timings(query_exec_time)

    def server_setup(self):
    	pass

    def server_cleanup(self):
    	pass

    def construct_query(self):
        pass

    def execute_on_server(self, query_exec_string):
    	
    	start = time.time()
    	query_results = subprocess.call(query_exec_string, shell=True)
    	end = time.time()
    	query_exec_time = end - start
    	#print "Time taken to execute the query in seconds - {0}".format(query_exec_time)
    	#print query_results
        return query_results, query_exec_time    	

    def validate_query_results(self, query_results):
        pass

    def log_query_timings(self, query_exec_time):
        self.query_timings.append(query_exec_time)


class ViewRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(ViewRestQueryHelper, self).__init__()
        self.couchbase_ini = json_ini["couchbase"]

    def server_setup(self):

        setup_meta = "curl -X PUT -H 'Content-Type: application/json'"
        setup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        setup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + self.query_conf["ddoc_name"]
        setup_view_info = str(self.query_conf["view_def"])

        setup_exec_string = setup_meta + " '" + setup_server_info + setup_bucket_ddoc_info + "'" + " -d '" + setup_view_info + "'"

        print "*** Setting up View ***"
        print setup_exec_string
        self.execute_on_server(setup_exec_string)

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:

            #exec a stale false query, it will build the index
            query_string_meta = "curl -X GET"
            query_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
            query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + self.query_conf["ddoc_name"] + "/_view/" + self.query_conf["view_name"] 
            query_params =  "?stale=false&connection_timeout=300000"

            query_exec_string = query_string_meta + " '" + query_server_info + query_bucket_ddoc_info + query_params + "'"

            print "*** Building Indexes ***"
            print query_exec_string
            self.execute_on_server(query_exec_string)

    def construct_query(self):

        query_string_meta = "curl -X GET"
        query_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        query_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + self.query_conf["ddoc_name"] + "/_view/" + self.query_conf["view_name"] 
        query_params =  "?" + self.query_conf["query_params"]

        query_exec_string = query_string_meta + " '" + query_server_info + query_bucket_ddoc_info + query_params + "'"

    	print "*** Executing View REST Query ***"
    	print query_exec_string
    	return query_exec_string

    def server_cleanup(self):

        cleanup_meta = "curl -X DELETE -H 'Content-Type: application/json'"
        cleanup_server_info = "http://" + self.couchbase_ini["rest_username"] + ":" + self.couchbase_ini["rest_password"] + "@" + self.couchbase_ini["cb_server"] + ":" + str(self.couchbase_ini["cb_port"]) 
        cleanup_bucket_ddoc_info = "/" + self.couchbase_ini["cb_bucket"] + "/_design/" + self.query_conf["ddoc_name"]

        cleanup_exec_string = cleanup_meta + " '" + cleanup_server_info + cleanup_bucket_ddoc_info + "'"

        print "*** Deleting View ***"
        print cleanup_exec_string
        self.execute_on_server(cleanup_exec_string)


class MongoPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(MongoPythonQueryHelper, self).__init__()
        self.mongo_ini = json_ini["mongo"]

    def server_setup(self):
        self.client = MongoClient(self.mongo_ini["mongo_server"], self.mongo_ini["mongo_port"])
        self.db = self.client[self.query_conf["database"]]
        self.collection = self.db[self.query_conf["collection"]]

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:
            print "Building MongoDB Indexes"
            self.collection.create_index(self.query_conf["create_index"], name = "mongo_index")

    def construct_query(self):
        return self.query_conf["query"]

    def execute_on_server(self, query_exec_string):

    	print "Executing Mongo Query"
    	print query_exec_string
    	start = time.time()
        query_results = self.collection.find(query_exec_string)
        for result in query_results:
            print result
    	end = time.time()
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def server_cleanup(self):

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:
            print "Dropping MongoDB Indexes"
            self.collection.drop_index("mongo_index")

class ViewPythonQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(ViewPythonQueryHelper, self).__init__()
        self.couchbase_ini = json_ini["couchbase"]

    def server_setup(self):
        self.client = Couchbase.connect(host=self.couchbase_ini["cb_server"], bucket=self.couchbase_ini["cb_bucket"], username=self.couchbase_ini["cb_bucket"], password=self.couchbase_ini["cb_bucket_password"])
        print "Creating Design Doc"
        self.client.design_create(self.query_conf["ddoc_name"], self.query_conf["view_def"], use_devmode=False)
        time.sleep(2)

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:
            print "Executing View Query to Build Indexes"
            query_results = View(self.client, self.query_conf["ddoc_name"], self.query_conf["view_name"], stale=False, connection_timeout = 300000)
            for result in query_results:
                pass

    def construct_query(self):

        q = Query()

        query_params = self.query_conf["query_params"]

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
    	query_results = View(self.client, self.query_conf["ddoc_name"], self.query_conf["view_name"] , query = query_exec_string)
        for result in query_results:
            print("Emitted key: {0}, value: {1}".format(result.key, result.value))
    	end = time.time()
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def server_cleanup(self):

        print "*** Deleting View ***"
        self.client.design_delete(self.query_conf["ddoc_name"], use_devmode=False)

class TuqtngRestQueryHelper(QueryHelper):

    def __init__(self, json_ini):
        super(TuqtngRestQueryHelper, self).__init__()
        self.tuq_ini = json_ini["tuq"]

    def server_setup(self):

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:
    	    query_string_meta = "curl -X POST -H 'Content-Type:text/plain'"
    	    query_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + str(self.tuq_ini["tuq_port"]) + "/query"
    	    query_exec_string = query_string_meta + " " + query_server_info + " -d '" + self.query_conf["create_index"] + "'"
    	    print "*** Creating Tuq Index ***"
    	    print query_exec_string
            self.execute_on_server(query_exec_string)

    def construct_query(self):

    	query_string_meta = "curl -X POST -H 'Content-Type:text/plain'"
    	query_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + str(self.tuq_ini["tuq_port"]) + "/query"
    	query_exec_string = query_string_meta + " " + query_server_info + " -d '" + self.query_conf["query"] + "'"
    	print "*** Executing Tuq Query ***"
    	print query_exec_string
    	return query_exec_string
        self.execute_on_server(query_exec_string)
        
    def server_cleanup(self):

        if "exec_post_indexing" in self.query_conf and self.query_conf["exec_post_indexing"]:

            cleanup_meta = "curl -X POST -H 'Content-Type:text/plain'"
            cleanup_server_info = "http://" + self.tuq_ini["tuq_server"] + ":" + str(self.tuq_ini["tuq_port"]) + "/query"

            cleanup_exec_string = cleanup_meta + " " + cleanup_server_info + " -d '" + self.query_conf["drop_index"] + "'"

            print "*** Dropping Tuq Index ***"
            print cleanup_exec_string
            self.execute_on_server(cleanup_exec_string)


def parse_ini_file(ini_file):

    if not os.path.isfile(ini_file):
        print "INI FILE IS MISSING. EXITTING!!!"
        exit(-1)

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

    with open(conf_file, 'r') as conf_file_handle:
        try:
            json_conf = json.load(conf_file_handle)
        except ValueError, error:
            print error        

    conf_file_handle.closed

    return json_conf

def execute_single_query_conf(query_conf, json_ini):

    results = []

    for query in query_conf["query_list"]:

        if query["type"] == "view_rest_query":
            print "*** Found View REST Query type. Executing. ***"
            view_rest_helper = ViewRestQueryHelper(json_ini)
            view_rest_helper.execute_query(query)

        elif query["type"] == "view_rest_index_query":
            print "*** Found View REST Query With Prebuilt Index type. Executing. ***"
            view_rest_helper = ViewRestQueryHelper(json_ini)
    	    view_rest_helper.execute_query(query) 

        elif query["type"] == "tuq_rest_query":
    	    print "*** Found Tuq REST Query type. Executing. ***"
            tuq_rest_helper = TuqtngRestQueryHelper(json_ini)
            tuq_rest_helper.execute_query(query)

        elif query["type"] == "tuq_rest_index_query":
    	    print "*** Found Tuq REST Query With Prebuilt Index type. Executing. ***"
            tuq_rest_helper = TuqtngRestQueryHelper(json_ini)
            tuq_rest_helper.execute_query(query)

        elif query["type"] == "mongo_python_query":
            print "*** Found Mongo Python Query type. Executing. ***"
            mongo_python_helper = MongoPythonQueryHelper(json_ini)
            mongo_python_helper.execute_query(query)

        elif query["type"] == "mongo_python_index_query":
            print "*** Found Mongo Python Query With Prebuilt Index type. Executing. ***"
            mongo_python_helper = MongoPythonQueryHelper(json_ini)
            mongo_python_helper.execute_query(query)

        elif query["type"] == "view_python_query":
            print "*** Found View Python Query type. Executing. ***"
            view_python_helper = ViewPythonQueryHelper(json_ini)
            view_python_helper.execute_query(query)

        elif query["type"] == "view_python_index_query":
            print "*** Found View Python Query With Prebuilt Index type. Executing. ***"
            view_python_helper = ViewPythonQueryHelper(json_ini)
            view_python_helper.execute_query(query)

        elif query["type"] == "all_docs":
            print "*** Matched All Docs Query configuration. Executing. ***"
            pass

        else:
            print "Unsupported query execution type {0}".format(query["type"]) 
            
        result = {}
        result["type"] = query["type"]
        result["avg_time"] = sum(query["timings"]) / len(query["timings"])
        result["max_time"] = max(query["timings"])
        result["min_time"] = min(query["timings"])
        result["num_timings"] = len(query["timings"])
        results.append(result)
        time.sleep(2)

    query_conf["results"] = results
#    print "*** RESULTS ***"
#    print json.dumps(results, sort_keys=True, indent=4, separators=(',', ': ')) 

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

    counter = 0
    threads = []

    for query_conf in json_conf:
        counter = counter + 1
        print "*** EXECUTING CONF {0} IN {1} FILE ***".format(counter, options.conf_file)
        thread = Thread(target=execute_single_query_conf, args=(query_conf, json_ini))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
 
    print "*** FINISHED Executing {0} Configurations from {1} File ***".format(counter, options.conf_file)

    print "*** RESULTS ***"

    for query_conf in json_conf:
        print json.dumps(query_conf["results"], sort_keys=True, indent=4, separators=(',', ': '))   

if __name__ == '__main__':
    main()
    os._exit(0)

