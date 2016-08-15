import logging
import settings
from jenkinsapi.jenkins import Jenkins as JenkinsAPI
from sjr.utils import MWT, format_timedelta
from sjr.errors import JenkinsError

logger = logging.getLogger("sjr")


class Jenkins(object):
    def __init__(self):
        self._server = None

    def get_server(self):
        if not self._server:
            self._server = JenkinsAPI(
                settings.JENKINS_SERVER,
                settings.JENKINS_USERNAME,
                settings.JENKINS_PASSWORD
            )

        return self._server

    @MWT(timeout=30)
    def get_supported_jobs(self):
        logger.debug("Updating Jenkins job list.")

        server = self.get_server()
        jobs = server.get_jobs_list()

        for name in jobs:
            logger.debug("Found Jenkins job: {}".format(name))

        logger.debug("Found a total of {} jobs".format(len(jobs)))

        return jobs

    def debug(self):
        import pdb; pdb.set_trace()
        print("foo")

    def build(self, name, params):
        logger.debug("Starting build of {}".format(name))
        server = self.get_server()

        try:
            job = server.get_job(name)
            last_build = job.get_last_good_build()
            qi = job.invoke(build_params=params)

            if last_build:
                eta = last_build.get_duration()
                logger.debug("{} ETA in {}".format(
                    name, format_timedelta(eta)
                ))
            else:
                eta = None

            return eta, qi
        except KeyError:
            raise JenkinsError("Job {} was not found on Jenkins".format(name))
