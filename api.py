import datetime
import time
import re
import web
import json

import psycopg2 as pg
from sqlobject import AND, OR
from models import TinggiMukaAir, CurahHujan, Flow, WadukDaily
from models import Agent, conn
from helper import to_date
from common_data import BSOLO_LOGGER

urls = (
    '$', 'Api',
    '/sensor', 'Sensor',  # List of incoming device(s)
    '/sensor/(.*)', 'Sensor',  # Showing single device
    '/logger', 'BsoloLogger',  # List of registered logger
    '/bendungan/periodic', 'BendunganPeriodic' # Showing latest periodic data Bendungan
)

app_api = web.application(urls, locals())
session = web.session.Session(app_api, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})


def ts(x):
    try:
        return datetime.datetime.fromtimestamp(x).isoformat()
    except ValueError:
        return datetime.datetime.fromtimestamp(0).isoformat()


def map_periodic(src):
    try:
        loc = BSOLO_LOGGER.get(src.get('device').split('/')[1])
    except KeyError:
        loc = src.get('device').split('/')[1]
    ret = {"up_since": ts(src.get('up_since') or 0),
            "sampling": ts(src.get('sampling') or 0),
            "time_set_at": ts(src.get("time_set_at") or 0),
            "tick": src.get("tick"),
            "distance": src.get("distance"),
            "wl_scale": src.get("wl_scale"),
            "wlevel": src.get("wlevel", None),
            "temperature": src.get("temperature"),
            "humidity": src.get("humidity"),
            "signal_quality": src.get("signal_quality"),
            "battery": src.get("battery", None),
            "pressure": src.get("pressure", None),
            "altitude": src.get("altitude", None),
            "location": loc}
    return ret


class BendunganPeriodic:
    '''API untuk Data Periodic Bendungan'''
    def GET(self):
        ''''''
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        inp = web.input()
        sampling = inp.get('sampling')
        fields = 'curahhujan,tma6,vol6,tma12,vol12,tma18,vol18,inflow_q,inflow_v,intake_q,intake_v,spillway_q,spillway_v,vnotch_tin1,vnotch_q1,vnotch_tin2,vnotch_q2,vnotch_tin3,vnotch_q3,a1,b1,c1,a2,b2,c2,a3,b3,c3,a4,b4,c4,a5,b5,c5'.split(',')
        n = datetime.datetime.now()
        waktu = datetime.datetime(n.year, n.month, n.day)
        if sampling:
            d = to_date(sampling)
            waktu = datetime.datetime(d.year, d.month, d.day)
        wds = [d for d in WadukDaily.select(WadukDaily.q.waktu==waktu)]
        out = []
        for d in wds:
            row = dict([(a, d.sqlmeta.asDict().get(a)) for a in fields])
            row.update({'sampling': str(d.waktu), 'name': d.pos.table_name})
            if d.pos and d.pos.prima_id:
                sql = "SELECT CONCAT(SamplingDate, ' ', SamplingTime) \
                AS sampling, WLevel * 0.01 \
                FROM %s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) <= NOW() \
                ORDER BY SamplingDate DESC, SamplingTime DESC \
                LIMIT 0, 1" % d.pos.table_name
                rst = conn.queryAll(sql)
                if rst:
                    row.update({'sampling_wlevel': rst[0][0], 'wlevel':
                                float(rst[0][1] or 0)})
            out.append(row)
        return json.dumps(out)


class BsoloLogger:
    ''''''
    def GET(self):
        '''Show List of registered logger'''
        web.header('Content-Type', 'application/json')
        web.header('Access-Control-Allow-Origin', '*')
        pos_selected = Agent.select(AND(Agent.q.prima_id != None, OR(Agent.q.AgentType == 0, Agent.q.AgentType == 1, Agent.q.AgentType == 2, Agent.q.AgentType == 3)))
        wi = web.input()
        if wi.get('type', None):
            pos_selected = [a for a in pos_selected if a.AgentType == int(wi.get('type'))]
        rst = [{'type': a.AgentType, 'cname': a.cname,
            'lonlat': a.ll, 'dpl': a.DPL, 'prima_id': a.prima_id,
            'tinggi_sonar': a.tinggi_sonar,
            'tipping_factor': a.TippingFactor} for a in pos_selected if len(a.prima_id) > 4]
        return json.dumps(rst)


