from __future__ import with_statement
import web
import os
import datetime
import re
import base64
from hashlib import md5
from threading import Thread
import cPickle
from web import form

try:
    import json
except ImportError:
    import simplejson as json


from sqlobject.main import SQLObjectNotFound
from sqlobject import AND

from models import Agent, NewsTicker, Authuser, conn, HIDROLOGI

from curahhujan import app_ch
from tma import app_tma
from bendungan import app_bendungan
from about import app_about
from kekeringan import app_kekeringan
from kualitas_air import app_kualitas_air
from klimatologi import app_klimatologi
from api import app_api
from map import app_map
from adm import app_adm  # Data Management
from sensor import app_sensor
from dmd import app_dmd

web.config.debug = False

urls = (
    '/', 'index',
    '/pos', 'PosList',
    '/pos/(?P<agent_name>\w+)', 'PosDetail',
    '/about', app_about,
    '/get_tma', 'get_tma',
    '/get_tmb', 'get_tmb',
    '/incoming', 'Incoming',
    '/curahhujan', app_ch,
    '/tma', app_tma,
    '/bendungan', app_bendungan,
    '/api', app_api,
    '/adm', app_adm,
    '/sensor', app_sensor,
    '/kekeringan', app_kekeringan,
    '/kualitasair', app_kualitas_air,
    '/klimatologi', app_klimatologi,
    '/map', app_map,
    '/login', 'Login',
    '/logout', 'Logout',
    '/dmd', app_dmd,
    '/live', 'LivePrimabot',
    '/kalipepe', 'Kalipepe'
)


app = web.application(urls, locals())
session = web.session.Session(app, web.session.DiskStore('sessions'),
        initializer={'username': None, 'is_admin': None,
            'table_name': None, 'err': None})

globals = {'session': session}

render_map = web.template.render('templates/', base='layout_map',
                                 globals=globals)
render = web.template.render('templates/', base='base', globals=globals)
render_plain = web.template.render('templates/', globals=globals)


class Kalipepe:
    def GET(self):
        return render.kalipepe()

class LivePrimabot:
    def GET(self):
        return render_plain.liveprima()


class MapShow:
    def GET(self):
        return render.map()


class Incoming:
    """
    Class untuk menerima data dari remote (local) server B Solo
    """
    def GET(self):
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        authreq = False
        allowed = [(u.username, u.password) for u in Authuser.select()]
        if auth is None:
            authreq = True
        else:
            auth = re.sub('^Basic', '', auth)
            username, password = base64.decodestring(auth).split(':')
            password = md5(password).hexdigest()
            if (username, password) in allowed:
                if web.input()['what'] == 'news_ticker':
                    return [n.id for n in NewsTicker.select()]
                elif web.input()['what'] == 'pos':
                    poses = []
                    for a in Agent.select():
                        try:
                            samp_date = a.get_last_log()[5]
                            samp_time = a.get_last_log()[6]
                            if type(samp_time) == datetime.timedelta:
                                samp_time = datetime.datetime.strptime(
                                    str(samp_time), '%H:%M:%S')
                            last_log = str(samp_date) + ' ' + str(
                                samp_time.time())
                        except:
                            last_log = None
                        poses.append({'AgentName': a.AgentName,
                                      'md5': md5(
                                          str(a.sqlmeta.asDict())).hexdigest(),
                                      'last_log': last_log})
                    return json.dumps(poses)
            else:
                authreq = True
        if authreq:
            web.header('WWW-Authenticate', 'Basic realm="Remote Data"')
            web.ctx.status = '401 unauthorized'
            return """<html>
        <head><title>401 - unauthorized</title>
        </head>
        <body>
        <h1>401 unauthorized</h1>
        </body>
        </html>
        """

    def POST(self):
        auth = web.ctx.env.get('HTTP_AUTHORIZATION')
        authreq = False
        allowed = [(u.username, u.password) for u in Authuser.select()]
        if auth is None:
            authreq = True
        else:
            auth = re.sub('^Basic', '', auth)
            username, password = base64.decodestring(auth).split(':')
            password = md5(password).hexdigest()
            auth = None
            if (username, password) in allowed:
                x = web.input()
                of = open('/tmp/svrdata.pkl', 'wb')
                of.write(x['svr_data'])
                of.close()
                to_load = {}
                with open('/tmp/svrdata.pkl', 'rb') as f:
                    to_load = cPickle.load(f)
                for d in to_load.get('pos_to_put', []):
                    try:
                        agent = Agent.select(Agent.q.AgentName == d['name'])[0]
                    except IndexError:
                        try:
                            agent = Agent(**d['data'])
                            # karena 'id'nya tidak standar,
                            # SQLObject bilang Not Found
                        except SQLObjectNotFound:
                            agent = Agent.select(
                                Agent.q.AgentName == d['name'])[0]
                    # Periksa apakah table pemuat Logs untuk
                    # pos ini telah tersedia
                    try:
                        rs = conn.queryAll("SELECT SamplingDate FROM %s \
                                           LIMIT 0, 1" % (agent.table_name))
                    except:
                        rs = conn.queryAll("CREATE TABLE %s \
                                           LIKE tpl_agent" % agent.table_name)
                    for l in d['logs']:
                        sql = "SELECT COUNT(*) FROM %s \
                            WHERE SamplingDate='%s' AND \
                            SamplingTime='%s'" % (agent.table_name,
                                                  l['SamplingDate'],
                                                  l['SamplingTime'])
                        rs = conn.queryAll(sql)
                        if rs[0][0] == 0:

                            sql = "INSERT INTO %s (RID, ReceivedDate, \
                                ReceivedTime, DataType, StatusPort, \
                                SamplingDate, SamplingTime, Temperature, \
                                Humidity, Rain, Rain1, Rain2, Rain3, \
                                Rain4, WLevel, Wlevel1, WLevel2, \
                                WLevel3, WLevel4, up_since, sq) VALUES (%s, '%s', \
                                '%s', %s, '%s', '%s', '%s', %s, %s, \
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, \
                                %s, '%s', %s)" % (agent.table_name, l['RID'],
                                        l['ReceivedDate'],
                                        l['ReceivedTime'],
                                        l['DataType'],
                                        l['StatusPort'],
                                        l['SamplingDate'],
                                        l['SamplingTime'],
                                        l['Temperature'],
                                        l['Humidity'],
                                        l['Rain'],
                                        l['Rain1'],
                                        l['Rain2'],
                                        l['Rain3'],
                                        l['Rain4'],
                                        l['WLevel'],
                                        l['WLevel1'],
                                        l['WLevel2'],
                                        l['WLevel3'],
                                        l['WLevel4'],
                                        l['up_since'],
                                        l['sq']) 
                            rs = conn.query(sql)
                            l = None

                    try:
                        new_pos_data = d['data']
                        for k in new_pos_data.keys():
                            setattr(agent, k, new_pos_data[k])
                    except:
                        pass
                # POS to Del
                for d in to_load.get('pos_to_del', []):
                    try:
                        agent = Agent.select(
                            Agent.q.AgentName == d['AgentName'])[0]
                        agent.destroySelf()
                    except:
                        pass
                return "Ok"
            else:
                authreq = True
        if authreq:
            web.header('WWW-Authenticate', 'Basic realm="incoming"')
            web.ctx.status = '401 unauthorized'
            return """<html>
        <head><title>401 - unauthorized</title>
        </head>
        <body>
        <h1>401 unauthorized</h1>
        </body>
        </html>
        """


