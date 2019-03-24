"""
    kualitas_air.py
    Aplikasi Kualitas Air

    @author: Widoyo
    @date: 05 Mei 2017
"""
import datetime
import web

from models import Agent


urls = (
    '$', 'Index',
    '/(\d+)', 'Show',
    '/(\W)', 'ShowByName'
)

app_kualitas_air = web.application(urls, locals())
session = web.session.Session(app_kualitas_air, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Show:
    def GET(self, pid):
        sql = "SELECT k.*, l.id, l.cname, l.ll FROM kualitas_air k, lokasi l WHERE \
                l.id=k.id_pos AND l.id=%d \
                ORDER BY k.waktu" % (int(pid))
        rst = Agent._connection.queryAll(sql)
        if rst:
            pos = (rst[0][-3], rst[0][-2])
            data = [r[:-4] for r in rst]
        return render.kualitas_air.show({'data': data, 'pos': pos})


class ShowByName:
    def GET(self, pos_name):
        pos_name = pos_name.lower()
        return pos_name


class Index:
    def GET(self):
        tahun = ''
        conn = Agent._connection
        sql = "SELECT YEAR(MAX(waktu)) FROM kualitas_air"
        rst = conn.queryAll(sql)
        if not rst:
            return "Tidak ada data Kualitas Air"
        sql = "SELECT k.waktu, k.ip, l.id, l.cname, l.ll \
                FROM kualitas_air k, lokasi l \
                WHERE k.id_pos=l.id AND YEAR(k.waktu)=%s \
                ORDER BY l.id, k.waktu" % rst[0][0]
        rst = conn.queryAll(sql)
        rows = []
        row = {}
        pos = 0
        poses = {}
        waktu = datetime.date.today()
        for d in rst:
            if pos != d[2]:
                if row:
                    rows.append((d[2], d[3], dict([r for r in row.get(pos)])))
                    row = {}
                pos = d[2]
                poses[pos] = dict(cname=d[3], id=pos)
                row[pos] = [(d[0].strftime('%m'), d[1])]
                continue
            row[pos].append((d[0].strftime('%m'), d[1]))
            waktu = d[0]
        return render.kualitas_air.index({'data': rows, 'poses': poses, 'waktu': waktu})
