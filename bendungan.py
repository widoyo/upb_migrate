"""
    bendungan.py
    Aplikasi tentang Bendungan / Waduk

    @author: Widoyo
    @date: 08 Jan 2016
"""
import datetime
import web
from web.utils import commify

from sqlobject import SQLObjectNotFound, AND, OR

from models import Agent, WILAYAH, WadukDaily, NO_VNOTCH, FAIL_VNOTCH

from helper import Struct, to_date

urls = (
    '$', 'Index',
    '/summary$', 'Summary',
    '/(\d+)', 'Elevasi',  # TMA Satu Pos pd Hari ini
    '/(\d+)/tma', 'ShowTma',  # Trend TMA Satu Pos
    '/(\d+)/(\d+)/(\d+)/(\d+)', 'Show',  # TMA Satu Pos hari terpilih
    '/(\d+)/(\d+)/(\d+)', 'Show',  # TMA satu pos bulan terpilih
    '/(\d+)/operasi', 'Operasi',  # Show Chart Operasi Bendungan
    '/(\w+\.*\-*\w+)/vnotch', 'Vnotch',  # Show table VNotch Bendungan
    '/(\w+\.*\-*\w+)/piezometer', 'Piezometer',  # Show table Piezometer Bendungan
    #'/(\d+)/keamanan', 'Keamanan',  # Show Chart Keamanan (piezometer) Bendungan
    '/(\d+)/piezometerr', 'piezometer_vnotch',
    '/(\d+)/vnotchh', 'vnotch_piezometer',
    '/(\d+)/pemantauan', 'Pemantauan',  # Show Pemantauan Bendungan
    '/primabot/(\d+-\d+)', 'ShowPrimabot'
)

KONDISI_BENDUNGAN = ("Normal", 'Defisit', 'Kering')

app_bendungan = web.application(urls, locals())
session = web.session.Session(app_bendungan, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'table_name': None, 'err': None})

globals = {'session': session, 'eval': eval, 'commify': commify}
render = web.template.render('templates/', base='base', globals=globals)
render_plain = web.template.render('templates/', globals=globals)
render_anon = web.template.render('templates/',
                                  base='base_anon', globals=globals)


class Vnotch:
    def GET(self, bd):

        if bd[3:] in NO_VNOTCH:
            return render.bendungan.vnotch_fail({'bd': bd, 'no_vnotch': True})
        if bd[3:] in FAIL_VNOTCH:
            return render.bendungan.vnotch_fail({'bd': bd, 'fail_vnotch': True})
        inp = web.input()
        sampling = inp.get('sampling')
        sampling = sampling and to_date(sampling) or datetime.date.today()

        pos = [a for a in Agent.select(Agent.q.AgentType==3) if a.table_name == bd][0]
        if sampling.month == datetime.date.today().month:
            wds = [wd for wd in WadukDaily.select(WadukDaily.q.pos==pos).orderBy('waktu') if wd.waktu.year == sampling.year and wd.waktu.month == sampling.month]
        else:
            wds = [wd for wd in WadukDaily.select(WadukDaily.q.pos==pos) if wd.waktu.year == sampling.year and wd.waktu.month == sampling.month and wd.waktu.day <= datetime.date.today().day]

        return render.bendungan.vnotch({'pos': pos, 'bulan': sampling, 'wds': wds})


class Piezometer:
    def GET(self, bd):
        '''Tampilkan data Piezometer untuk lokasi "bd"
        Default tampilkan data terakhir, kecuali ada sampling yang diinginkan
        Menampilkan data selama _bulan_terpilih_
        '''
        inp = web.input()
        sampling = inp.get('sampling', None)
        bendungans= dict([a.strip().split() for a in open('agent_table.txt').readlines()])
        id_bdg = bendungans.get(bd)
        if not id_bdg:
            return web.notfound()
        sql = "SELECT MAX(waktu) FROM waduk_daily WHERE pos_id=%s" % id_bdg
        rst = Agent._connection.queryAll(sql)
        if not sampling:
            sampling = rst[0]

        sampling = sampling and to_date(sampling) or None

        pos = Agent.get(id_bdg)

        if sampling.month == datetime.date.today().month:
            wds = [wd for wd in WadukDaily.select(WadukDaily.q.pos==pos).orderBy('-waktu') if wd.waktu.year == sampling.year and wd.waktu.month == sampling.month]
        else:
            wds = [wd for wd in WadukDaily.select(WadukDaily.q.pos==pos) if wd.waktu.year == sampling.year and wd.waktu.month == sampling.month and wd.waktu.day <= datetime.date.today().day]

        return render.bendungan.piezometer({'pos': pos, 'bulan': sampling, 'wds': wds})


