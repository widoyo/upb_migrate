# Data Management
import sys
import datetime
import calendar
import json
sys.path.append('../')
from memory_profiler import profile

import web
from sqlobject import OR, AND, SQLObjectNotFound

from models import AgentBd, conn, WadukDaily,TinggiMukaAir, BendungAlert
from models import CurahHujanTerkini, BendungFormA, BendungFormA1
from models import BendungFormB, BendungFormB1_1, BendungFormB1_2
from models import BendungFormB1_3, BendungFormB1_4, BendungFormB3
from models import NO_VNOTCH, FAIL_VNOTCH

from helper import to_date, json_serializer

urls = (
    '', 'BdIndex',
    '/(\w+\.*\-*\w+)/FormBlangko', 'FormBlangkoIndex',
    '/(\w+\.*\-*\w+)/FormBlangko/formA', 'FormA',
    '/(\w+\.*\-*\w+)/FormBlangko/formA1', 'FormA1',
    '/(\w+\.*\-*\w+)/FormBlangko/formB', 'FormB',
    #'/(\w+\.*\-*\w+)/FormBlangko/formB/rekap', 'RekapB',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_1', 'FormB1_1',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_2', 'FormB1_2',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_3', 'FormB1_3',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_4', 'FormB1_4',
    '/(\w+\.*\-*\w+)/FormBlangko/formB2_1', 'FormB2_1',
    '/(\w+\.*\-*\w+)/FormBlangko/formB2_2', 'FormB2_2',
    '/(\w+\.*\-*\w+)/FormBlangko/formB3', 'FormB3',
    '/(\w+\.*\-*\w+)/FormBlangko/formA/update', 'FormAUpdate',
    '/(\w+\.*\-*\w+)/FormBlangko/formA1/update', 'FormA1Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB/update', 'FormBUpdate',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_1/update', 'FormB1_1Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_2/update', 'FormB1_2Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_3/update', 'FormB1_3Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB1_4/update', 'FormB1_4Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB2_1/update', 'FormB2_1Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB2_2/update', 'FormB2_2Update',
    '/(\w+\.*\-*\w+)/FormBlangko/formB3/update', 'FormB3Update',
    '/update', 'BdUpdate',
    '/teknis', 'BdIndexTeknis',
    '/rotw', 'BdIndexRotw',
    '/rotw/csv', 'BdRtowImport',
    '/(\w+\.*\-*\w+)', 'BdShow',
    '/(\w+\.*\-*\w+)/rtow/export', 'BdRtowExport',
    '/(\w+\.*\-*\w+)/rtow/import', 'BdRtowImport',
    '/(\w+\.*\-*\w+)/add', 'BdPeriodicAdd',
)


app_admbd = web.application(urls, locals())
session = web.session.Session(app_admbd, web.session.DiskStore('sessions'),
        initializer={'username': None, 'is_admin': None,
            'table_name': None, 'err': None})

def csrf_token():
    if not session.has_key('csrf_token'):
        from uuid import uuid4
        session['csrf_token'] = uuid4().hex
    return session.get('csrf_token')


globals = {'session': session, 'csrf_token': csrf_token}
render = web.template.render('templates/', base='base_adm', globals=globals)


class BdRtowExport:
    def GET(self, table_name):
        inp = web.input()
        bd = dict([(a.table_name, a.AgentId) for a in  AgentBd.select(AgentBd.q.AgentType==3)])
        if table_name not in bd.keys():
            return 'table_name: ' + table_name + ' tidak ditemukan'
        rows = export_rtow(bd.get(table_name))
        web.header('Content-Type', 'application/vnd.ms-excel')
        web.header('Content-Disposition', 'attachment;filename=' + table_name + '.csv')
        s = table_name + '\n'
        for r in rows:
            s += '\t'.join(map(lambda x: type(x)== datetime.datetime and x.strftime('%Y-%m-%d') or str(x), r)) + '\n'
        return s


class BdRtowImport:
    def GET(self, table_name):
        return render.adm.bendungan.rtow_import({'table_name': table_name})

    def POST(self, table_name):
        fi = web.input(rtow_file={})
        data = fi['rtow_file'].file.read()
        fname = '/tmp/' + table_name + '.csv'
        with open(fname, 'w') as f:
            f.write(data)
        data_in = import_rtow(fname)
        pos_id = data_in.get('pos_id')
        pos = AgentBd.get(pos_id)
        date_list = ','.join(["'"+str(d.get('waktu'))+"'" for d in data_in.get('object')])
        for d in data_in.get('object'):
            try:
                wd = WadukDaily.select(AND(WadukDaily.q.pos==pos, WadukDaily.q.waktu==d.get('waktu')))[0]
                wd.set(**d)
            except IndexError:
                wd = WadukDaily(**d)
        return web.redirect('/adm/bendungan/rotw', absolute=True)


def import_rtow(file_input):
    '''Mengimport data RTOW (setahun) dari file excel
            nop1 | nop2 | des1 | des2 | ...
    tma
    outflow_q
    inflow_q
    bon_a
    bon_b


    '''
    lines = open(file_input).readlines()
    nama_bendungan = lines[0].strip()
    bd_names = dict([(a.table_name, a.AgentId) for a in AgentBd.select(AgentBd.q.AgentType==3)])
    if nama_bendungan not in bd_names.keys():
        ret = dict(ok=False, msg=','.join(bd_names))
        return ret
    if len(lines) != 26:
        ret = dict(ok=False, msg='Data harus dari Nop - Okt / 24 baris')
        return ret
    cols = lines[1].strip().split('\t')
    data = []
    for i in range(24):
        i += 2
        line = lines[i].split('\t')
        waktu = datetime.datetime.strptime(line[0], '%Y-%m-%d').date()
        val = dict(waktu=waktu, posID=bd_names.get(nama_bendungan))
        for j in (1,2,3,4,5,6,7,8):
            try:
                val[cols[j]] = float(line[j].strip())
            except ValueError:
                val[cols[j]] = None
        data.append(val)
    ret = dict(ok=True, pos_id=bd_names.get(nama_bendungan), table_name=nama_bendungan, object=data)
    return ret


