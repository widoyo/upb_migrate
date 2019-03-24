"""
    curahhujan.pt
    Aplikasi tentang Curah Hujan

    @author: Widoyo
    @date: 25 Nop 2015
"""
from memory_profiler import profile
import datetime
import calendar
import web

from sqlobject import AND, OR, SQLObjectNotFound

from models import AgentCh, KLIMATOLOGI, WILAYAH, conn

from helper import Struct, to_date

urls = (
    '$', 'Index',  # Tampilkan daftar pos
    '/(\d+)', 'Jamjaman',  # (pos_id) Tampilkan satu pos jam-jaman
    '/(\d+)/bulanan', 'Index',  # (pos_id) Tampilkan satu pos jan-des bbrp tahun, (Tahunan)
    '/(\d+)/(\d+)', 'Index',  # (pos_id/th) Tampilkan satu pos, tahun terpilih
    '/(\d+)/(\d+)/(\d+)', 'Index', # (pos_id/th/bl) Tampilkan hujan per hari dalam tahun/bulan
    '/(\d+)/daily', 'Daily',
    '/(\d+)/tertinggi', 'CurahHujanTertinggi', # (pos_id/tertingi/th) Chart curah hujan tertinggi pos per tahun
    '/wilayah/rerata', 'WilayahRerata',
    '/data', 'ExploreData'

)

app_ch = web.application(urls, locals())
session = web.session.Session(app_ch, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'table_name': None, 'err': None})
globals = {'session': session, 'eval': eval, 'now': datetime.date.today()}
render = web.template.render('templates/', base='base', globals=globals)
render_plain = web.template.render('templates/', globals=globals)
render_anon = web.template.render('templates/', base='base_anon',
                                  globals=globals)
render_fluid = web.template.render('templates/', base='base_fluid',
                                   globals=globals)


class Jamjaman:
    @profile
    def GET(self, pid):
        try:
            pos = AgentCh.get(pid)
        except SQLObjectNotFound:
            return web.notfound()
        now = datetime.datetime.now()
        try:
            tanggal = to_date(web.input().get('d'))
        except:
            tanggal = datetime.date.today()
            if now.hour < 9:
                tanggal = tanggal - datetime.timedelta(days=1)
        ch_per_jam = pos.get_aday_ch(tanggal)
        sebelum = tanggal - datetime.timedelta(days=1)
        if tanggal == datetime.date.today():
            sesudah = None
        else:
            sesudah = tanggal + datetime.timedelta(days=1)
        start = datetime.datetime.combine(tanggal, now.time().replace(hour=7, minute=0))

        labels = [(start + datetime.timedelta(hours=h)).hour for h in range(24)]
        ch_set = []
        ch_ = dict([(c[0].hour, c[1]) for c in ch_per_jam])
        for l in labels:
            ch_set.append((l, float(ch_.get(l, 0) or '0')))
        return render.curahhujan.jamjaman({'pos': pos, 'tanggal': tanggal,
            'sebelum': sebelum, 'sesudah': sesudah,
            'data': {'categories': labels, 'series': ch_set}})


class ExploreData:
    def GET(self):
        return web.template.frender('templates/curahhujan/vs_generated.html')()

    def generate_vs(self):
        poses = AgentCh.select(OR(AgentCh.q.AgentType==0, AgentCh.q.AgentType==1))
        num_hari = 7
        start = datetime.date.today() - datetime.timedelta(days=num_hari)
        dates = []
        i = start
        while i < datetime.date.today():
            dates.append(i)
            i += datetime.timedelta(days=1)
        ret = {}
        for p in poses:
            i = start
            pos_data = []
            ret[p] = {'pos': p, 'data_hujan': pos_data}
            while i < datetime.date.today():
                pos_data.append(p.get_segmented_rain(i))
                i += datetime.timedelta(days=1)
        with open('templates/curahhujan/vs_generated.html', 'w') as f:
            f.write(str(render.curahhujan.vs({'poses': ret, 'dates': dates})))


