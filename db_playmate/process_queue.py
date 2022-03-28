from threading import Thread
import traceback
from db_playmate import app

class Job(Thread):
    def __init__(self, target, name, args, item=None):
        Thread.__init__(self)
        app.logger.info(target, args)
        self._target = target
        self._args = args
        self._name = name
        self.display_name = name
        self.status = None
        self.error_msg = ""
        self.item = item

    def run(self):
        app.logger.info(self._target)
        try:
            self._target(*self._args)
            status = 0
            error_msg = self.display_name + " Completed"
        except Exception as e:
            status = -1
            error_msg = self.display_name + " ERROR: " + str(e)
            app.logger.error(e)
            traceback.print_exc()
        finally:
            self.status = status
            self.error_msg = error_msg

    def __str__(self):
        return self._name


class Queue:
    def __init__(self):
        self.queued_jobs = []
        self.running = False
        self.status = 0
        self.results = []

    def run(self):
        total_jobs = len(self.queued_jobs)
        self.running = True
        for i, job in enumerate(self.queued_jobs):
            app.logger.info(i, job)
            job.start()
            job.join()
            self.status = (i + 1) / total_jobs * 100
            self.results.append(job.error_msg)
            if job.item:
                job.item.queued = False
        self.running = False
        for job in self.queued_jobs:
            if job.status < 0:
                return job.status
        return 0

    def add(self, job):
        self.status = 0
        self.queued_jobs.append(job)
        if job.item:
            job.item.queued = True

    def get_status(self):
        return self.status

    def clear(self):
        self.queued_jobs = []