class Summary:
    def GET(self):
        '''Ringkasan seluruh bendungan hari ini'''
        bdgs = Agent.select(Agent.q.AgentType==3)
        nums = bdgs.count()
        ids = [b.AgentId for b in bdgs]
        today = datetime.date.today()
        # mengambil nilai ROTW (Rencana Operasi Tahunan Waduk)
        #
        sql = "SELECT SUM(po_outflow_q) AS po_outflow, \
                SUM(intake_q) AS outflow, SUM(inflow_q) AS inflow, \
                SUM(vol6) AS vol6, SUM(po_vol) AS po_vol, \
                SUM(po_inflow_q) AS po_inflow_q \
                FROM waduk_daily \
                WHERE waktu='%s'" % (today)
        # mengambil nilai ROTW (Rencana Operasi Tahunan Waduk)
        #
        jhar = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        waktu_rtow = today.replace(day=15)
        if today.day >= 16:
            waktu_rtow = today.replace(day=jhar[today.month - 1])
        sql2 = "SELECT SUM(po_outflow_q) AS po_outflow, \
                SUM(po_vol) AS po_vol, \
                SUM(po_inflow_q) AS po_inflow_q \
                FROM waduk_daily \
                WHERE waktu = '%s'" % (waktu_rtow)
        rst = Agent._connection.queryAll(sql)
        rst2 = Agent._connection.queryAll(sql2)
        rec = rst[0]
        rec2 = rst2[0]
        real_vol = rec[3] and commify('%d' % (rec[3])) or '-'
        rotw_vol = rec2[1] and commify('%d' % (rec2[1])) or '-'
        rotw_inflow_q = rec2[2] and commify('%d' % (rec2[2])) or '-'
        real_inflow_q = rec[2] and commify('%d' % (rec[2])) or '-'
        # total kapasitas volume waduk
        tot_vol = commify(int(sum([b.volume for b in bdgs])))
        # total luas baku irigasi
        tot_lbi = sum([b.lbi for b in bdgs])
        all_pos = [{'id': a.AgentId, 'name': a.cname, 'll': a.ll} for a in bdgs]
        js_foot = """
        """
        return render.bendungan.summary({'nums': nums,
            't_vol': tot_vol, 'today': today, 'r_vol': real_vol,
            'rotw_vol': rotw_vol, 'po_outflow_q': rec2[0], 'outflow_q': rec[1],
            'po_inflow_q': rotw_inflow_q, 'inflow_q': real_inflow_q,
            't_lbi': tot_lbi, 'js_foot': js_foot})


class ShowPrimabot:
    def GET(self, pid):
        try:
            oid = Agent.select(Agent.q.prima_id == pid)[0].AgentId
            bd = Agent.get(oid)
            if bd.AgentType != 3:
                raise web.notfound(404)
        except:
            raise web.notfound(404)
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            tanggal = to_date(tanggal)
        try:
            bendungan = Agent.get(int(oid))
            if bendungan.AgentType != 3:
                raise SQLObjectNotFound
        except SQLObjectNotFound:
            return web.notfound(404)
        sql = "SELECT SamplingDate, SamplingTime, WLevel, Temperature, Humidity, Rain4 FROM %(table_name)s \
                ORDER BY SamplingDate DESC, SamplingTime DESC \
                LIMIT 0, 25" % ({'table_name': bendungan.table_name})
        rst = [(int(r[0].strftime('%s'))+r[1].seconds, r[2], r[3], r[4], r[5]) for r in bendungan._connection.queryAll(sql)]
        latest = {}
        if not rst:
            sql = "SELECT SamplingDate, SamplingTime, WLevel, Temperature, Humidity, Rain4 FROM %(table_name)s \
                ORDER BY SamplingDate, SamplingTime LIMIT 0, 25" % ({'table_name': bendungan.table_name})
            rst = [(int(r[0].strftime('%s'))+r[1].seconds, r[2], r[3], r[4], r[5]) for r in bendungan._connection.queryAll(sql)]
        d = rst[0]
        samp = datetime.datetime.fromtimestamp(d[0])
        if samp.date() == datetime.date.today():
            sampling = samp.strftime('%H:%M')
        else:
            sampling = samp.strftime('%d %b %H:%M')
        latest = dict(sampling=sampling, wlevel=d[1]/100.0, temperature=d[2], humidity=d[3], sq=d[4])
        return render.bendungan.liveprima(
            bendungan,
            meta={'now': tanggal.strftime('%d %b %y'),
                  'tma': rst,
                  'latest_sampling': latest
                  })