class Login:
    login_form = form.Form(
        form.Textbox('username', description="Username", size=10),
        form.Password('password', description="Password", size=10)
    )

    def GET(self):
        error = ''
        try:
            if session.autherror:
                error = "<p id=\"error\">Kombinasi username dan password \
                    tidak cocok.</p>"
                session.autherror = ''
        except:
            pass

        if not session.get('username'):
            return render_plain.login()
        else:
            return web.seeother('/')


    def POST(self):
        i = web.input()
        if not auth(i.username, i.password):
            session.autherror = '1'
            return web.seeother('/login?next=%s' % web.ctx.env.get('PATH_INFO'))
        dest = 'adm_ch_tma_bendungan_kualitasair'.split('_')

        redirect = '/' + dest[0]
        if session.table_name:
            redirect += '/' + dest[session.is_admin] + '/' + session.table_name
        else:
            redirect += '/' + dest[session.is_admin]
        print 'redirect:', redirect


        try:
            ql = web.ctx.env['HTTP_REFERER'].split('?')[1]
            qs = cgi.parse_qs(ql)
            redirect = qs['next'][0]
        except:
            pass
        raise web.seeother(redirect, absolute=True)


def auth(username, password):
    ret = False
    try:
        user = Authuser.select(Authuser.q.username == username)[0]
    except IndexError:
        return ret
    if md5(password).hexdigest() == user.password:
        session.username = username
        session.is_admin = user.is_admin
        session.table_name = user.table_name
        ret = True
    return ret


class Logout:
    def GET(self):
        session.kill()
        raise web.seeother('/login')


class get_tma:
    def GET(self):
        '''Mengambil data Log terakhir dari masing-masing Pos
        Pos yang dipilih yang ada LatLonnya'''
        data = []
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        HIDE_THIS += [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = Agent.select(AND(Agent.q.AgentType != 3,
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "cname"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        for agent in agents:
            if agent.get_tma():
                data.append(agent.get_tma())
        web.header('Content-Type', 'application/json')
        return json.dumps(data)


class get_tmb:
    def GET(self):
        '''Mengambil data Log terakhir dari masing-masing Pos
        Pos yang dipilih yang ada LatLonnya'''
        data = []
        for agent in Agent.select(Agent.q.AgentType == 3):
            if agent.get_tma():
                data.append(agent.get_tma())
        web.header('Content-Type', 'application/json')
        return json.dumps(data)


class index:
    def GET(self):
        return render.index()
        # return map_render.map_tma(news)


def is_test():
    if 'WEBPY_ENV' in os.environ:
        return os.environ['WEBPY_ENV'] == 'test'

if (not is_test()) and __name__ == "__main__":
    app.run()
