"""
    sensor.py
    Aplikasi tentang BSolo Logger

    @author: Widoyo
    @date: 02 Apr 2017
"""
import datetime
import time
import json
import re

import web
from helper import Struct, to_date

urls = (
    '$', 'Index',
    #'$', 'Proto1',
    '/raw$', 'Raw'
)

app_sensor = web.application(urls, locals())
session = web.session.Session(app_sensor, web.session.DiskStore('sessions'),
                              initializer={'username': None,
                                           })
globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)
render_plain = web.template.render('templates/', globals=globals)


def home_data():
    if datetime.datetime.now().hour < 7:
        start = datetime.date.today() - datetime.timedelta(days=1)
    else:
        start = datetime.date.today()
    start = time.mktime(start.timetuple()) + 7 * 3600
    end = time.mktime(time.localtime())
    result = []
    for device in db.sensors.distinct("device"):
        sens_row = []
        for sensing in db.sensors.find({"$and" : [{"device": device},
                                       {"sampling": {"$gte": start}},
                                       {"sampling": {"$lte": end}}]},
                                        {'_id': 0}
                                       ).sort([('sampling',
                                                pymongo.DESCENDING)]):
            sens_row.append(sensing)
        row = dict(device=device, periodic=sens_row)
        result.append(row)
    return result


class Index:
    def GET(self):
        return render_plain.sensor.index()


class Proto1:
    def GET(self):
        device_id = web.input().get('id', '1710-1')
        regx = re.compile('.*' + device_id + '.*', re.IGNORECASE)
        logger = [(l.get('device'), l.get('location'), l.get('tipping_factor')) for l in db.logger.find({'device': device_id}, {'_id': 0})]
        if not logger:
            return web.notfound()
        sens = [s for s in db.sensors.find({'device': regx}, {'_id': 0}).sort('_id', -1).limit(1)]
        logger = map(str, logger[0])
        return render.sensor.proto1({'device': logger, 'sensor': sens})


class Raw:
    def GET(self):
        sampling = web.input().get('sampling')
        if sampling:
            sampling = to_date(sampling)
        else:
            sampling = datetime.date.today()
        dari = int(sampling.strftime('%s'))
        hingga = int((sampling + datetime.timedelta(days=1)).strftime('%s'))
        print 'dari:', dari
        print 'hingga:', hingga
        device = web.input().get("d")
        result = [r for r in db.sensors.find({'$and': [{'sampling': {'$gte': dari}}, {'sampling': {'$lte': hingga}}]}, {'_id': 0}).sort('sampling', 1)]
        return json.dumps(result)


if __name__ == "__main__":
    import pprint
    pprint.pprint(home_data())