class ShowTma:
    '''Tampilkan Grafik TMA dan Data Env (Prima)'''
    def GET(self, pid):
        try:
            pos = Agent.get(pid)
        except SQLObjectNotFound:
            return web.notfound()
        try:
            dari = to_date(web.input().dari)
            dari = datetime.datetime.combine(dari, datetime.time(7, 0, 0))
            hingga = to_date(web.input().hingga)
            hingga = datetime.datetime.combine(hingga,
                                               datetime.datetime.now().time())
        except:
            hingga = datetime.datetime.now()
            dari = hingga - datetime.timedelta(days=2)
            dari = dari.replace(hour=7, minute=0, second=0)
        #print dari, hingga
        tma_trend = pos.get_log_tma(dari, hingga)

        series = ['{x: %s, y: %s}' % (int(a[0].strftime('%s')) + a[1].seconds, float(a[2] or 0)*0.01) for a in tma_trend]
        data_series = [{'nama': pos.cname,
                        'series': ', '.join(series),
                        'satuan': 'M'}]

        return render.bendungan.show_tma({'pos': pos, 'data': data_series,
                                'dari': dari, 'hingga': hingga})


class Keamanan:
    def GET(self, oid):
        bendung = Agent.get(int(oid))
        meta = {"dari": datetime.date(2017, 1, 1),
                "hingga": datetime.date(2017, 3, 1)}
        return render.bendungan.keamanan.index(bendung, meta)


class Pemantauan:
    def GET(self, oid):
        try:
            bendung = Agent.get(int(oid))
        except SQLObjectNotFound:
            return web.notfound()
        dari = datetime.date(2017, 3, 1)
        hingga = datetime.date(2017, 3, 31)
        meta = {"dari": dari,
                "hingga": hingga,
                "daily": WadukDaily.select(AND(
                    WadukDaily.q.pos == bendung,
                    WadukDaily.q.waktu >= dari,
                    WadukDaily.q.waktu <= hingga))}
        return render.bendungan.pemantauan(bendung, meta)


class Operasi:
    def GET(self, oid):
        try:
            bendung = Agent.get(int(oid))
        except SQLObjectNotFound:
            return web.notfound()
        inp = web.input()
        if inp.get('periode'):
            periode = to_date(inp.periode)
        else:
            periode = datetime.date.today()
        if periode.month < 11:
            periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu
        else:
            periode = datetime.date(periode.year, 11, 1)
        
        tanggal = periode
        if periode.month > 10:
            tanggal = datetime.date(tanggal.year + 1, 11, 1)

        if tanggal.year <= 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=1))
                rr.append(periode.replace(day=16))
                periode += datetime.timedelta(days=jhar[i])
        if tanggal.year > 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=15))
                rr.append(periode.replace(day=jhar[i]))
                periode += datetime.timedelta(days=jhar[i])
        sql = "SELECT waktu, po_tma, po_inflow_q, po_inflow_v, \
                po_outflow_q, po_outflow_v, \
                tma6, vol6, inflow_q, inflow_v, intake_q, intake_v, po_bona, po_bonb, vol_bona, vol_bonb \
                FROM waduk_daily \
                WHERE waktu IN (%s) AND pos_id=%s \
                ORDER BY waktu" % (','.join(["'"+str(i)+"'" for i in rr]), oid)
        rst = Agent._connection.queryAll(sql)
        sql_realisasi = "SELECT \
                tma6, vol6, inflow_q, inflow_v, intake_q, intake_v \
                FROM waduk_daily \
                WHERE pos_id=%s AND waktu BETWEEN %s AND %s \
                ORDER BY waktu"
        meta = {'rst': rst, 'daily': [], 'dari': periode, 'hingga': periode, 'tanggal':tanggal}
        return render.bendungan.operasi(bendung, meta)

