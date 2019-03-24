"""
    tma.py
    Aplikasi tentang Tinggi Muka Air

    @author: Widoyo
    @date: 17 Des 2015
"""
import datetime
from ftplib import FTP
import web

from sqlobject import AND, OR

from models import Agent, HIDROLOGI, WILAYAH, CAUSE_TABLE
from common_data import DEBIT_POS, FTP_HOST, CCTV_IMG_DIR
from common_data import CCTV_POS
from helper import Struct, to_date

urls = (
    '$', 'Index',
    '/(\W)', 'ShowByName',
    '/(\d+)', 'ShowTmaCh',
    '/(\d+)/ch', 'Show',
    '/debit', 'DebitList',
    '/add', 'Add',
    '/list', 'TAdmin'
)

app_tma = web.application(urls, locals())
session = web.session.Session(app_tma, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'table_name': None, 'err': None})

globals = {'session': session, 'eval': eval}
render = web.template.render('templates/', base='base', globals=globals)
render_plain = web.template.render('templates/', globals=globals)
render_anon = web.template.render('templates/', base='base_anon',
                                  globals=globals)
render_fluid = web.template.render('templates/', base='base_fluid',
                                   globals=globals)


class ShowByName:
    def GET(self, pos_name):
        poses = dict([(a.table_name, a.AgentId) for a in Agent.select()])
        pos_id = poses.get(pos_name, None)
        if pos_id:
            return Show().GET(pos_id)
        else:
            return web.notfound()


class DebitList:
    def GET(self):
        try:
            tanggal = to_date(web.input().get('d'))
        except:
            tanggal = datetime.date.today()
        AGENT_TABLE = dict([a.strip().split('\t') for a in
            open('agent_table.txt').readlines()])
        poses = []
        db = Agent._connection
        for a in DEBIT_POS.keys():
            pos = Agent.get(int(AGENT_TABLE.get(a)))
            if pos.lengkung_kapasitas:
                pos.lengkung_series = [map(float, s.strip().split('\t')) for s in pos.lengkung_kapasitas.split('\n')]
            formula = DEBIT_POS.get(a)
            if formula:
                pos.debit_formula = formula
            sql = "SELECT CONCAT(SamplingDate, ' ', SamplingTime), WLevel*0.01 AS WLevel FROM %s ORDER BY SamplingDate DESC, SamplingTime DESC LIMIT 0, 1" % (a,)
            rst = db.queryAll(sql)
            try:
                tma = float(rst[0][1])
                pos.tma = {'tanggal': datetime.datetime.strptime(rst[0][0], '%Y-%m-%d %H:%M:%S'), 'tma': tma}
                debit = formula.get('a') * (tma - formula.get('b')) ** formula.get('c')
                pos.debit = debit
            except:
                pos.tma = {'tanggal': None, 'tma': None}
                pos.debit = None

            poses.append(pos)

        return render.tma.lengkung_debit({'poses': poses, 'tanggal': tanggal})


class Add:
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "cname"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        tgl = datetime.date.today()
        return render.tma.addt(agents, tgl)

    def POST(self):
        pos = web.input().get('pos')
        samplingdate = web.input().get('samplingdate')
        samplingtime = web.input().get('samplingtime')
        wlevel = web.input().get('wlevel')
        self.store(pos, samplingdate, samplingtime, wlevel)
        return web.seeother('/tma/list', absolute=True)

    def is_in(self, table_name, tanggal, jam):
        '''Cek apakah data telah tersimpan'''
        sql = "SELECT wlevel FROM %(table_name)s \
            WHERE \
              ReceivedTime='00:00:00' AND SamplingDate='%(tanggal)s' AND \
              SamplingTime='%(jam)s'"
        rst = Agent._connection.queryAll(sql % {'table_name': table_name,
                                                'tanggal': tanggal,
                                                'jam': jam})
        return rst

    def store(self, table_name, tanggal, jam, nilai):
        '''
        Menyimpan
        '''
        jam = jam + ':00:00'
        if self.is_in(table_name, tanggal, jam):
            sql = "UPDATE %(table_name)s SET WLevel=%(wlevel)s \
                WHERE \
                  ReceivedTime='00:00:00' AND SamplingDate='%(samplingdate)s' \
                  AND SamplingTime='%(samplingtime)s'"
        else:
            sql = "INSERT INTO %(table_name)s (SamplingDate, SamplingTime, WLevel) \
                  VALUES ('%(samplingdate)s', '%(samplingtime)s', %(wlevel)s)"

        Agent._connection.queryAll(sql % dict(table_name=table_name,
                                              samplingdate=tanggal,
                                              samplingtime=jam,
                                              wlevel=nilai))
        return True