def export_rtow(bd_id, periode=datetime.date.today()):
    '''Return csv of RTOW Bendungan dg ID bd_id'''
    if periode.month < 11:
        periode = datetime.date(periode.year - 1, 11, 1) # 1 Nop tahun lalu
    else:
        periode = datetime.date(periode.year, 11, 1)
    jhar = [30, 31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31]
    rr = []
    for i in range(12):
        rr.append(periode.replace(day=1))
        rr.append(periode.replace(day=16))
        periode += datetime.timedelta(days=jhar[i])
    sql = "SELECT waktu, po_tma, po_vol, po_outflow_q, po_inflow_q, po_bona, po_bonb, vol_bona, vol_bonb \
            FROM waduk_daily \
            WHERE pos_id=%s AND waktu IN (%s) \
            ORDER BY pos_id, waktu" % (bd_id, ','.join(["'"+str(i)+"'" for i in rr]))
    rows = conn.queryAll(sql)
    header = "waktu,po_tma,po_vol,po_outflow_q,po_inflow_q,po_bona,po_bonb,vol_bona,vol_bonb".split(',')
    return [header] + list(rows)


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


def bd_hari(sampling=datetime.date.today()):
    sp = datetime.date(2016, 1, 3)
    wds = AgentBd.select(AgentBd.q.AgentType==3)
    rs = WadukDaily.select(AND(WadukDaily.q.waktu>=sp, WadukDaily.q.waktu<=sp)).orderBy(('pos_id, waktu',))
    for r in rs:
        print r.pos.cname, r.waktu
    return sampling


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


class BdIndexTeknis:
    @login_required
    @admin_required
    def GET(self):
        bdgs = AgentBd.select(AgentBd.q.AgentType==3).orderBy('wilayah')
        poses = bdgs
        return render.adm.bendungan.teknis({'poses': poses})

    @login_required
    @admin_required
    def POST(self):
        inp = web.input()
        try:
            wd = AgentBd.get(int(inp.get('pk')))
            wd.set(**{inp.get('name'): float(inp.get('value', 0))})
        except SQLObjectNotFound:
            return web.notfound()
        except ValueError:
            wd = AgentBd.get(int(inp.get('pk')))
            wd.set(**{inp.get('name'): inp.get('value', 0)})

        return {"Ok": "true"}


class BdUpdate:
    @login_required
    def POST(self):
        inp = web.input()
        try:
            wd = WadukDaily.get(int(inp.get('pk')))
            wd.set(**{inp.get('name'): float(inp.get('value', 0))})
            wd = wd.sqlmeta.asDict()
            waktu = wd['waktu']
            tgl = waktu.strftime('%Y-%m-%d')
            id = wd['posID']
            tma6 = wd['tma6']
            tma12 = wd['tma12']
            tma18 = wd['tma18']
            # memeriksa apakah table 'tma' telah terisi dari pos dan waktu
            if tma6:
                tmas = [t for t in TinggiMukaAir.select(AND(TinggiMukaAir.q.agent==id, TinggiMukaAir.q.waktu==tgl, TinggiMukaAir.q.jam=='6'))]
                if tmas == []:
                    TinggiMukaAir(**{'agent': id, 'waktu': waktu, 'jam': '6','manual': tma6, 'origin': 'web'})
                if tmas:
                    tma = [t for t in tmas if t.jam == '6'][0]
                    tma.set(**{'jam': '6', 'manual': tma6 })
                    tma.syncUpdate()
            if tma12:
                tmas = [t for t in TinggiMukaAir.select(AND(TinggiMukaAir.q.agent==id, TinggiMukaAir.q.waktu==tgl, TinggiMukaAir.q.jam=='12'))]
                if tmas == []:
                    TinggiMukaAir(**{'agent': id, 'waktu': waktu, 'jam': '12','manual': tma12, 'origin': 'web'})
                if tmas:
                    tma = [t for t in tmas if t.jam == '12'][0]
                    tma.set(**{'jam': '12', 'manual': tma12 })
                    tma.syncUpdate()
            if tma18:
                tmas = [t for t in TinggiMukaAir.select(AND(TinggiMukaAir.q.agent==id, TinggiMukaAir.q.waktu==tgl, TinggiMukaAir.q.jam=='18'))]
                if tmas == []:
                    TinggiMukaAir(**{'agent': id, 'waktu': waktu, 'jam': '18','manual': tma18, 'origin': 'web'})
                if tmas:
                    tma = [t for t in tmas if t.jam == '18'][0]
                    tma.set(**{'jam': '18', 'manual': tma18 })
                    tma.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormAUpdate:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formA = BendungFormA.get(int(inp.get('pk')))
            data_ = inp.get('value',0)
            try:
                formA.set(**{inp.get('name'): float(data_)})
            except ValueError:
                formA.set(**{inp.get('name'): data_})
            except TypeError:
                formA.set(**{inp.get('name'): int(data_)})
            formA.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormA1Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formA1 = BendungFormA1.get(int(inp.get('pk')))
            data_ = inp.get('value',0)
            try:
                formA1.set(**{inp.get('name'): float(data_)})
            except ValueError:
                formA1.set(**{inp.get('name'): data_})
            except TypeError:
                formA1.set(**{inp.get('name'): int(data_)})
            formA1.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}