class piezometer_vnotch:
#    def GET(self, oid):
#        bendung = Agent.get(int(oid))
#        meta = {"dari": datetime.date(2017, 1, 1),
#                "hingga": datetime.date(2017, 3, 1)}
#        return render.bendungan.keamanan.index(bendung, meta)

    def GET(self, oid):
        try:
            bendung = Agent.get(int(oid))
        except SQLObjectNotFound:
            return web.notfound()


        inp = web.input()
        if inp.get('periode'):
            periode = to_date(inp.periode)
        else:
            periode = datetime.date.today()
        year = datetime.date.today().year
        if periode.month < 11 and periode.year == year:
            periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu
            year = datetime.date.today().year
            start = datetime.date(year=year -1, month=11, day=1)
        if periode.month > 10 and periode.year == year:
            periode = datetime.date(periode.year, 11, 1) # 1 Nop tahun lalu
            year = datetime.date.today().year + 1
            start = datetime.date(year=year - 1, month=11, day=1)
        if periode.month < 11 and periode.year > year:
            periode = datetime.date(periode.year -1, 11, 1)
            year =  datetime.date.today().year + 1
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month > 10 and periode.year > year:
            periode = datetime.date(periode.year, 11, 1)
            year =  datetime.date.today().year
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month < 11 and periode.year < year:
            periode = datetime.date(periode.year -1, 11, 1)
            year =  datetime.date.today().year + 1
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month > 10 and periode.year < year:
            periode = datetime.date(periode.year, 11, 1)
            year =  datetime.date.today().year
            start = datetime.date(year=year -1 , month=11, day=1)

        #print start
        oneday = datetime.timedelta(days=1)
        oneweek = datetime.timedelta(days=7)


        while start.weekday() != 0:
            start += oneday
        
        days = []
        while start.year <= year:
            days.append(start.strftime("%Y-%m-%d"))
            start += oneweek
            if start.month == 11 and start.year == year:
                break

        sql = "SELECT waktu, a1, b1, c1, a2, b2, c2, a3, b3, c3, a4, b4, c4, a5, b5, c5, vnotch_q1, vnotch_q2, vnotch_q3, vnotch_tin1, vnotch_tin2, vnotch_tin3 \
                FROM waduk_daily \
                WHERE waktu IN (%s) AND pos_id=%s \
                ORDER BY waktu" % (','.join(["'"+ str(i) +"'" for i in days]), oid)

        rst2 = Agent._connection.queryAll(sql)


        #periode = datetime.date.today()

#        if periode.month < 11:


        #periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu


#        else:
#            periode = datetime.date(periode.year, 11, 1)
        
        tanggal = periode
        if periode.month > 10:
            tanggal = datetime.date(tanggal.year + 1, 11, 1)

        if tanggal.year <= 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=1))
                rr.append(periode.replace(day=16))
                periode += datetime.timedelta(days=jhar[i])
        if tanggal.year > 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=15))
                rr.append(periode.replace(day=jhar[i]))
                periode += datetime.timedelta(days=jhar[i])

        sql = "SELECT waktu, po_tma, po_inflow_q, po_inflow_v, \
                po_outflow_q, po_outflow_v, \
                tma6, vol6, inflow_q, inflow_v, intake_q, intake_v, po_bona, po_bonb, vol_bona, vol_bonb \
                FROM waduk_daily \
                WHERE waktu IN (%s) AND pos_id=%s \
                ORDER BY waktu" % (','.join(["'"+str(i)+"'" for i in rr]), oid)

        rst1 = Agent._connection.queryAll(sql)

        meta = {'rst1': rst1, 'rst2': rst2, 'dari': periode, 'hingga': periode, 'tanggal':tanggal }
        return render.bendungan.keamanan.piezometerr(bendung, meta)