class TAdmin:
    def GET(self):
        '''List data manually added'''
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "cname"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        sql = "SELECT SamplingDate, SamplingTime, WLevel FROM %(table_name)s \
            WHERE \
              ReceivedTime='00:00:00' \
              AND SamplingDate > '2017-04-16' \
            ORDER BY \
              SamplingDate DESC, SamplingTime DESC"
        tmas = []
        for a in agents:
            rst = a._connection.queryAll(sql % {'table_name': a.table_name})
            for row in rst:
                tmas.append((a,) + row)
        return render.tma.tlist(tmas)

    def POST(self, oid):
        '''Delete record with selected oid'''
        return True


class Show:
    def GET(self, pid):
        try:
            pos = Agent.get(pid)
        except SQLObjectNotFound:
            return web.notfound()
        hingga = datetime.datetime.now()
        dari = hingga - datetime.timedelta(days=3)
        tma_trend = pos.get_log_tma(dari, hingga)
        series = [(str(a[0]), str(a[1]), float(a[2] or 0)*0.01) for a in tma_trend]
        return render.tma.show({'pos': pos, 'data': series})

def timedelta_total_seconds(timedelta):
    return (timedelta.microseconds + 0.0 +
            (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) /10 ** 6

class ShowTmaCh:
    '''Tampilkan Grafik TMA dan CH yang mempengaruhi'''
    def GET(self, pid):
        try:
            pos = Agent.get(pid)
        except SQLObjectNotFound:
            return web.notfound()
        pics = []
        if pos.table_name in CCTV_POS:
            # mendapatkan 3 nama file terakhir dari CCTV FTP Server
            try:
                ftp = FTP(FTP_HOST)
                ftp.login()
                ftp.cwd(CCTV_IMG_DIR + '/' + pos.table_name)
                nlst = ftp.nlst()
                pics = nlst[-3:]
            except:
                pics = ['Fail to Connect CCTV Server','Fail to Connect CCTV Server','Fail to Connect CCTV Server']
        try:
            dari = to_date(web.input().dari)
            dari = datetime.datetime.combine(dari, datetime.time(7, 0, 0))
            hingga = to_date(web.input().hingga)
            hingga = datetime.datetime.combine(hingga,
                                               datetime.datetime.now().time())
        except:
            hingga = datetime.datetime.now()
            dari = hingga - datetime.timedelta(days=3)
            dari = dari.replace(hour=7, minute=0, second=0)

        tma_trend = pos.get_log_tma(dari, hingga)

        # membuat pola waktu per jam
        ch_patt = []
        t = int(dari.strftime('%s'))
        thingga = int(hingga.strftime('%s'))
        while t <= thingga:
            ch_patt.append([t, 0])
            t += 60 * 60  # 60 * 60 = 60 menit/1 jam
        ch_patt = dict(ch_patt)
        series = [[a[0], a[1], float(a[2] or 0)*0.01] for a in tma_trend]
        print len(ch_patt), len(series)
        data_series = [{'nama': pos.cname,
                        'series': series,
                        'satuan': 'M'}]
        # menghitung Debit
        if pos.table_name in DEBIT_POS.keys():
            formula = DEBIT_POS.get(pos.table_name)
            if formula:
                series = [] # series of debit
                for tgl, jam, tma in data_series[0].get('series'):
                    tma_lokal = tma - pos.DPL
                    if tma_lokal - formula.get('b') > 0:
                        deb = formula.get('a') * (tma_lokal - formula.get('b')) ** formula.get('c')
                    else:
                        deb = 0
                    #dt = datetime.datetime.combine(tgl, datetime.time(0)) + jam - datetime.timedelta(hours=7)

                    _d = {'sampling': int(tgl.strftime('%s')) + jam.seconds,
                            'tma': tma, 'debit': deb}
                    series.append('{x: %(sampling)s, y: %(tma)s, debit: %(debit)s}' % _d)
                data_series[0]['series'] = '[' + ','.join(series) + ']'
        else:
            series = []
            for tgl, jam, tma in data_series[0].get('series'):
                #dt = datetime.datetime.combine(tgl, datetime.time(0)) + jam - datetime.timedelta(hours=7)
                #epoch = datetime.datetime.utcfromtimestamp(0)

                #_d = {'sampling': timedelta_total_seconds((dt - epoch)),
                #        'tma': tma}
                _d = {'sampling': int(tgl.strftime('%s')) + jam.seconds,
                        'tma': tma}
                series.append('{x: %(sampling)s, y: %(tma)s}' % _d)
            data_series[0]['series'] = '[' + ','.join(series) + ']'

        # mencari data CH
        data_ch = {'nama': '', 'series': [], 'satuan': 'mm'}
        if pos.table_name in CAUSE_TABLE.keys():
            ch_list = CAUSE_TABLE.get(pos.table_name)
            AGENT_TABLE = dict([(a.table_name, a.AgentId) for a in Agent.select(OR(Agent.q.AgentType == 0, Agent.q.AgentType == 1, Agent.q.AgentType == 2))])
            for ch in ch_list:
                print 'CH', ch
                pos_ch = Agent.get(AGENT_TABLE.get(ch))
                ch_trend = pos_ch.get_log(dari, hingga, False)
                series = [(int(a[0].strftime('%s')) + a[1].seconds, float(a[2] or 0)) for a in ch_trend]
                for s in series:
                    nilai = ch_patt.get(s[0])
                    if not nilai:
                        ch_patt[s[0]] = s[1]
                    else:
                        ch_patt[s[0]] = nilai > s[1] and nilai or s[1]
                _t = {'nama': pos_ch.cname,
                      'series': series}
                #print ch, _t['series']
                if not _t.get('series'):
                    _t['series'] = []
                data_ch['nama'] += ', ' + pos_ch.cname
            data_ch['series'] = '[' + ','.join(['{x: %s, y: %s}' %(k, v) for k, v in ch_patt.items()]) + ']'
        data_series.append(data_ch)
#        print len(data_series[0]['series'])

        return render.tma.show_tma_ch({'pos': pos, 'data': data_series,
                                'dari': dari, 'hingga': hingga,
                                'pics': pics})


class Index:
    def GET(self):
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            try:
                tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except:
                tanggal = datetime.datetime.strptime(tanggal, "%d %b %y").date()
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "urutan"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        data = [Struct(**{'pos': a,
                          'tma': Struct(**a.get_segmented_wl(tanggal))}) for a
                in agents]
        js = """
        <script type="text/javascript">
        $(function(){
            $('.tanggal').datepicker({dateFormat: 'd M y'});
            $('.show-current-date').bind('change', function () {
             $(this).parent().submit()});
        });
        </script>"""
        sebelum = tanggal - datetime.timedelta(days=1)
        sesudah = tanggal + datetime.timedelta(days=1)
        if web.ctx.env.get('HTTP_X_PJAX') is not None:
            return render_plain.tma.index_table(
                tma=data, meta={'now': tanggal.strftime('%d %b %y'),
                                'before': sebelum.strftime('%d %b %y'),
                                'after': sesudah.strftime('%d %b %y')},
                wilayah=WILAYAH)

        return render.tma.index(
            tma=data, meta={'now': tanggal.strftime('%d %b %y'),
                            'before': sebelum.strftime('%d %b %y'),
                            'after': sesudah.strftime('%d %b %y')},
            wilayah=WILAYAH, js=js)

if __name__ == '__main__':
    pass
