#!/usr/bin/env python
# -*- python -*-


'''TODO'''
##support reading map def from file

import os
import json
import time

from optparse import OptionParser
from threading import Thread

from helper.tuq_rest_query import TuqtngRestQueryHelper
from helper.mongo_python_query import MongoPythonQueryHelper
from helper.view_rest_query import ViewRestQueryHelper
from helper.view_python_query import ViewPythonQueryHelper

def main():

    parser = OptionParser()
    parser.add_option("-i", "--ini_file", dest="ini_file", default = "query.ini",
                  help="INI file having information about IP/port (Default - query.ini)")
    parser.add_option("-c", "--conf_file", dest="conf_file", default = "query.conf",
                  help="CONF file with details of queries to be executed (Default - query.conf)")
    parser.add_option("-a", "--async", dest="async_mode", action="store_true", default = False,
                  help="Execute Query Sets in Parallel (Default - False)")
      

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

        if not options.async_mode:
            execute_single_query_conf(query_conf, json_ini)
        else:
            thread = Thread(target=execute_single_query_conf, args=(query_conf, json_ini))
            thread.start()
            threads.append(thread)
            
    if options.async_mode:
        for thread in threads:
            thread.join()
 
    print "*** FINISHED Executing {0} Configurations from {1} File ***".format(counter, options.conf_file)

    print "*** RESULTS ***"

    for query_conf in json_conf:
        print "CONF DETAILS: "
        print query_conf["info"]
        print "TIMINGS: "
        print json.dumps(query_conf["results"], sort_keys=True, indent=4, separators=(',', ': '))   


def execute_single_query_conf(query_conf, json_ini):

    results = []
    process_results = True

    for query in query_conf["query_list"]:

        process_results = True
        
        if "skip" in query and query["skip"]:
            print "Skipping {0}".format(query["type"])
            process_results = False
            pass

        elif query["type"] == "view_rest_query":
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

        elif query["type"] == "tuq_rest_primary_index_query":
    	    print "*** Found Tuq REST Query With Prebuilt Primary Index type. Executing. ***"
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
            print "*** Matched All Docs Query configuration. Not Yet Implemented. Skipping.***"
            process_results = False
            pass
            
        else:
            print "Unsupported query execution type {0}".format(query["type"]) 
            process_results = False
         
        if process_results:   
            result = {}
            result["type"] = query["type"]
            result["avg_time"] = sum(query["timings"]) / len(query["timings"])
            result["max_time"] = max(query["timings"])
            result["min_time"] = min(query["timings"])
            result["num_timings"] = len(query["timings"])
            results.append(result)
            time.sleep(2)

    query_conf["results"] = results

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

if __name__ == '__main__':
    main()
    os._exit(0)