class vnotch_piezometer:
    def GET(self, oid):
        try:
            bendung = Agent.get(int(oid))
        except SQLObjectNotFound:
            return web.notfound()



        inp = web.input()
        if inp.get('periode'):
            periode = to_date(inp.periode)
        else:
            periode = datetime.date.today()
        year = datetime.date.today().year
        if periode.month < 11 and periode.year == year:
            periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu
            year = datetime.date.today().year
            start = datetime.date(year=year -1, month=11, day=1)
        if periode.month > 10 and periode.year == year:
            periode = datetime.date(periode.year, 11, 1) # 1 Nop tahun lalu
            year = datetime.date.today().year + 1
            start = datetime.date(year=year - 1, month=11, day=1)
        if periode.month < 11 and periode.year > year:
            periode = datetime.date(periode.year -1, 11, 1)
            year =  datetime.date.today().year + 1
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month > 10 and periode.year > year:
            periode = datetime.date(periode.year, 11, 1)
            year =  datetime.date.today().year
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month < 11 and periode.year < year:
            periode = datetime.date(periode.year -1, 11, 1)
            year =  datetime.date.today().year + 1
            start = datetime.date(year=year -1 , month=11, day=1)
        if periode.month > 10 and periode.year < year:
            periode = datetime.date(periode.year, 11, 1)
            year =  datetime.date.today().year
            start = datetime.date(year=year -1 , month=11, day=1)

        #print start
        oneday = datetime.timedelta(days=1)
        oneweek = datetime.timedelta(days=7)


        while start.weekday() != 0:
            start += oneday
        
        days = []
        while start.year <= year:
            days.append(start.strftime("%Y-%m-%d"))
            start += oneweek
            if start.month == 11 and start.year == year:
                break
        #print days

        sql = "SELECT waktu, a1, b1, c1, a2, b2, c2, a3, b3, c3, a4, b4, c4, a5, b5, c5, vnotch_q1, vnotch_q2, vnotch_q3, vnotch_tin1, vnotch_tin2, vnotch_tin3 \
                FROM waduk_daily \
                WHERE waktu IN (%s) AND pos_id=%s \
                ORDER BY waktu" % (','.join(["'"+ str(i) +"'" for i in days]), oid)

        rst2 = Agent._connection.queryAll(sql)


#-----menambahkan nilai curah hujan keesokan hari nya(manipulasi database hujan)------
        j=[]
        for f in rst2:
            j.append(f[0])

        day_ch=[]
        for dch in j:
            d_ch = dch  + datetime.timedelta(days=1)
            day_ch.append(d_ch)

        c_h=[]
        for a in day_ch:
            wd = WadukDaily.select(AND(WadukDaily.q.waktu==a, WadukDaily.q.pos==oid))
            try:
                wdch = wd[0].curahhujan
            except IndexError:
                wdch = None
            c_h.append(wdch)

        z=[]
        for b,d in zip (rst2, c_h):
            z.append((b,d))


        #print rst2

        #periode = datetime.date.today()
        #periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu

        tanggal = periode
        if periode.month > 10:
            tanggal = datetime.date(tanggal.year + 1, 11, 1)

        if tanggal.year <= 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=1))
                rr.append(periode.replace(day=16))
                periode += datetime.timedelta(days=jhar[i])
        if tanggal.year > 2018:
            jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
            rr = []
            for i in range(12):
                rr.append(periode.replace(day=15))
                rr.append(periode.replace(day=jhar[i]))
                periode += datetime.timedelta(days=jhar[i])

        sql = "SELECT waktu, po_tma, po_inflow_q, po_inflow_v, \
                po_outflow_q, po_outflow_v, \
                tma6, vol6, inflow_q, inflow_v, intake_q, intake_v, po_bona, po_bonb, vol_bona, vol_bonb \
                FROM waduk_daily \
                WHERE waktu IN (%s) AND pos_id=%s \
                ORDER BY waktu" % (','.join(["'"+str(i)+"'" for i in rr]), oid)

        rst1 = Agent._connection.queryAll(sql)



        meta = {'rst1': rst1, 'rst2': z, 'dari': periode, 'hingga': periode, 'tanggal':tanggal }
        return render.bendungan.keamanan.vnotchh(bendung, meta)