class FormBUpdate:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB = BendungFormB.get(int(inp.get('pk')))
            try:
                formB.set(**{inp.get('name'): float(inp.get('value',0))})
            except ValueError:
                formB.set(**{inp.get('name'): inp.get('value',0)})
            formB.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormB1_1Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB1_1 = BendungFormB1_1.get(int(inp.get('pk')))
            try:
                formB1_1.set(**{inp.get('name'): float(inp.get('value',0))})
            except ValueError:
                formB1_1.set(**{inp.get('name'): inp.get('value',0)})
            formB1_1.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}


class FormB1_2Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB1_2 = BendungFormB1_2.get(int(inp.get('pk')))
            try:
                formB1_2.set(**{inp.get('name'): float(inp.get('value',0))})
            except ValueError:
                formB1_2.set(**{inp.get('name'): inp.get('value',0)})
            formB1_2.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormB1_3Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB1_3 = BendungFormB1_3.get(int(inp.get('pk')))
            try:
                formB1_3.set(**{inp.get('name'): str(inp.get('value',0))})
            except ValueError:
                formB1_3.set(**{inp.get('name'): inp.get('value',0)})

            formB1_3.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormB1_4Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB1_4 = BendungFormB1_4.get(int(inp.get('pk')))
            try:
                formB1_4.set(**{inp.get('name'): str(inp.get('value',0))})
            except ValueError:
                formB1_4.set(**{inp.get('name'): inp.get('value',0)})

            formB1_4.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}

class FormB3Update:
    @login_required
    def POST(self,table_name):
        inp = web.input()
        print inp
        try:
            formB3 = BendungFormB3.get(int(inp.get('pk')))
            try:
                formB3.set(**{inp.get('name'): str(inp.get('value',0))})
            except ValueError:
                formB3.set(**{inp.get('name'): inp.get('value',0)})

            formB3.syncUpdate()
        except SQLObjectNotFound:
            return web.notfound()

        return {"Ok": "true"}


