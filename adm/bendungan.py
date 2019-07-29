# Data Management
import os
import sys
import datetime
import calendar
import json
sys.path.append('../')
from memory_profiler import profile

import base64

import web
from sqlobject import OR, AND, SQLObjectNotFound
from sqlobject.sqlbuilder import *

from models import AgentBd, conn, WadukDaily,TinggiMukaAir, BendungAlert
from models import NO_VNOTCH, FAIL_VNOTCH, FOTO_PATH, PETUGAS_CHOICES
from models import Kegiatan, Foto, BENDUNGAN_DICT
from models import Kerusakan, Asset, Tanggapan1, Tanggapan2

from helper import to_date, json_serializer
from keamanan import app_keamanan

urls = (
    '', 'BdIndex',
    '/update', 'BdUpdate',
    '/teknis', 'BdIndexTeknis',
    '/rotw', 'BdIndexRotw',
    '/rotw/csv', 'BdRtowImport',
    '/kegiatan', 'BdKegiatanIndex',
    '/asset','BdAdminKerusakan',
    '/(\w+\.*\-*\w+)/keamanan', 'BdKeamanan',
    '/(\w+\.*\-*\w+)', 'BdShow',
    '/(\w+\.*\-*\w+)/rtow/export', 'BdRtowExport',
    '/(\w+\.*\-*\w+)/rtow/import', 'BdRtowImport',
    '/(\w+\.*\-*\w+)/add', 'BdPeriodicAdd',
    '/(\w+\.*\-*\w+)/kegiatan', 'BdKegiatan',
    '/(\w+\.*\-*\w+)/kegiatan/(\d+)', 'BdKegiatan',
    '/(\w+\.*\-*\w+)/asset', 'BdAsset',
    '/(\w+\.*\-*\w+)/kerusakan', 'BdKerusakan',
    '/(\w+\.*\-*\w+)/kerusakan/(\d+)', 'BdKerusakan',
    '//tanggapan1','BdTanggapan1',
    '//tanggapan2','BdTanggapan2',
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


globals = {'session': session, 'csrf_token': csrf_token}
render = web.template.render('templates/', base='base_adm', globals=globals)
render_peltek = web.template.render('templates/', base='base_peltek', globals=globals)
render_plain = web.template.render('templates/', base='', globals=globals)

class BdKeamanan:
    @login_required
    @profile
    def GET(self, table_name):
        inp = web.input()
        ordering = '-waktu'
        try:
            pos = AgentBd.get(BENDUNGAN_DICT.get(table_name))
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
        msg = ''
        if session.has_key('err'):
            msg = session.pop('err')
        return render.adm.bendungan.keamanan({'bd': pos, 'periodic': rs,
            'tanggal': tg, 'msg': msg})


class BdKerusakan: 
    def GET(self, table_name, id=None):
        kerusakan_id = id
        if kerusakan_id:
            return "Detail kerusakan dengan ID "+id
        else:
            try:
                pos = AgentBd.get(BENDUNGAN_DICT.get(table_name))
            except:
                return web.notfound()
            tgl = datetime.date.today()
            kerusakan = Kerusakan.select(Kerusakan.q.table_name==table_name)
            return render.adm.bendungan.kerusakan.index({'pos': pos, 'tgl': tgl, 'kerusakan' : kerusakan})

    def POST(self, table_name):
        inp = web.input()
        asset_id = inp.get('asset_id')
        uraian_kerusakan = inp.get('uraian_kerusakan')
        kategori = inp.get('kategori')
        kerusakan_db = Kerusakan(asset=int(asset_id),table_name = table_name, cuser = session.get('username'), uraian = uraian_kerusakan, kategori = kategori)

        filename = FOTO_PATH +table_name + '_kerusakan_' +str(kerusakan_db.id)+ '_' + inp.get('filename').lower()

        if not os.path.isdir(FOTO_PATH):
            os.mkdir(FOTO_PATH)
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(inp.get('data').split(',')[1]))

        foto = Foto(filepath=filename, keterangan=inp.get('uraian_kerusakan'),
                    obj_type='kerusakan', obj_id=kerusakan_db.id, cuser=session.get('username'))

        kerusakan_db.foto = foto
      
        return "ok"


class BdAdminKerusakan:
    @login_required
    @admin_required
    def GET(self):
        tgl = datetime.date.today()
        kerusakan = Kerusakan.select()
        return render.adm.bendungan.kerusakan.admin({'tgl': tgl, 'kerusakan' : kerusakan})


class BdTanggapan1:
    @login_required
    @admin_required
    def POST(self):
        inp = web.input()
        kerusakan_id = inp.get('kerusakan_id')
        kategori = inp.get('kategori')
        uraian = inp.get('uraian')
        lanjut = inp.get('lanjut')
        if lanjut == '0':
            lanjut = False
        elif lanjut == '1':
            lanjut = True
        Tanggapan1(kerusakan=int(kerusakan_id),uraian=uraian,lanjut=lanjut,kategori=kategori,cuser=session.get('username'))
        return "ok"

class BdTanggapan2:
    @login_required
    @admin_required
    def GET(self):
        tgl = datetime.date.today()
        tanggapan1 = Tanggapan1.select(Tanggapan1.q.lanjut == True)
        return render_peltek.adm.bendungan.kerusakan.tanggapan2({'tgl': tgl,'tanggapan1':tanggapan1})

    def POST(self):
        inp = web.input()
        t1_id = inp.get('tanggapan1_id')
        uraian = inp.get('uraian-tanggapan2')
        if inp.get('nilai'):
            nilai = inp.get('nilai')
        else:
            nilai = None
        if inp.get('tgl-laksana'):
            tgl_laksana = inp.get('tgl-laksana')
        else:
            tgl_laksana = None
        Tanggapan2(tanggapan1=int(t1_id),uraian=uraian,nilai=nilai,pelaksanaan=tgl_laksana,cuser=session.get('username'))
        return web.redirect('')

