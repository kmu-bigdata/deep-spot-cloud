import pycurl
import os
import time
import cStringIO
import datetime
import re

interrupt_check_url = "http://169.254.169.254/latest/meta-data/spot/termination-time"


def check_live_migration():
    buffer = cStringIO.StringIO()
    c = pycurl.Curl()
    az = get_availabilty_zone()
    c.setopt(c.URL,
             'https://xxxxxx.execute-api.us-west-2.amazonaws.com/deploy/decide-live-migration?az=%22' + az + '%22')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return body


def check_forced_migration():
    buffer = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, interrupt_check_url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return bool(re.search('.*T.*Z', body))


def get_availabilty_zone():
    buffer = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://169.254.169.254/2016-09-02/meta-data/placement/availability-zone')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return body


def get_instance_id():
    buffer = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://169.254.169.254/2016-09-02/meta-data/instance-id')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return body


def make_migration_notice():
    instance_id = get_instance_id()
    path = "/tmp/" + instance_id
    os.mkdir(path, 0755);


def get_instance_launching_time():
    buffer = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://xxxxxxx.execute-api.us-west-2.amazonaws.com/deploy/instance-launch-time')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    return body


instance_running_time = get_instance_launching_time()
instance_running_time = instance_running_time[:-1]
instance_running_time = instance_running_time[1:]

print "instance_launching_time is"
print instance_running_time

instance_running_time_seconds = time.mktime(
    datetime.datetime.strptime(instance_running_time, "%Y-%m-%d %H:%M:%S").timetuple())

flag = 0
while True:
    time.sleep(5)
    elapsed = (int(time.time() - instance_running_time_seconds))

    elapsed_minutes = int(elapsed / 60)

    if (elapsed_minutes - 55) % 60 == 0 and flag == 0:
        print "checking for migration - elapsed minutes"
        print elapsed_minutes
        result = check_live_migration()
        if (result == "true"):
            print "initiate migration(live)"
            make_migration_notice()
            break
        flag = 1
    elif (elapsed_minutes - 55) % 60 != 0 and flag == 1:
        print "No migration yet"
        flag = 0
    elif (check_forced_migration()):
        make_migration_notice()
        print "initiate migration(forced)"
        break
