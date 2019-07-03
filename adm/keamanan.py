# Data Management
import os
import sys
import datetime
import calendar
import json

import web
from sqlobject import OR, AND, SQLObjectNotFound

from models import AgentBd, conn, WadukDaily,TinggiMukaAir, BendungAlert
from models import NO_VNOTCH, FAIL_VNOTCH, FOTO_PATH
from models import Kegiatan, Foto

from helper import to_date, json_serializer

urls = (
    '/', 'Index',
)


app_keamanan = web.application(urls, locals())
session = web.session.Session(app_keamanan, web.session.DiskStore('sessions'),
        initializer={'username': None, 'is_admin': None,
            'table_name': None, 'err': None})

def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session['csrf_token'] = uuid4().hex
    return session.get('csrf_token')


globals = {'session': session, 'csrf_token': csrf_token}
render = web.template.render('templates/', base='base_adm', globals=globals)


def csrf_protected(func):
    def decorated(*args, **kwargs):
        inp = web.input()
        print 'CSRF_TOKEN', inp.csrf_token
        print 'SESSION_CSRF_TOKEN', session.get('csrf_token')
        if not (inp.has_key('csrf_token') and inp.csrf_token==session.pop('csrf_token', None)):
            raise web.HTTPError(
                    '400 Bad Request',
                    {'content-type': 'text/html'},
                    """Cross-site request forgery (CSRF) attempt (or stale browser form, <a href='#'>Kembali</a>""")
        return func(*args, **kwargs)
    return decorated



def login_required(func):
    def func_wrapper(*args, **kwargs):
        if not session.get('username'):
            raise web.seeother('/login', absolute=True)
        return func(*args, **kwargs)
    return func_wrapper


def admin_required(func):
    def func_wrapper(*args, **kwargs):
        if session.get('table_name'):
            raise web.forbidden()
        return func(*args, **kwargs)
    return func_wrapper


class Index:
    def GET(self):
        return 'Hello'


class BdKeamananIndex:
    @login_required
    def GET(self):
        print 'Keamanan Index'
        inp = web.input()
        if inp.get('sampling'):
            sampling = to_date(inp.sampling)
        else:
            sampling = datetime.date.today()
        tanggal = sampling
        bdgs = AgentBd.select(AgentBd.q.AgentType==3).orderBy('wilayah')
        poses = dict([(a.table_name, a) for a in bdgs])
        daily_bd = dict([(w.pos.table_name, w) for w in WadukDaily.select(WadukDaily.q.waktu==tanggal)])
        poses = [(poses.get(p), daily_bd.get(p)) for p in [p.table_name for p in bdgs]]
        return render.adm.bendungan.index({'poses': poses, 'tanggal': tanggal})


class BdPeriodicAdd:
    @login_required
    def POST(self, tbl_name):
        wi = web.input()
        return render.adm.bendungan.add({'table_name': tbl_name})


class Dummy(object):
    pass

class Index:
    @login_required
    def GET(self):
        dest = 'adm_ch_tma_bendungan'.split('_')
        redirect_to  = '/adm'
        if session.table_name:
            direct_to = '/adm/' + dest[session.is_admin] + '/' + session.table_name
        elif session.is_admin in (1, 2, 3):
            direct_to = '/adm/' + dest[session.is_admin]
        elif session.is_admin == 9:
            return render.adm.index()
        return web.seeother(redirect_to, absolute=True)


if __name__ == "__main__":
    pass