class CurahHujanTertinggi:
    def GET(self, pos_id):
        try:
            pos = AgentCh.get(int(pos_id))
        except SQLObjectNotFound:
            return web.notfound()
        dari = datetime.date.today().year
        hingga = datetime.date.today().year - 1
        sql = "SELECT waktu, MAX(manual) \
                FROM curahhujan \
                WHERE agent_id=%s \
                GROUP BY YEAR(waktu), \
                MONTH(waktu) \
                ORDER BY waktu ASC" % (pos_id, )
        data = {}
        tahun = 0
        for d in AgentCh._connection.queryAll(sql):
            if d[0]:
                if tahun != d[0].year:
                    _year_data = []
                    data[d[0].year] = _year_data
                    tahun = d[0].year
                _year_data.append((d[0].month, d[1] or 0))

        data = [(k, v) for k, v in data.items()]
        data.sort()

        return render.curahhujan.tertinggi({'pos': pos, 'data': data})


class WilayahRerata:
    def GET(self):
        dari = 2015
        hingga = datetime.date.today().year - 1
        poses = [(a.AgentId, a.cname, a.wilayah) for a in AgentCh.select(OR(AgentCh.q.AgentType==0, AgentCh.q.AgentType==1)).orderBy('wilayah, cname')]
        return render.curahhujan.wilayah_rerata(poses)


class Daily:
    def GET(self, pos_id):
        try:
            pos = AgentCh.get(int(pos_id))
        except SQLObjectNotFound:
            return web.notfound()
        web_input = web.input()
        periode = web_input.get('p', 10)
        year = int(web_input.get('year', datetime.date.today().year))
        sql = "SELECT waktu, manual FROM curahhujan \
                WHERE agent_id=%s AND YEAR(waktu)=%s ORDER BY waktu" % (pos_id, year)
        setahun = [] # 10 harian
        bulan = 0
        bln_ = [0, 0, 0]
        for r in conn.queryAll(sql):
            if r[0].month != bulan:
                if bulan:
                    setahun.append((bulan, bln_))
                bln_ = [0, 0, 0]
                bulan = r[0].month
            if r[0].day < 10:
                bln_[0] += r[1]
            elif r[0].day < 21:
                bln_[1] += r[1]
            else:
                bln_[2] += r[1]
        setahun.append((bulan, bln_))

        setahun = dict(setahun)
        series = [setahun.get(b, [0, 0, 0]) for b in range(1, 13)]
        s = []
        d = []
        t = []
        for data in series:
            s.append(data[0])
            d.append(data[1])
            t.append(data[2])

        data = {'periode': periode, 'year': year, 'pos': pos, 'series': (s, d, t)}
        template = (periode == 10) and render.curahhujan.daily10 \
                or render.curahhujan.daily15
        return template(data)


class Human:
    def GET(self, tahun=None, bulan=None):
        skr = datetime.date.today()
        data = []
        try:
            tahun = int(tahun)
        except:
            tahun = skr.year

        try:
            bulan = int(bulan)
        except:
            bulan = skr.month
        (a, z) = calendar.monthrange(tahun, bulan)
        next_month = datetime.date(tahun, bulan, z) + datetime.timedelta(days=1)
        prev_month = datetime.date(tahun, bulan, 1) - datetime.timedelta(days=2)

        tdata = dict([(i, dict(telemetri=None, total=None, manual=None))
                      for i in range(0, z)])
        for a in AgentCh.select(AND(OR(AgentCh.q.AgentType == KLIMATOLOGI,
                                     AgentCh.q.AgentType == 0),
                                  AgentCh.q.expose == True)).orderBy(
                                      ["wilayah", "cname"]):
            sql = "SELECT DAY(waktu), pagi+sore+malam AS telemetri, total, manual \
                FROM curahhujan WHERE agent_id=%s AND \
                YEAR(waktu)=%s AND MONTH(waktu)=%s" % (a.AgentId, tahun, bulan)
            rst = AgentCh._connection.queryAll(sql)
            tdata.update(dict([(r[0], Struct(**dict(telemetri=r[1], total=r[2],
                                                    manual=r[3])))
                               for r in rst]))
            data.append(Struct(**dict(AgentName=a.AgentName, wilayah=a.wilayah,
                        data=tdata)))
        ctx = dict(curr_month=datetime.date(tahun, bulan, 1), data=data,
                   wilayah=WILAYAH, numdays=z+1, prev_month=prev_month,
                   next_month=next_month)
        return render_fluid.curahhujan.human.index(ctx)