class Show:
    def GET(self, oid, tahun=None, bulan=None, tgl=None):
        try:
            bd = Agent.get(oid)
            if bd.AgentType != 3:
                raise web.notfound(404)
        except:
            raise web.notfound(404)
        if not tgl:
            try:
                tanggal = datetime.date(int(tahun), int(bulan), 1)
                return self.tma_monthly(oid, tahun, bulan)
            except:
                pass
        try:
            tanggal = datetime.date(int(tahun), int(bulan), int(tgl))
        except:
            tanggal = datetime.date.today()
        sebelum = tanggal - datetime.timedelta(days=1)
        sesudah = tanggal + datetime.timedelta(days=1)
        # '#248F8F', '#70DBDB', '#EBFAFA'
        try:
            bendungan = Agent.get(int(oid))
            if bendungan.AgentType != 3:
                raise SQLObjectNotFound
        except SQLObjectNotFound:
            return web.notfound(404)
        plotlines = ""
        tma = bendungan.get_segmented_tma_bendungan()
        series = [float(d[0]) for d in tma.get('kapasitas_series')]
        if tma.get('elevasi'):
            plotlines = "{ value: " + str(tma.get('elevasi') or 0) + "\
                , color: '#cc0000', width: 4, label: {text: '+'"
            + str(tma.get('elevasi') or 0) + "} }, "

        '''
            val_min = min(series, key=lambda x: abs(x - elevasi))
            idx = series.index(val_min)
            series.insert(idx + 1, {'y': elevasi,
                                    'dataLabels': {
                                        'enabled': 'true',
                                        'style': {'fontSize': 24}
                                    },
                          'marker':
                                    {'fillColor': '#33CC33', 'radius': 5}})
'''
        return render_anon.bendungan.show(
            bendungan,
            meta={'now': tanggal.strftime('%d %b %y'),
                  'before': sebelum.strftime('%d %b %y'),
                  'after': sesudah.strftime('%d %b %y'),
                  'categories1': [float(d[1]) for d
                                  in tma.get('kapasitas_series')],
                  'categories': [],
                  'series': series,
                  'plotlines': plotlines,
                  'tma': tma
                  })

    def tma_monthly(self, oid, tahun, bulan):
        '''Return http response TMA monthly on Pos oid'''
        bd = Agent.get(int(oid))
        return render_anon.bendungan.monthly(bd, {})


class Elevasi:
    def GET(self, oid):
        try:
            bd = Agent.get(oid)
            if bd.AgentType != 3:
                raise web.notfound(404)
        except:
            raise web.notfound(404)
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            tanggal = to_date(tanggal)
        sebelum = tanggal - datetime.timedelta(days=1)
        sesudah = tanggal + datetime.timedelta(days=1)
        try:
            bendungan = Agent.get(int(oid))
            if bendungan.AgentType != 3:
                raise SQLObjectNotFound
        except SQLObjectNotFound:
            return web.notfound(404)
        s_mamin = 5.8
        s_mabanjir = 10.8
        plotlines = ""
        tma = bendungan.get_segmented_tma_bendungan(tanggal)
        series = [[float(v), float(k)] for k, v in tma.get('kapasitas_series')]
        elev_series = []
        if tma.get('elevasi'):
            s_elevasi = (s_mabanjir - s_mamin) / (bendungan.siaga3-bendungan.siaga4) * (tma.get('elevasi') - bendungan.siaga4) + s_mamin
            plotlines = "{ value: \
                " + str(s_elevasi) + "\
                , color: '#000099', width: 2, label: {text: '+"\
                + str(tma.get('elevasi') or 0) + "', style: {fontSize: 24, backgroundColor: 'white'}}}, "
            elev_series = [[e[0], tma.get('elevasi') or 0] for e in series]
        return render.bendungan.elevasi(
            bendungan,
            meta={'now': tanggal.strftime('%d %b %y'),
                  'before': sebelum.strftime('%d %b %y'),
                  'after': sesudah.strftime('%d %b %y'),
                  'categories1': [float(d[1]) for d
                                  in tma.get('kapasitas_series')],
                  's_ma_min': s_mamin,
                  's_ma_normal': (s_mabanjir - s_mamin) / (bendungan.siaga3-bendungan.siaga4) * (bendungan.siaga1 - bendungan.siaga4) + s_mamin,
                  's_ma_banjir': s_mabanjir,
                  'series': series,
                  'elev_series': elev_series,
                  'plotlines': plotlines,
                  'tma': tma
                  })