class BdShow:
    @login_required
    @profile
    def GET(self, table_name):
        inp = web.input()
        csv = inp.get('csv')
        ordering = csv and 'waktu' or '-waktu'
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
        except:
            return web.notfound()
        webinput = web.input(sampling=str(datetime.date.today()))
        tg = datetime.datetime.strptime(webinput.sampling, '%Y-%m-%d').date()
        #sql = "SELECT * FROM waduk_daily WHERE \
        #        pos_id=%s AND waktu='%s'" % (pos.id, tg)
        #rs = conn.queryAll(sql)
        if tg.month == datetime.date.today().month:
            rs = [r for r in WadukDaily.select(WadukDaily.q.pos==pos).orderBy(ordering) if r.waktu.month == tg.month and r.waktu.year == tg.year and r.waktu.day <= tg.day]
        else:
            rs = [r for r in WadukDaily.select(WadukDaily.q.pos==pos).orderBy(ordering) if r.waktu.month == tg.month and r.waktu.year == tg.year]
        if csv:
        
            web.header('Content-Type', 'application/cnd.ms-excel')
            web.header('Content-Disposition', 'attachment; filename="'+table_name+'.csv"')
            cols = "waktu,curahhujan,tma6,vol6,tma12,vol12,tma18,vol18,inflow_q,inflow_v,intake_q,intake_v,outflow_q,outflow_v,spillway_q,spillway_v,vnotch_tin1,vnotch_q1,vnotch_tin2,vnotch_q2,vnotch_tin3,vnotch_q3,a1,a2,a3,a4,a5,b1,b2,b3,b4,b5,c1,c2,c3,c4,c5".split(',')
            out = ",".join(cols)
            for r in rs:
                out += "\n" + ",".join([str(getattr(r, c)) for c in cols])
                #out += "\n"
            return out
        msg = ''
        if session.has_key('err'):
            msg = session.pop('err')
        return render.adm.bendungan.show({'bd': pos, 'periodic': rs,
            'tanggal': tg, 'msg': msg})



    @login_required
    # @csrf_protected
    def POST(self, table_name):
        try:
            try:
                pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            except IndexError:
                return web.notfound()
            inp = web.input()
            fields = 'curahhujan,tma,vol,inflow_q,inflow_v,intake_q,intake_v,spillway_q,spillway_v'.split(',')
            koloms = 'tanggal,jam,tma'.split(',')
            form2_fields = 'tma,vol'.split(',')
            form3_fields = 'vnotch_tin1,vnotch_q1,vnotch_tin2,vnotch_q2,vnotch_tin3,vnotch_q3'.split(',')
            form4_fields = 'a1,b1,c1,a2,b2,c2,a3,b3,c3,a4,b4,c4,a5,b5,c5'.split(',')
            # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'waduk_daily'
            try:
                wd = WadukDaily.select(AND(WadukDaily.q.waktu==to_date(inp.waktu), WadukDaily.q.pos==pos))[0]
                is_wd_exist = True
            except IndexError:
                wd = None
                is_wd_exist = False

            # memeriksa apakah table 'tma' telah terisi dari pos dan waktu
            tmas = [t for t in TinggiMukaAir.select(AND(TinggiMukaAir.q.agent==pos, TinggiMukaAir.q.waktu==to_date(inp.waktu)))]

            if inp.tahap == 'pagi':
                obj = {}
                for f in fields:
                    if inp.get(f):
                        nilai = float(inp.get(f))
                    else:
                        nilai = None
                    if f in 'tma,vol'.split(','):
                        obj.update({f + '6': nilai})
                    else:
                        obj.update({f: nilai})
                obj.update({'pos': pos, 'waktu': to_date(inp.waktu)})
                if not is_wd_exist:
                    wd = WadukDaily(**obj)
                else:
                    wd.set(**obj)
                # Mengupdate / Insert data TinggiMukaAir
                try:
                    tma = [t for t in tmas if t.jam == '6'][0]
                    tma.set(**{'jam': '6', 'manual': obj.get('tma6')})
                    tma.syncUpdate()
                except:
                    tma = TinggiMukaAir(**{'agent': pos,
                        'waktu': obj.get('waktu'), 'jam': '6',
                        'manual': obj.get('tma6'), 'origin': 'web'})
                    tma.syncUpdate()
            elif inp.tahap in ('siang', 'sore'):
                # jika data pagi belum ada, untuk WadukDaily perlu error
                if not is_wd_exist:
                    session['err'] = "<strong style='margin-right: 10px'>P e r h a t i a n</strong>Data TMA Pagi tidak ditemukan."
                    return web.redirect('/adm/bendungan/' + table_name + '?sampling=' + inp.waktu.replace('/', '-'), absolute=True)
                per = inp.tahap == 'siang' and '12' or '18'
                if per == '12':
                    wd.tma12 = float(inp.get('tma'))
                    wd.vol12 = float(inp.get('vol'))
                elif per == '18':
                    wd.tma18 = float(inp.get('tma'))
                    wd.vol18 = float(inp.get('vol'))

                # Mengupdate / Insert data TinggiMukaAir
                try:
                    tma = [t for t in tmas if t.jam == per][0]
                    tma.set(**{'jam': per, 'manual': float(inp.get('tma'))})
                    tma.syncUpdate()
                except:
                    tma = TinggiMukaAir(**{'agent': pos,
                        'waktu': to_date(inp.waktu), 'jam': per,
                        'manual': float(inp.get('tma')), 'origin': 'web'})
                    tma.syncUpdate()
            elif inp.tahap == 'vnotch': # inputan vnotch
                # jika data pagi belum ada, untuk WadukDaily perlu error
                if not is_wd_exist:
                    session['err'] = "<strong style='margin-right: 10px'>P e r h a t i a n</strong>Data TMA Pagi tidak ditemukan."
                    return web.redirect('/adm/bendungan/' + table_name + '?sampling=' + inp.waktu.replace('/', '-'), absolute=True)
                obj = {}
                for f in form3_fields:
                    if inp.get(f):
                        obj.update({f: float(inp.get(f))})
                wd.set(**obj)
            elif inp.tahap == 'piezometer':
                # jika data pagi belum ada, untuk WadukDaily perlu error
                if not is_wd_exist:
                    session['err'] = "<strong style='margin-right: 10px'>P e r h a t i a n</strong>Data TMA Pagi tidak ditemukan."
                    return web.redirect('/adm/bendungan/' + table_name + '?sampling=' + inp.waktu.replace('/', '-'), absolute=True)
                obj = {}
                for f in form4_fields:
                    if inp.get(f):
                        obj.update({f: float(inp.get(f))})
                wd.set(**obj)

            return web.redirect('/adm/bendungan/' + table_name, absolute=True)

        except AttributeError:
            try:
                bendungan = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
                bendungan_id = bendungan.id
                print bendungan_id
            except IndexError:
                return web.notfound()
            inp = web.input()
            # memeriksa apakah record pada bendungan_id, tanggal dan jam sudah ada pada tabel 'bendung_alert'
            if inp.tahap == 'banjir':
                try:
                    ba = BendungAlert.select(AND(BendungAlert.q.tanggall==to_date(inp.tanggall), BendungAlert.q.bendungan==bendungan_id, BendungAlert.q.jam==inp.jam))[0]
                    print ba
                    is_ba_exist = True
                except IndexError:
                    ba = None
                    is_ba_exist = False

                if inp.tahap == 'banjir':
                    obj = {'bendunganID':bendungan_id, 'tanggall':to_date(inp.tanggall), 'jam':inp.jam, 'tmab':float(inp.tmab), 'spillwayb_q':float(inp.spillwayb_q)}
                    if not is_ba_exist:
                        ba = BendungAlert(**obj)
                    else:
                        ba.set(**obj)
                return web.redirect('/adm/bendungan/' + table_name, absolute=True)


            if inp.tahap == 'chterkini':
            # memeriksa apakah record pada bendungan__id, tanggal dan jam sudah ada pada tabel 'curahhujan_terkini'

                try:
                    chkini = CurahHujanTerkini.select(AND(CurahHujanTerkini.q.tanggall==to_date(inp.tanggall), CurahHujanTerkini.q.bendungan==bendungan_id, CurahHujanTerkini.q.jam==inp.jam))[0]
                    print chkini
                    is_chkini_exist = True
                except IndexError:
                    chkini = None
                    is_chkini_exist = False

                if inp.tahap == 'chterkini':
                    objj = {'bendunganID':bendungan_id, 'tanggall':to_date(inp.tanggall), 'jam':inp.jam, 'ch_terkini':float(inp.ch_terkini)}
                    if not is_chkini_exist:
                        chkini = CurahHujanTerkini(**objj)
                    else:
                        chkini.set(**objj)
                return web.redirect('/adm/bendungan/' + table_name, absolute=True)