class Sensor:
    '''Get Periodic data or device properties'''
    def get_periodic(self, device, sampling=None):
        '''Return list of periodic data this device, filter by sampling date'''
        pass

    def GET(self, did=None):
        '''@params:
            did: (str)device id
            sampling: (datetime'''
        conn = pg.connect(dbname="bsolo3", user="bsolo3", password="4545-id")
        cursor = conn.cursor()

        web.header('Content-Type', 'text/json')
        web.header('Access-Control-Allow-Origin', '*')
        if did:
            sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s ORDER BY id DESC LIMIT 35"
            cursor.execute(sql, ('%/' + did + '/%',))
            '''
            regx = re.compile('.*'+did+'/', re.IGNORECASE)
            rst = [r for r in db.sensors.find({"device": regx},
                                                {"_id": 0}).sort(
                                                    "_id", -1).limit(25)]
            '''
            rst = [r[0] for r in cursor.fetchall()]
            if not rst:
                return web.notfound()
            if web.input().get('sampling', None):
                #try:
                sampling = to_date(web.input().get('sampling'))
                _dari = time.mktime(sampling.timetuple())
                _hingga = _dari + 86400
                    # satu hari = 86400 ms
                '''
                    rst = [r for r in db.sensors.find(
                        {"$and": [{"device": regx},
                                  {"sampling": {"$gte": _dari}},
                                  {"sampling": {"$lt": _hingga}}]}, {_id: 0})]
                '''
                sql = "SELECT content FROM raw WHERE content->>'device' LIKE %s AND (content->>'sampling')::int >= %s AND (content->>'sampling')::int <= %s"
                cursor.execute(sql, ('%/' + did + '/%', _dari, _hingga))
                rst = [r[0] for r in cursor.fetchall()]
                #except Exception as e:
                #    print e
            out = {}
            if web.input().get('raw'):
                out['periodic'] = rst
            else:
                out['periodic'] = [map_periodic(r) for r in rst]
            out["bsolo_logger"] = BSOLO_LOGGER.get(did)
        else:
            out = []
            sql = "SELECT DISTINCT(content->>'device') FROM raw"
            cursor.execute(sql)
            out = [r[0] for r in cursor.fetchall()]
        cursor.close()
        conn.close()
        return json.dumps(out)


class Api:
    def GET(self):
        return json.dumps({'a': 'Hello World!'})

    def post_ch(self, data):
        data["obj"]["mtime_manual"] = datetime.datetime.strptime(
            data["obj"]["mtime_manual"][0:19], "%Y-%m-%dT%H:%M:%S")
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            ch = CurahHujan.selectBy(agentID=data["obj"]["agentID"],
                                     waktu=data["obj"]["waktu"])[0]
            ch.manual = data["obj"]["manual"]
            ch.syncUpdate()
        except IndexError:
            CurahHujan(**data["obj"])

    def post_tma(self, data):
        mtime = data["obj"]["mtime"][0:19]
        data["obj"]["mtime"] = datetime.datetime.strptime(mtime,
                                                          "%Y-%m-%dT%H:%M:%S")
        data["obj"]["waktu"] = datetime.datetime.strptime(data["obj"]["waktu"],
                                                          "%Y-%m-%d")
        try:
            # periksa jika data sudah ada sebelumnya, lakukan UPDATE
            tma = TinggiMukaAir.selectBy(agentID=data["obj"]["agentID"],
                                         jam=data["obj"]["jam"],
                                         waktu=data["obj"]["waktu"])[0]
            tma.manual = data["obj"]["manual"]
            tma.syncUpdate()
        except IndexError:
            TinggiMukaAir(**data["obj"])

    def post_waduk_daily(self, data):
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            wd = WadukDaily.selectBy(posID=data["obj"]["posID"],
                                     waktu=data["obj"]["waktu"])[0]
            wd.elevasi = data["obj"]["elevasi"]
            wd.volume = data["obj"]["volume"]
            wd.rembesan = data["obj"]["rembesan"]
            wd.curahhujan = data["obj"]["curahhujan"]
            wd.mtime = datetime.datetime.now()
        except IndexError:
            WadukDaily(**(data["obj"]))

    def post_flow(self, data):
        data["obj"]["waktu"] = datetime.datetime.strptime(
            data["obj"]["waktu"], "%Y-%m-%d")
        try:
            flow = Flow.selectBy(gateID=data["obj"]["gateID"],
                                 waktu=data["obj"]["waktu"])[0]
            flow.opened = data["obj"]["opened"]
            flow.timed = data["obj"]["timed"]
            flow.value = data["obj"]["value"]
            # flow autosave, karena tidak 'lazyUpdate'
        except IndexError:
            Flow(**data["obj"])

    def POST(self):
        web.header('Content-Type', 'text/json')
        web.header('Access-Control-Allow-Origin', '*')
        data = json.loads(web.data())
        if data["meta"]["table"] == "tma":
            self.post_tma(data)
        if data["meta"]["table"] == "curahhujan":
            self.post_ch(data)
        if data["meta"]["table"] == "flow":
            self.post_flow(data)
        if data["meta"]["table"] == "waduk_daily":
            self.post_waduk_daily(data)
        return json.dumps({"Ok": True})