class Index:
    '''
    Untuk menampilkan informasi Curah Hujan
    '''
    @profile
    def GET(self, pos_id='', tahun='', bulan=''):
        if not pos_id:
            tanggal = web.input().get('d')
            paper = web.input().get('paper', False)
            return self.curah_hujan_home(tanggal, paper)
        else:
            try:
                tahun = int(tahun)
            except:
                tahun = datetime.date.today().year
            return self.curah_hujan_pos(pos_id, tahun, bulan)

    @profile
    def curah_hujan_home(self, tanggal=None, paper=False):
        if not tanggal:
            tanggal = datetime.date.today() - datetime.timedelta(days=1)
        else:
            try:
                tanggal = to_date(tanggal)
            except:
                tanggal = to_date(tanggal)
        HIDE_THIS = [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = AgentCh.select(AND(OR(AgentCh.q.AgentType == KLIMATOLOGI, AgentCh.q.AgentType == 0.0), AgentCh.q.expose == True)).orderBy(('wilayah', 'urutan', ))
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        data = [{'pos': a, 'ch': a.get_segmented_rain(tanggal)} for a in agents]
        sebelum = tanggal - datetime.timedelta(days=1)
        sesudah = tanggal + datetime.timedelta(days=1)
        template_render = render.curahhujan.harian_all
        if paper:
            template_render = render_plain.curahhujan.harian_paper
        return template_render(
            curah_hujan=data,
            meta={'now': tanggal,
                  'before': sebelum,
                  'after': sesudah},
            wilayah=WILAYAH)

    @profile
    def curah_hujan_pos(self, pos_id, tahun=datetime.date.today().year,
                        bulan=''):
        '''
        Jika bulan valid, otomatis tahun juga valid,
          tampilkan curah hujan setiap hari pada bulan terpilih
          sumbu mendatar berisi tanggal
        Jika tahun valid, bulan kosong, tampilkan curah hujan 3 tahun lalu,
          dari tahun terpilih, sumbu mendatar berisi bulan-bulan
        '''
        try:
            agent = AgentCh.get(pos_id)
        except SQLObjectNotFound:
            return web.notfound()
        if agent.AgentType not in (1.0, 0.0):
            return web.notfound()
        ch = agent.get_ch(tahun, bulan)
        data = []
        for a in ch:
            try:
                data.append((a[0], a[2] or 0))
            except:
                data.append((a[0], 0))
        series = {}
        to_render = render.curahhujan.bulanan
        if bulan:
            # hujan per hari pada 'bulan'
            series = [0 for r in range(
                calendar.monthrange(tahun, int(bulan))[1])]
            sql = "SELECT waktu, manual, pagi, sore, malam, tmalam FROM curahhujan \
                    WHERE agent_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s" % (pos_id, tahun, bulan)

            for d in conn.queryAll(sql):
                series[d[0].day-1] = d[1]
            data = Struct(**{'series': series, 'categories': [s+1 for s in range(len(series))],'bulan': datetime.date(tahun, int(bulan), 1)})
            to_render = render.curahhujan.harian
        elif data:
            print data
            # hujan per bulan pada 'tahun'
            th = data[0][0].year
            series[th] = [0 for r in range(0, 12)]
            for d in data:
                if d[0].year != th:
                    th = d[0].year
                    series[th] = [0 for r in range(0, 12)]
                    series[th][d[0].month-1] = d[1]
                else:
                    series[th][d[0].month-1] = d[1]
            data = [Struct(**{'tahun': k, 'series': v})
                    for k, v in sorted(series.items())]
        ctx = {'pos': agent, 'data': data}
        return to_render(ctx)
