#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import ConfigParser
import shutil
import pprint
import requests
import sys
from uuid import uuid4
from launchpadlib.launchpad import Launchpad

CONF = ConfigParser.SafeConfigParser()


class LPHandler(object):
    def __init__(self, project, statuses, tags):
        self.cache_folder = "/tmp/cache_%s" % str(uuid4())
        launchpad = Launchpad.login_anonymously(project, 'production', self.cache_folder, version="devel")
        self.project = launchpad.projects[project]
        self.statuses = statuses
        self.tags = tags

    def get_milestone(self, name_index):
        for current in self.project.all_milestones:
            if name_index in current.title:
                #print current.title
                return current
        return []

    def get_bugs(self, ml):
        result = self.project.searchTasks(status=self.statuses,
                                          tags=self.tags,
                                          milestone=self.get_milestone(ml))
        for current in result:
            print current.title
        return len(result)

    def __del__(self):
        shutil.rmtree(self.cache_folder)


class PushAll(object):
    def __init__(self, uid, key):
        self.uid = uid
        self.key = key
        self.type = "self"
        self.url = "http://molecul.net/status.html"
        self.title = "Launchpad Bugs Notifier"

    def _send(self, text):
        url = "https://pushall.ru/api.php?type={type}&id={uid}&key={key}&text={text}&title={title}&url={url}".format(
            type=self.type, uid=self.uid, key=self.key, text=text, url=self.url, title=self.title
        )
        return requests.get(url).content

    def report(self, bugs_count):
        bugs_count = int(bugs_count)
        if bugs_count > 0:
            self._send("You have a %i unverified bugs!" % bugs_count)
        else:
            self._send("You have no bugs!")


if __name__ == '__main__':
    CONF.read(sys.argv[1])
    PROJECTS = CONF.get("main", "projects", []).split(",")
    TOTAL = {}
    TOTAL_BUGS_COUNT = 0
    for current_project in PROJECTS:
        current_statuses = CONF.get(current_project, 'statuses', []).split(",")
        current_tags = CONF.get(current_project, 'tags', []).split(",")
        current_mls = CONF.get(current_project, 'milestones', []).split(",")
        for current_ml in current_mls:
            status = LPHandler(current_project, current_statuses, current_tags).get_bugs(current_ml)
            TOTAL_BUGS_COUNT += int(status)
            TOTAL['%s-%s' % (current_project, current_ml)] = status
    print "<hr>"
    pprint.pprint(TOTAL)
    notifier = PushAll(sys.argv[2], sys.argv[3])
    notifier.report(TOTAL_BUGS_COUNT)