class BdIndexRotw:
    @login_required
    @admin_required
    def GET(self):
        inp = web.input()
        try:
            pola_operasi = open('pola_operasi.txt').read()
        except:
            pola_operasi = "Basah"
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
        sql = "SELECT pos_id, waktu, po_outflow_q, po_tma, po_outflow_v, id, po_bona, po_bonb, vol_bona, vol_bonb \
                FROM waduk_daily \
                WHERE waktu IN (%s) \
                ORDER BY pos_id, waktu" % ','.join(["'"+str(i)+"'" for i in rr])
        rst = conn.queryAll(sql)
        bdgs = dict([(a.AgentId, a) for a in AgentBd.select(AgentBd.q.AgentType==3)])
        bids = list(set([r[0] for r in rst]))
        data = []
        bid = 0
        row = []
        for r in rst:
            if bid != r[0]:
                bid = r[0]
                row = [{'id': r[5], 'tma': r[3], 'q': r[2], 'v': r[4], 'bona': r[6], 'bonb': r[7], 'volbona': r[8], 'volbonb': r[9]}]
                data.append((r[0], row))
                continue
            row.append({'id': r[5], 'tma': r[3], 'q': r[2], 'v': r[4], 'bona': r[6], 'bonb': r[7], 'volbona': r[8], 'volbonb': r[9]})
        return render.adm.bendungan.rotw({'data': data, 'bendungan': bdgs,
            'periode': rr, 'pola_operasi': pola_operasi, 'tanggal': tanggal})


class BdIndex:
    @login_required
    @admin_required
    def GET(self):
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


class FormBlangkoIndex:
    @login_required
    def GET(self, tabel_name):
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == tabel_name][0]
        except:
            return web.notfound()
        return render.adm.bendungan.FormBlangko.index({'bd':pos,'table_name': tabel_name})

class FormA:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        csv = inp.get('csv')
        ordering ='-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

#-----------------------------------------------------------------------------
        if tgal.month == datetime.date.today().month:
            bendufor = [r for r in BendungFormA.select(BendungFormA.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day <= tgal.day]
            #sql = "SELECT id FROM bendung_form_a WHERE bendungan_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s AND DAY(waktu)<=%s" %(poss.AgentId, tgal.year, tgal.month, tgal.day)
            #ids = [i[0] for i in conn.queryAll(sql)]
            #bendufor = BendungFormA.select(BendungFormA.q.id in ids)
        else:
            bendufor = [r for r in BendungFormA.select(BendungFormA.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day <= tgal.day]
            #sql = "SELECT id FROM bendung_form_a WHERE bendungan_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s AND DAY(waktu)<=%s" %(poss.AgentId, tgal.year, tgal.month, tgal.day)
            #ids = [i[0] for i in conn.queryAll(sql)]
            #bendufor = BendungFormA.select(BendungFormA.q.id in ids)

#-----------------------------------------------------------------------------
        order ='-waktu'
        tagl = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()
        if tagl.month == datetime.date.today().month:
            wadudail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day <= tagl.day]
            #sql = "SELECT id FROM waduk_daily WHERE pos_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s AND DAY(waktu)<=%s" %(poss.AgentId, tgal.year, tgal.month, tgal.day)
            #ids = [i[0] for i in conn.queryAll(sql)]
            #wadudail = WadukDaily.select(WadukDaily.q.id in ids)
        else:
            wadudail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day <= tagl.day]
            #sql = "SELECT id FROM waduk_daily WHERE pos_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s AND DAY(waktu)<=%s" %(poss.AgentId, tgal.year, tgal.month, tgal.day)
            #ids = [i[0] for i in conn.queryAll(sql)]
            #wadudail = WadukDaily.select(WadukDaily.q.id in ids)

#------menampilkan 30 hari-----------------------------------------------------
        now=datetime.datetime.now()
        if tgal:
            now = tgal
        tahun = now.year
        bul = now.month
        num_hari = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong = [datetime.date(tahun,bul, i) for i in range(1, num_hari)]
        dout = [(t, []) for t in tgl_kosong]
        dout = dict(dout)
        dwds = [(r.waktu.date(), r) for r in wadudail]
        dwds = dict(dwds)
        outputt = sorted([(t, dwds.get(t)) for t in dout.keys()])

        a = []
        for c in outputt:
            a.append(c[1])

        now = datetime.datetime.now()
        if tgal:
            now = tgal
        tahuns = now.year
        buls = now.month
        num_harii = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong1 = [datetime.date(tahuns,buls, k) for k in range(1, num_harii)]
        bfout = [(w, []) for w in tgl_kosong1]
        bfout = dict(bfout)
        dbfa = [(rr.waktu, rr) for rr in bendufor]
        dbfa = dict(dbfa)
        output_dbfa = sorted([(w, dbfa.get(w)) for w in bfout.keys()])

        y = []
        for x in output_dbfa:
            y.append(x[1])

        z = []
        for b,d in zip (a, y):
                #if b != None and d !=None:
                if b and d:
                    z.append((b,d))

#----------------------vol total-----------------------
        p = []
        for s in z :
            total_vol = (s[1].vol_pintu1 or 0) + (s[1].vol_pintu2 or 0) + (s[1].vol_pelimpahutama or 0)
            p.append(total_vol)