class LengkungKapasitas:
    def GET(self, oid):
        try:
            bd = Agent.get(oid)
            if bd.AgentType != 3:
                raise web.notfound(404)
        except:
            raise web.notfound(404)
        tanggal = web.input().get('d')
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            try:
                tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except:
                tanggal = datetime.datetime.strptime(tanggal, "%d %b %y").date()
        sebelum = tanggal - datetime.timedelta(days=1)
        sesudah = tanggal + datetime.timedelta(days=1)
        # '#248F8F', '#70DBDB', '#EBFAFA'
        try:
            bendungan = Agent.get(int(oid))
            if bendungan.AgentType != 3:
                raise SQLObjectNotFound
        except SQLObjectNotFound:
            return web.notfound(404)
        plotlines = ""
        tma = bendungan.get_segmented_tma_bendungan(tanggal)
        series = [[float(v), float(k)] for k, v in tma.get('kapasitas_series')]
        elev_series = []
        if tma.get('elevasi'):
            plotlines = "{ value: \
                " + str(tma.get('elevasi') or 0) + "\
                , color: '#cc0000', width: 2, label: {text: '+"
            + str(tma.get('elevasi') or 0) + "', style: {fontSize: 24}}}, "
            elev_series = [[e[0], tma.get('elevasi') or 0] for e in series]

        return render.bendungan.lengkung_kapasitas(
            bendungan,
            meta={'now': tanggal.strftime('%d %b %y'),
                  'before': sebelum.strftime('%d %b %y'),
                  'after': sesudah.strftime('%d %b %y'),
                  'categories1': [float(d[1]) for d
                                  in tma.get('kapasitas_series')],
                  'categories': [],
                  's_ma_min': 0.8,
                  's_ma_normal': 10 / (bendungan.siaga3/bendungan.siaga4) * (bendungan.siaga1 - bendungan.siaga4),
                  's_ma_banjir': 10.8,
                  'series': series,
                  'elev_series': elev_series,
                  'plotlines': plotlines,
                  'tma': tma
                  })

    def tma_monthly(self, oid, tahun, bulan):
        '''Return http response TMA monthly on Pos oid'''
        bd = Agent.get(int(oid))
        return render.bendungan.monthly(bd, {})


class Index:
    def GET(self):
        tanggal = web.input().get('d')
        paper = web.input().get('paper', False)
        if not tanggal:
            tanggal = datetime.date.today()
        else:
            try:
                tanggal = datetime.datetime.strptime(tanggal, "%Y-%m-%d").date()
            except:
                tanggal = datetime.datetime.strptime(tanggal, "%d %b %y").date()
        BENDUNGAN = 3.0
        agents = Agent.select(Agent.q.AgentType == BENDUNGAN).orderBy(('wilayah', 'urutan'))

        # Menambah field Kondisi bendungan
        for a in agents:
            a.get_segmented_tma_bendungan(tanggal)

        data = [Struct(**{'pos': a,
                          'tma': Struct(
                              **a.get_segmented_tma_bendungan(tanggal))})
                for a in agents]
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

        template_render = render.bendungan.index
        if paper:
            template_render = render_plain.bendungan.harian_paper
        return template_render(
            bendungan=data,
            meta={'now': tanggal.strftime('%d %b %y'),
                  'before': sebelum.strftime('%d %b %y'),
                  'after': sesudah.strftime('%d %b %y')},
            wilayah=WILAYAH, js=js)


def test_volume_bendungan():
    lines = open('/tmp/jombor.txt').readlines()
    for l in lines:
        print l


if __name__ == '__main__':
    test_volume_bendungan()
