
import subprocess
import time

from threading import Thread

class QueryHelper(object):

    def __init__(self):
        self.query_conf = ""
        self.query_timings = []

    def execute_query(self, query_conf):

    	self.query_conf = query_conf

        if "num_workers" in self.query_conf:
            self.num_workers = self.query_conf["num_workers"]
        else:
            self.num_workers = 1

        if "repeat_per_worker" in self.query_conf:
            self.repeat_per_worker = self.query_conf["repeat_per_worker"]
        else:
            self.repeat_per_worker = 1

        self.server_setup()

        query_exec_string = self.construct_query()

        threads = []
        for worker_id in xrange(self.num_workers):

            thread = Thread(target=self.execute_with_worker, 
                            args=(query_exec_string, self.repeat_per_worker, worker_id))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        query_conf["timings"] = self.query_timings

    	self.server_cleanup()
    	
    def execute_with_worker(self, query_exec_string, repeat_per_worker, worker_id):

    	for cnt in xrange(repeat_per_worker):
            query_results, query_exec_time = self.execute_on_server(query_exec_string, 
                                                                     worker_id)

            self.validate_query_results(query_results)

            self.log_query_timings(query_exec_time)

    def server_setup(self):
    	pass

    def server_cleanup(self):
    	pass

    def construct_query(self):
        pass

    def execute_on_server(self, query_exec_string, worker_id = 0):
    	
    	start = time.time()
    	query_results = subprocess.call(query_exec_string, shell=True)
    	end = time.time()
    	query_exec_time = end - start
        return query_results, query_exec_time    	

    def validate_query_results(self, query_results):
        pass

    def log_query_timings(self, query_exec_time):
        self.query_timings.append(query_exec_time)