#----------------------debit rerata total-----------------------
        v = []
        for q in z:
            total_debit = (q[1].debit_rerata_pintu1 or 0) + (q[1].debit_rerata_pintu2 or 0) + (q[1].debit_pelimpahutama or 0)
            v.append(total_debit)
        j = []
        k = 0
        for t,u in zip (a, y):
                if t and u:
                    j.append((t,u,p[k],v[k]))
                    k = k+1

        return render.adm.bendungan.FormBlangko.forma.Form_A({'tanggal': tgal, 'bd':poss, 'periodicc': output_dbfa, 'periodic_wdd': outputt, 'new_periodic': j, 'table_name': table_nama})



    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,bukaan_pintu1,vol_pintu1,debit_rerata_pintu1,jam_pintu1,bukaan_pintu2,vol_pintu2,debit_rerata_pintu2,jam_pintu2,h_pelimpahutama,vol_pelimpahutama,debit_pelimpahutama,jam_pelimpahutama,vol_total_pelepasan,debit_rerata_total_pelepasan,keterangan'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormA.select(AND(BendungFormA.q.waktu==to_date(inp.waktu), BendungFormA.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False

        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)

                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        print objj
        if not is_form_exist:
            form = BendungFormA(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')


        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formA?sampling='+waktuu, absolute=True)

class FormA1:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        csv = inp.get('csv')
        ordering ='-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

#-----------------------------------------------------------------------------
        if tgal.month == datetime.date.today().month:
            bendufor = [r for r in BendungFormA1.select(BendungFormA1.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day <= tgal.day]
        else:
            bendufor = [r for r in BendungFormA1.select(BendungFormA1.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day] 


#-----------------------------------------------------------------------------
        order ='-waktu'
        tagl = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()
        if tagl.month == datetime.date.today().month:
            wadudail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day <= tagl.day]
        else:
            wadudail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day == tagl.day]


#------menampilkan 30 hari-----------------------------------------------------
        now=datetime.datetime.now()
        if tgal:
            now = tgal
        tahun = now.year
        bul = now.month
        num_hari = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong = [datetime.date(tahun,bul, i) for i in range(1, num_hari)]
        dout = [(t, []) for t in tgl_kosong]
        dout = dict(dout)
        dwds = [(r.waktu.date(), r) for r in wadudail]
        dwds = dict(dwds)
        outputt = sorted([(t, dwds.get(t)) for t in dout.keys()])

        a=[]
        for c in outputt:
            a.append(c[1])
        #print a



        now=datetime.datetime.now()
        if tgal:
            now = tgal
        tahuns = now.year
        buls = now.month
        num_harii = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong1 = [datetime.date(tahuns,buls, k) for k in range(1, num_harii)]
        bfout = [(w, []) for w in tgl_kosong1]
        bfout = dict(bfout)
        dbfa = [(rr.waktu, rr) for rr in bendufor]
        dbfa = dict(dbfa)
        output_dbfa = sorted([(w, dbfa.get(w)) for w in bfout.keys()])

        y=[]
        for x in output_dbfa:
            y.append(x[1])
        #print y


        z=[]
        for b,d in zip (a, y):
                if b != None and d !=None:
                    z.append((b,d))       

        


        return render.adm.bendungan.FormBlangko.forma1.Form_A1({'tanggal': tgal, 'bd':poss, 'periodicc': output_dbfa, 'periodic_wdd': outputt, 'new_periodic': z, 'table_name': table_nama})


    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,luas_baku,nama_di,luas_terlayani,padi_jenistanaman,palawija_jenistanaman,bero_jenistanaman,padi_umurtanaman,palawija_umurtanaman,padi_sisaumur,palawija_sisaumur,keterangan'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormA1.select(AND(BendungFormA1.q.waktu==to_date(inp.waktu), BendungFormA1.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False

        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)

                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        print objj
        if not is_form_exist:
            form = BendungFormA1(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')


        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formA1?sampling='+waktuu, absolute=True)



class FormB:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        csv = inp.get('csv')
        ordering ='-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

#-----------------------------------------------------------------------------
        if tgal.month == datetime.date.today().month:
            bendfor = [r for r in BendungFormB.select(BendungFormB.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day <= tgal.day]
        else:
            bendfor = [r for r in BendungFormB.select(BendungFormB.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day] 


#-----------------------------------------------------------------------------
        order ='-waktu'
        tagl = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()
        if tagl.month == datetime.date.today().month:
            waddail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day <= tagl.day]
        else:
            waddail = [rr for rr in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(order) if rr.waktu.month == tagl.month and rr.waktu.year == tagl.year and rr.waktu.day == tagl.day]


#------menampilkan 30 hari-----------------------------------------------------
        now=datetime.datetime.now()
        if tgal:
            now = tgal
        tahun = now.year
        bul = now.month
        num_hari = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong = [datetime.date(tahun,bul, i) for i in range(1, num_hari)]
        dout = [(t, []) for t in tgl_kosong]
        dout = dict(dout)
        dwds = [(r.waktu.date(), r) for r in waddail]
        dwds = dict(dwds)
        output = sorted([(t, dwds.get(t)) for t in dout.keys()])

        now=datetime.datetime.now()
        if tgal:
            now = tgal
        tahuns = now.year
        buls = now.month
        num_harii = (calendar.monthrange(now.year, now.month)[1]) + 1
        tgl_kosong1 = [datetime.date(tahuns,buls, k) for k in range(1, num_harii)]
        bfout = [(w, []) for w in tgl_kosong1]
        bfout = dict(bfout)
        dbfs = [(rr.waktu, rr) for rr in bendfor]
        dbfs = dict(dbfs)
        output_dbfs = sorted([(w, dbfs.get(w)) for w in bfout.keys()])


        return render.adm.bendungan.FormBlangko.formb.Form_B({'tanggal': tgal, 'bd':poss, 'periodic': output_dbfs, 'periodic_wd': output, 'table_name': table_nama})


    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,retakan_puncak_bendung,penurunan_puncak_bendung,kelurusan_puncak_bendung,retakan_lereng_hulu,penurunan_lereng_hulu,tonjolan_lereng_hulu,retakan_lereng_hilir,penurunan_lereng_hilir,tonjolan_lereng_hilir,retakan_pd_beton,gerusan_ujung_hilir,mengetahui_petugas,mengetahui_koordinator'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB.select(AND(BendungFormB.q.waktu==to_date(inp.waktu), BendungFormB.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        print objj
        if not is_form_exist:
            form = BendungFormB(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')


        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB?sampling='+waktuu, absolute=True)


class FormB1_1:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rss = [r for r in BendungFormB1_1.select(BendungFormB1_1.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rss = [r for r in BendungFormB1_1.select(BendungFormB1_1.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]
            print rss


        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]


        return render.adm.bendungan.FormBlangko.formb1_1.Form_B1_1({'tanggal': tgal, 'bd':poss, 'periodic': rss, 'periodic_wd': rs2})

    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,kondisi_cuaca,tinggi,panjang,kond_jln_atas_mercu,tanda_penurunan_mercu,tanda_pergerakan_mercu,kond_pembuang_mercu,kond_pagar_mercu,tanda_gerakan_lerenghulu,tonjolan_lubangbenam_retakan_lerenghulu,erosi_penurunan_lerenghulu,dimana_kedalaman_lebarpanjangretakan_lerenghulu,tumbuhan_sarangbinatang_lerenghulu,tanda_retak_platbeton,dimana_kedalaman_lebarpanjangretakan_platbeton,parimeter_joint_platbeton,kond_beton_platbeton,erosi_platbeton,kond_permukaan_buitmen,erosi_buitmen,tanda_gerakan_riprap,rusak_krn_cuaca_riprap,pelapukan_riprap,erosi_riprap,slip_dbwhair_riprap,tanda_gerakan_lerenghilir,tonjolan_lubangbenam_retak_lerenghilir,erosi_penurunan_longsorantanah_lerenghilir,dimana_kedalaman_lebarpanjangretakan_lerenghilir,slip_dbwhair_lerenghilir,tanda_rembesan,dimana_kuantitas_warna_rembesan,kondtumbuhan,jns_plindung_lereng'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB1_1.select(AND(BendungFormB1_1.q.waktu==to_date(inp.waktu), BendungFormB1_1.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        if not is_form_exist:
            form = BendungFormB1_1(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')



        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB1_1?sampling='+waktuu, absolute=True)

class FormB1_2:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rss = [r for r in BendungFormB1_2.select(BendungFormB1_2.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rss = [r for r in BendungFormB1_2.select(BendungFormB1_2.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]
            print rss


        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]


        return render.adm.bendungan.FormBlangko.formb1_2.Form_B1_2({'tanggal': tgal, 'bd':poss, 'periodic': rss, 'periodic_wd': rs2})

    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,jenis_bendung,pintu_jml_jenis_bendung,pengoperasian_bendung,operasidarurat_bendung,pelimpahbantu_bendung,jplimphbantu_bendung,kondisi_salpengahantar,lantdasar_salpenghantar,lereng_salpenghantar,kondisi_spillweir,auserosi_spillweir,lokasi_spillweir,kondisi_dinding,auserosi_dinding,dmn_dinding,kondisijoint_dinding,kondisisaluran_dinding,kond_salcuram,auserosi_salcuram,lapbasah_salcuram,dmn_salcuram,jenis_kolam,kondisi_kolam,auserosi_kolam,lapbasah_kolam,dmn_kolam,ketidakwajaran_kinerja,tandaslip_dsekitar,tandarembesan_dsekitar,jenistumbuhan_dsekitar,gangguan_dsekitar'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB1_2.select(AND(BendungFormB1_2.q.waktu==to_date(inp.waktu), BendungFormB1_2.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        if not is_form_exist:
            form = BendungFormB1_2(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')



        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB1_2?sampling='+waktuu, absolute=True)

class FormB1_3:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rss = [r for r in BendungFormB1_3.select(BendungFormB1_3.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rss = [r for r in BendungFormB1_3.select(BendungFormB1_3.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]
            print rss


        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]


        return render.adm.bendungan.FormBlangko.formb1_3.Form_B1_3({'tanggal': tgal, 'bd':poss, 'periodic': rss, 'periodic_wd': rs2})

    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,lok_piezometer,jumlah_piezometer,jenis_piezometer,kond_baik_piezometer,kond_tdkbaik_piezometer,lok_alt_rembesan,jml_alt_rembesan,jns_alt_rembesan,kond_altbaik_rembesan,kond_alttdkbaik_rembesan,lok_altpnurunan,jml_altpnurunan,jns_altpnurunan,kond_altbaikpnurunan,kond_alttdkbaikpnurunan,lok_multilayer,jml_multilayer,jns_multilayer,kond_baikmultilayer,kond_tdkbaikmultilayer,lok_observasi,jml_observasi,jns_observasi,kond_baikobservasi,kond_tdkbaikobservasi,lok_inclinometer,jml_inclinometer,jns_inclinometer,kond_baikinclinometer,kond_tdkbaikinclinometer,tandaerosi_kakibendung,aliranlubang_kakibendung,lapsbasah_kakibendung,dmn_kakibendung,lihat_lubang_benam_tumpuanbendung,slip_tumpuanbendung,tndapatahan_tumpuanbendung,retakan_tumpuanbendung'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB1_3.select(AND(BendungFormB1_3.q.waktu==to_date(inp.waktu), BendungFormB1_3.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        if not is_form_exist:
            form = BendungFormB1_3(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')



        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB1_3?sampling='+waktuu, absolute=True)

class FormB1_4:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rss = [r for r in BendungFormB1_4.select(BendungFormB1_4.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rss = [r for r in BendungFormB1_4.select(BendungFormB1_4.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]
            print rss


        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]


        return render.adm.bendungan.FormBlangko.formb1_4.Form_B1_4({'tanggal': tgal, 'bd':poss, 'periodic': rss, 'periodic_wd': rs2})

    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,lok_inlet,jns_inlet,akses_inlet,kond_inlet,auserosi_inlet,lapbas_inlet,dmnlok_inlet,kondsamb_inlet,kondsalbuang_inlet,pintu_hidromekanik,katupjenis_hidromekanik,metodoperasi_hidromekanik,pengoperasiandarurat_hidromekanik,kond_hidromekanik,lok_outlet,jns_outlet,akses_outlet,kond_outlet,auserosi_outlet,lapsbas_outlet,dmnlok_outlet,kondsamb_outlet,kondsalbuang_outlet,ukur_gorong,kond_gorong,auserosi_gorong,lapsbas_gorong,dmnlok_gorong,kondsamb_gorong,kondsalbuang_gorong,endapan_gorong,endapan_waduk,tebingsungai_hilir,erosipengikisan_hilir,pengaruhtumbuhan_hilir,habitatterdekat_hilir,jumlahpenduduk_hilir'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB1_4.select(AND(BendungFormB1_4.q.waktu==to_date(inp.waktu), BendungFormB1_4.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        if not is_form_exist:
            form = BendungFormB1_4(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')



        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB1_4?sampling='+waktuu, absolute=True)

class FormB2_1:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air

        rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year]

        return render.adm.bendungan.FormBlangko.formb2_1.Form_B2_1({'tanggal': tgal, 'bd':poss, 'periodic': rs2})

class FormB2_2:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        #menghubungkan dengan tabel waduk daily untuk mendapatkan data elevasi muka air
        rs2 = [r for r in WadukDaily.select(WadukDaily.q.pos==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year]
        e=[]
        for p in rs2:
            waktuuu = p.waktu.strftime('%Y-%m-%d')
            x = p.waktu + datetime.timedelta(days=1)
            x = x.strftime('%Y-%m-%d')
            x = datetime.datetime.strptime(x, '%Y-%m-%d').date()
            e.append(x)
        b=[]
        for a in e:
            wd = WadukDaily.select(AND(WadukDaily.q.waktu==a, WadukDaily.q.pos==poss))
            try:
                wdch = wd[0].curahhujan
            except IndexError:
                wdch = None
            b.append(wdch)
        z=[]
        for b,d in zip (rs2, b):
            z.append((b,d))
        print z
        return render.adm.bendungan.FormBlangko.formb2_2.Form_B2_2({'tanggal': tgal, 'bd':poss, 'periodic': z})

class FormB3:
    @login_required
    def GET(self, table_nama):
        inp = web.input()
        ordering ='waktu' or '-waktu'
        try:
            poss = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_nama][0]
        except:
            return web.notfound()
        webinputt = web.input(sampling=str(datetime.date.today()))
        tgal = datetime.datetime.strptime(webinputt.sampling, '%Y-%m-%d').date()

        if tgal.year == datetime.date.today().year and tgal.month == datetime.date.today().month and tgal.day == datetime.date.today().day:
            rss = [r for r in BendungFormB3.select(BendungFormB3.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]

        else:
            rss = [r for r in BendungFormB3.select(BendungFormB3.q.bendungan==poss).orderBy(ordering) if r.waktu.month == tgal.month and r.waktu.year == tgal.year and r.waktu.day == tgal.day]


        return render.adm.bendungan.FormBlangko.formb3.Form_B3({'tanggal': tgal, 'bd':poss, 'periodic': rss})

    @login_required
    # @csrf_protected
    def POST(self, table_name):       
        try:
            pos = [a for a in AgentBd.select(AgentBd.q.AgentType==3) if a.table_name == table_name][0]
            bendungan_id = pos.id
        except IndexError:
            return web.notfound()
        inp = web.input()
        fields = 'waktu,mslah_pbendung,tndkan_pbendung,mslah_lerhulubend,tndkan_lerhulubend,mslah_lerhilirbend,tndkan_lerhilirbend,mslah_instrumentasi,tndkan_instrumentasi,mslah_pmbuang,tndkan_pmbuang,mslah_tumpuan,tndkan_tumpuan,mslah_plimpah,tndkan_plimpah,mslah_inlet,tndkan_inlet,mslah_hidromekanik,tndkan_hidromekanik,mslah_outlet,tndkan_outlet,mslah_waduk,tndkan_waduk,mslah_bagsungai,tndkan_bagsungai,mslah_lain,tndkan_lain'.split(',')

        # memeriksa apakah record pada Pos dan waktu(tgl) sudah ada pada tabel 'bendung_form'
        try:
            form = BendungFormB3.select(AND(BendungFormB3.q.waktu==to_date(inp.waktu), BendungFormB3.q.bendungan==bendungan_id))[0]
            is_form_exist = True
        except IndexError:
            form = None
            is_form_exist = False


        objj = {}
        for f in fields:
            if inp.get(f):

                if f == 'waktu':
                    nilai = to_date(inp.waktu)
                else:
                    nilai = inp.get(f)
                
            else:
                nilai = None
            objj.update({f: nilai})
        objj.update({'bendunganID':bendungan_id, 'waktu': to_date(inp.waktu)})
        if not is_form_exist:
            form = BendungFormB3(**objj)
        else:
            form.set(**objj)
        bf = form.sqlmeta.asDict()
        waktuu = bf['waktu']
        waktuu = waktuu.strftime('%Y-%m-%d')

        return web.redirect('/adm/bendungan/' + table_name + '/FormBlangko/formB3?sampling='+waktuu, absolute=True)

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
    #print export_rtow(81)
    print import_rtow('/tmp/bd_ngancar.csv')
    #print get_tma_daily_on_pos('jarum', datetime.date(2016, 4, 24))