class BdAsset:
    def GET(self, table_name):
        try:
            pos = AgentBd.get(BENDUNGAN_DICT.get(table_name))
        except:
            return web.notfound()
        tgl = datetime.date.today()
        asset = Asset.select(Asset.q.table_name==table_name)

        data = open('asset.csv').readlines()
        flist = []
        for item in data:
            l = item.strip().split("_")
            s = str(l[0]+" > "+l[1])
            flist.append(s)

        fflist = []
        for kategori in flist:
            if kategori not in fflist:
                fflist.append(kategori)

        return render.adm.bendungan.asset.index({'pos': pos, 'tgl': tgl, 'asset' : asset,'data':fflist})

    def POST(self, table_name):
        inp = web.input()
        state = inp.get('state')
        if state == 'hapus':
            asset_id = inp.get('asset_id')
            delete = Delete('asset',where='id='+asset_id)
            query = conn.sqlrepr(delete)
            conn.query(query)
            return "ok"
        elif state == 'tambah':
            nama = inp.get('nama_asset_add')
            kategori = inp.get('kategori-asset')
            merk = inp.get('merk')
            model = inp.get('model')
            bmn = inp.get('bmn')
            Asset(table_name=table_name,cuser=session.get('username'),kategori=kategori+'_'+nama,nama=nama,merk=merk,model=model,bmn=bmn)
            return web.redirect('asset')

        else:
            try:
                asset = Asset.get(int(inp.get('pk')))
                asset.set(**{inp.get('name'):inp.get('value')})

            except SQLObjectNotFound:
                return web.notfound()
        web.header('Content-Type', 'application/json')
        return json.dumps({"Ok": "true"})

class BdKegiatanIndex:
    def GET(self):
        bdgs = [k for k,v in BENDUNGAN_DICT.items()]
        return render.adm.bendungan.kegiatan_index(bdgs)


class BdKegiatan:
    def GET(self, table_name, id=None):
        inp = web.input()
        tgl = to_date(inp.get('sampling',
                              datetime.date.today().strftime('%Y-%m-%d')))
        bd_id = BENDUNGAN_DICT.get(table_name)
        pos = AgentBd.get(int(bd_id))
        if id:
            kegiatan = Kegiatan.get(int(id))
            return render.adm.bendungan.kegiatan_show(kegiatan=kegiatan)
        if inp.get('sampling') and inp.get('paper'):
            sql = "SELECT k.petugas, k.uraian, f.filepath FROM \
                    kegiatan k, foto f \
                    WHERE f.obj_type='kegiatan' AND k.id=f.obj_id AND DATE(k.sampling)='%s' \
                    AND k.table_name='%s'" % (tgl.strftime('%Y-%m-%d'), table_name)
            rst = [{'p': r[0], 'u': r[1], 'f': r[2]} for r in conn.queryAll(sql)]
            return render_plain.adm.bendungan.kegiatan_paper(pos, tgl, rst)

        sql = "SELECT k.petugas, DATE(k.sampling), k.uraian, k.id \
                FROM kegiatan k, foto f \
                WHERE f.obj_type='kegiatan' AND k.id=f.obj_id \
                AND k.table_name='%s' AND YEAR(k.sampling)=%s \
                AND MONTH(k.sampling)=%s \
                ORDER BY k.sampling DESC" % (table_name, tgl.year, tgl.month)
        rows = [r for r in conn.queryAll(sql)]
        tgls = list(set(r[1] for r in rows))
        print rows 
        result = dict([(t, {}) for t in tgls])
        for r in rows:
            if r[0] in result[r[1]]:
                result[r[1]][r[0]].append({'uraian': r[2], 'kid': r[3]})
            else:
                result[r[1]][r[0]] = [{'uraian': r[2], 'kid': r[3]}]
        return render.adm.bendungan.kegiatan(dict(pos=pos,
                                              petugas=PETUGAS_CHOICES,
                                              kegiatan=result, tgl=tgl))

    def POST(self, table_name):
        inp = web.input()
        keg = Kegiatan(table_name=table_name, 
                       petugas=inp.get('petugas'), uraian=inp.get('uraian'), 
                       sampling=to_date(inp.get('waktu')),
                      cuser=session.username)
        filename = FOTO_PATH + '/' +table_name + '_kegiatan_' +str(keg.id)+ '_' + inp.get('filename').lower()
        if not os.path.isdir(FOTO_PATH):
            os.mkdir(FOTO_PATH)
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(inp.get('data').split(',')[1]))
        foto = Foto(filepath=filename, keterangan=inp.get('uraian'),
                    obj_type='kegiatan', obj_id=keg.id, cuser=session.get('username'))
        keg.foto = foto
        web.header('Content-Type', 'application/json')
        return json.dumps({"Ok": "true"})


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

class BdShow:
    @login_required
    @profile
    def GET(self, table_name):
        inp = web.input()
        csv = inp.get('csv')
        ordering = csv and 'waktu' or '-waktu'
        try:
            pos = AgentBd.get(BENDUNGAN_DICT.get(table_name))
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
