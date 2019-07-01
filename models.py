import datetime

from sqlobject import *
from web.utils import commify
import time
import datetime

from helper import Struct
from common_data import BENDUNGAN_DICT, CAUSE_TABLE, NO_VNOTCH, FAIL_VNOTCH

DB_USER = 'root'
DB_NAME = 'upbbsolodb'
DB_PWD = ''

MONGO_PORT = 27017
MONGO_HOST = 'localhost'

FOTO_PATH = 'static/img/foto/'

try:
    from local_settings import *
except:
    pass

cs = "mysql://%s:%s@localhost/%s?debug=0" % (DB_USER, DB_PWD, DB_NAME)
conn = connectionForURI(cs)
sqlhub.processConnection = conn

KLIMATOLOGI = 1.0
HIDROLOGI = 2.0
BENDUNGAN = 3.0

POS_TYPE = {0.0: 'Keduanya', 1.0: 'Klimatologi', 2.0: 'Hidrologi',
            3.0: 'Bendungan'}

WILAYAH = {1: 'Hulu', 2: 'Madiun', 3: 'Hilir'}
BSOLO = 'B. Solo'

ARR = (('klaten', 'pabelan', 'tawangmangu', 'karangpandan', 'wonogiri', 'jurug',
        'rejoso', 'tritis'),
       ('ngawi', 'waduk_notopuro',  'sooko'),
       ('nglirip_dam', 'cepu', 'lamongan', 'waduk_gondang', 'bojonegoro'))
AWLR = (('colo_weir', 'jurug', 'jarum', 'wonogiri_dam', 'tangen_bridge'),
        ('sekayu', 'ketonggo_bridge'),
        ('napel', 'cepu', 'bojonegoro_awlr', 'babat_barrage'))
BSOLO2 = ('rejoso', 'nglirip_dam', 'wonogiri_dam', 'tangen_brigde', 'colo_weir',
          'babat_barrage')
ONLIMO_STATION_MAP = {'jurug': 1, 'pabelan': 2, 'cepu': 3}


class Embung(SQLObject):
    nama = StringCol(length=35)
    jenis = StringCol(length=1, default='b') # 'a': Air Baku, 'b': BPAir
    desa = StringCol(length=35)
    kec = StringCol(length=35)
    kab = StringCol(length=35)
    ll = StringCol(length=50)
    sumber_air = StringCol(length=35)
    tampungan = FloatCol(notNone=False) # dalam Meter Kubik
    debit = FloatCol(notNone=False) # dalam Liter / detik
    pipa_transmisi = FloatCol(notNone=False) # dalam Meter
    saluran_traansmisi = FloatCol(notNone=False) # dalam Meter
    air_baku = IntCol(notNone=False) # Banyaknya KK terlayani
    irigasi = FloatCol(notNone=False) # dalam Hektar
    cuser = StringCol(length=35)
    muser = StringCol(length=35, default=None)
    cdate = DateTimeCol(default=datetime.datetime.utcnow)
    mdate = DateTimeCol(default=None)


class Foto(SQLObject):
    filepath = StringCol(length=100)
    keterangan = StringCol(length=255, notNone=False)
    obj_type = StringCol(length=20) # nama class
    obj_id = IntCol()
    cuser = StringCol(length=35)
    muser = StringCol(length=35, default=None)
    cdate = DateTimeCol(default=datetime.datetime.utcnow)
    mdate = DateTimeCol(default=None)

PETUGAS_CHOICES = "koordinator_keamanan_pemantauan_operasi_pemeliharaan".split('_')
KEGIATAN_CHOICES = ('koordinasi','keamanan','pemantauan','operasi','pemeliharaan')

class Kegiatan(SQLObject):
    foto = ForeignKey('Foto')
    table_name = StringCol(length=35) # nama bendungan
    sampling = DateTimeCol()
    petugas = StringCol(length=35) # lihat PERSONIL_CHOICES
    uraian = StringCol()
    cuser = StringCol(length=35)
    muser = StringCol(length=35, default=None)
    cdate = DateTimeCol(default=datetime.datetime.utcnow)
    mdate = DateTimeCol(default=None)


class RequestResponse(SQLObject):
    ReqDate = DateCol(dbName='ReqDate')
    ReqTime = TimeCol(dbName='ReqTime')
    ReqPhone = StringCol(length=25, dbName='ReqPhone')
    ReqMessage = StringCol(length=180, dbName='ReqMessage')
    ReqID = StringCol(length=25, dbName='ReqID')

    @property
    def AgentName(self):
        try:
            return Agent.select(
                Agent.q.AgentPhone == self.ReqPhone)[0].AgentName
        except:
            return ''

    class sqlmeta:
        idName = 'ReqID'
        table = 'requestresponse'
        idType = str


class AgentBd(SQLObject):
    AgentId = StringCol(length=25, alternateID=True, dbName='AgentID')
    AgentName = StringCol(length=25, dbName='AgentName', unique=True)
    AgentType = FloatCol(dbName='AgentType')
    TippingFactor = FloatCol(default=None, dbName='TippingFactor')
    ll = StringCol()
    prima_id = StringCol(length=12) # ID Logger prima, mis: '1711-2'
    logger_model = IntCol() # GPA, SCU, Cuwin, BPPT, Prima
    cname = StringCol(length=50) # Common Name
    siaga1 = FloatCol(dbName='Normal')
    siaga2 = FloatCol(dbName='SiagaLower')
    siaga3 = FloatCol(dbName='SiagaUpper')
    siaga4 = FloatCol(dbName='CriticalLower')
    sedimen = FloatCol(dbName='Sedimen')
    bts_elev_awas = FloatCol(dbName='bts_elev_awas')
    bts_elev_siaga = FloatCol(dbName='bts_elev_siaga')
    bts_elev_waspada = FloatCol(dbName='bts_elev_waspada')
    wilayah = IntCol(default=1)
    kab = StringCol(length=35) # Kabupaten / Kota
    lbi = FloatCol(default=0, notNone=False)  # Luas Baku Irigasi, utk bendungan
    volume = FloatCol(default=0, notNone=False)  # volume untuk bendungan
    lengkung_kapasitas = StringCol(length=1024, default=None)  # data lengkung
    expose = BoolCol(default=True)
    elev_puncak = FloatCol()
    batas_rembesan = FloatCol()
    vn_tin1_limit = FloatCol()
    vn_tin2_limit = FloatCol()
    vn_tin3_limit = FloatCol()
    vn_q1_limit = FloatCol()
    vn_q2_limit = FloatCol()
    vn_q3_limit = FloatCol()
    vn1_panjang_saluran = FloatCol()
    vn2_panjang_saluran = FloatCol()
    vn3_panjang_saluran = FloatCol()
    pie1a_elev_dasar_pipa = IntCol()
    pie1b_elev_dasar_pipa = IntCol()
    pie1c_elev_dasar_pipa = IntCol()
    pie2a_elev_dasar_pipa = IntCol()
    pie2b_elev_dasar_pipa = IntCol()
    pie2c_elev_dasar_pipa = IntCol()
    pie3a_elev_dasar_pipa = IntCol()
    pie3b_elev_dasar_pipa = IntCol()
    pie3c_elev_dasar_pipa = IntCol()
    pie4a_elev_dasar_pipa = IntCol()
    pie4b_elev_dasar_pipa = IntCol()
    pie4c_elev_dasar_pipa = IntCol()
    pie5a_elev_dasar_pipa = IntCol()
    pie5b_elev_dasar_pipa = IntCol()
    pie5c_elev_dasar_pipa = IntCol()
    pie1a_panjang_pipa = IntCol()
    pie1b_panjang_pipa = IntCol()
    pie1c_panjang_pipa = IntCol()
    pie2a_panjang_pipa = IntCol()
    pie2b_panjang_pipa = IntCol()
    pie2c_panjang_pipa = IntCol()
    pie3a_panjang_pipa = IntCol()
    pie3b_panjang_pipa = IntCol()
    pie3c_panjang_pipa = IntCol()
    pie4a_panjang_pipa = IntCol()
    pie4b_panjang_pipa = IntCol()
    pie4c_panjang_pipa = IntCol()
    pie5a_panjang_pipa = IntCol()
    pie5b_panjang_pipa = IntCol()
    pie5c_panjang_pipa = IntCol()
    pie1a_batas_tek_pori = FloatCol()
    pie1b_batas_tek_pori = FloatCol()
    pie1c_batas_tek_pori = FloatCol()
    pie2a_batas_tek_pori = FloatCol()
    pie2b_batas_tek_pori = FloatCol()
    pie2c_batas_tek_pori = FloatCol()
    pie3a_batas_tek_pori = FloatCol()
    pie3b_batas_tek_pori = FloatCol()
    pie3c_batas_tek_pori = FloatCol()
    pie4a_batas_tek_pori = FloatCol()
    pie4b_batas_tek_pori = FloatCol()
    pie4c_batas_tek_pori = FloatCol()
    pie5a_batas_tek_pori = FloatCol()
    pie5b_batas_tek_pori = FloatCol()
    pie5c_batas_tek_pori = FloatCol()
 
    def get_status_rembesan1(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q1
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]

    def get_status_rembesan2(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q2
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]
    def get_status_rembesan3(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q3
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]


    def lengkung(self):
        return self.lengkung_kapasitas.split('\n')


    class sqlmeta:
        idName = 'AgentID'
        idType = str
        table = 'agent'

    @property
    def table_name(self):
        return self.AgentName.lower().replace('.', '_').replace(' ', '_')

class AgentTma(SQLObject):
    AgentId = StringCol(length=25, alternateID=True, dbName='AgentID')
    AgentName = StringCol(length=25, dbName='AgentName', unique=True)
    AgentType = FloatCol(dbName='AgentType')
    ll = StringCol()
    DPL = FloatCol(dbName='DPL')
    prima_id = StringCol(length=12) # ID Logger prima, mis: '1711-2'
    logger_model = IntCol() # GPA, SCU, Cuwin, BPPT, Prima
    cname = StringCol(length=50) # Common Name

    class sqlmeta:
        idName = 'AgentID'
        table = 'agent'

    @property
    def table_name(self):
        return self.AgentName.lower().replace('.', '_').replace(' ', '_')

class AgentCh(SQLObject):
    AgentId = StringCol(length=25, alternateID=True, dbName='AgentID')
    AgentName = StringCol(length=25, dbName='AgentName', unique=True)
    AgentType = FloatCol(dbName='AgentType')
    TippingFactor = FloatCol(default=None, dbName='TippingFactor')
    ll = StringCol()
    prima_id = StringCol(length=12) # ID Logger prima, mis: '1711-2'
    logger_model = IntCol() # GPA, SCU, Cuwin, BPPT, Prima
    cname = StringCol(length=50) # Common Name
    expose = BoolCol(default=True)
    wilayah = IntCol(default=1)
    kab = StringCol(length=35) # Kabupaten / Kota

    class sqlmeta:
        idName = 'AgentID'
        table = 'agent'

    @property
    def table_name(self):
        return self.AgentName.lower().replace('.', '_').replace(' ', '_')

    def get_segmented_rain(self, tanggal=datetime.date.today()):
        '''
        Menghitung curah hujan 3 segment: pagi(7-12), sore(12-18), malam
        @rows = (Rain, SamplingDate, SamplingTime)
        '''
        if self.AgentType == 2:
            return {}
        result = self._connection.queryAll("SELECT Rain * %s AS Rain, SamplingDate, SamplingTime \
            FROM %s WHERE SamplingDate BETWEEN '%s' AND '%s' \
            ORDER BY SamplingDate, SamplingTime" % (
                self.TippingFactor,
                self.table_name, str(tanggal),
                str(tanggal + datetime.timedelta(days=1))))
        if not result:
            data_pagi = data_sore = data_malam = data_tmalam = []
            pagi = sore = malam = tmalam = 0
        else:
            # 25200 = 07:00
            # 46800 = 13:00
            # 68400 = 19:00
            # 3600 = 01:00
            data_pagi = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds >= 25200) and (
                    r[1] == tanggal and r[2].seconds <= 46800)]
            pagi = sum(data_pagi)

            data_sore = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds > 46800) and (
                    r[1] == tanggal and r[2].seconds <= 68400)]
            sore = sum(data_sore)

            data_malam = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds > 68400) or (
                    r[1] == tanggal+datetime.timedelta(days=1) and
                    r[2].seconds < 3600)]
            malam = sum(data_malam)
            data_tmalam = [r[0] or 0 for r in result if (
                r[1] == tanggal+datetime.timedelta(days=1) and r[2].seconds > 3600) and (r[1] == tanggal+datetime.timedelta(days=1) and r[2].seconds <= 25200)]
            tmalam = sum(data_tmalam)
        rst = self._connection.queryAll("SELECT manual, mtime_manual, \
                                        origin_manual FROM curahhujan \
                                        WHERE agent_id=%s AND \
            waktu='%s'" % (self.AgentId, str(tanggal)))
        if rst:
            manual = rst[0][0]
            mtime_manual = rst[0][1]
            origin_manual = rst[0][2]
        else:
            manual = None
            mtime_manual = None
            origin_manual = None
        # Kategori hujan
        kat = ("Sangat Ringan", "Ringan", "Sedang", "Lebat", "Sangat Lebat")
        idx = 0
        if 5 > manual < 20:
            idx = 1
        elif 20 > manual < 50:
            idx = 2
        elif 50 > manual < 100:
            idx = 3
        elif manual > 100:
            idx = 4
        result = {'agent_id': self.AgentId, 'waktu': tanggal, 'pagi': pagi,
                  'sore': sore, 'malam': malam, 'tmalam': tmalam,
                  'total': sum(filter(None, [pagi, sore, malam, tmalam])),
                  'manual': manual, 'mtime_manual': mtime_manual,
                  'kategori': kat[idx], 'num_t': len(data_pagi) + len(data_sore) + len(data_malam) + len(data_tmalam),
                  'origin_manual': origin_manual}
        return result

    def get_aday_ch(self, tanggal=datetime.date.today()):
        if self.AgentType not in (0, 1):
            return []
        dari = datetime.datetime.combine(tanggal, (datetime.datetime.min + datetime.timedelta(hours=7)).time())
        jams = []
        for j in range(0, 24):
            jams.append(dari + datetime.timedelta(hours=j))
        hingga = dari + datetime.timedelta(hours=24)
        sql = "SELECT SamplingDate, HOUR(SamplingTime), \
                SUM(Rain * %(tipping_factor)s) FROM %(table_name)s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN \
                '%(dari)s' AND '%(hingga)s' \
                GROUP BY SamplingDate, HOUR(SamplingTime)" % dict(tipping_factor=self.TippingFactor,
                        table_name=self.table_name, dari=dari, hingga=hingga)
        print sql
        def timedelta_to_time(td):
            secs = td.seconds
            hour = int(secs / 3600)
            minute = int(secs / 60) % 60
            return datetime.time(hour, minute, 0)
        return [(datetime.datetime.combine(r[0], timedelta_to_time(r[1])), r[2]) for r in self._connection.queryAll(sql)]


    def get_ch(self, tahun=datetime.date.today().year, bulan=''):
        '''
        Mengambil data Curah hujan selama setahun
        '''
        if self.AgentType == 2:  # 1.0 = Tinggi Muka Air
            return ()
        SEBELUM = 2
        tahun = int(tahun)
        if bulan and int(bulan) in range(1, 12):
            sql = "SELECT DAY(waktu), SUM(pagi+sore+malam) AS telemetri, manual \
                    FROM curahhujan \
                WHERE agent_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s \
                GROUP BY DAY(waktu);" % (
                    self.AgentId, tahun, bulan)
            return conn.queryAll(sql)

        tahun = ','.join([str(t) for t in range(tahun-SEBELUM, tahun+1)])
        sql = "SELECT waktu, SUM(pagi+sore+malam) AS telemetri, SUM(manual) from curahhujan \
            WHERE agent_id=%s AND YEAR(waktu) IN (%s) \
            GROUP BY YEAR(waktu), MONTH(waktu);" % (self.AgentId, tahun)
        ret = conn.queryAll(sql)
        return ret


class Agent(SQLObject):
    AgentId = StringCol(length=25, alternateID=True, dbName='AgentID')
    AgentName = StringCol(length=25, dbName='AgentName', unique=True)
    AgentType = FloatCol(dbName='AgentType')
    #AgentLocation = StringCol(length=50, dbName='AgentLocation')
    AgentPhone = StringCol(length=25, dbName='AgentPhone')
    DPL = FloatCol(dbName='DPL')
    DAS = StringCol(dbName='DAS')
    TippingFactor = FloatCol(default=None, dbName='TippingFactor')
    #ReportSchedule = FloatCol(dbName='ReportSchedule', default=60.0)
    ll = StringCol()
    siaga1 = FloatCol(dbName='Normal')
    siaga2 = FloatCol(dbName='SiagaLower')
    siaga3 = FloatCol(dbName='SiagaUpper')
    siaga4 = FloatCol(dbName='CriticalLower')
    sedimen = FloatCol(dbName='Sedimen')
    bts_elev_awas = FloatCol(dbName='bts_elev_awas')
    bts_elev_siaga = FloatCol(dbName='bts_elev_siaga')
    bts_elev_waspada = FloatCol(dbName='bts_elev_waspada')
    PRain1 = StringCol(length=25, default=None, dbName='PRain1')
    PRain2 = StringCol(length=25, default=None, dbName='PRain2')
    PRain3 = StringCol(length=25, default=None, dbName='PRain3')
    PRain4 = StringCol(length=25, default=None, dbName='PRain4')
    PWater1 = StringCol(length=25, default=None, dbName='PWater1')
    PWater2 = StringCol(length=25, default=None, dbName='PWater2')
    PWater3 = StringCol(length=25, default=None, dbName='PWater3')
    PWater4 = StringCol(length=25, default=None, dbName='PWater4')
    NRain1 = StringCol(length=25, default=None, dbName='NRain1')
    NRain2 = StringCol(length=25, default=None, dbName='NRain2')
    NRain3 = StringCol(length=25, default=None, dbName='NRain3')
    NRain4 = StringCol(length=25, default=None, dbName='NRain4')
    NWater1 = StringCol(length=25, default=None, dbName='NWater1')
    NWater2 = StringCol(length=25, default=None, dbName='NWater2')
    NWater3 = StringCol(length=25, default=None, dbName='NWater3')
    NWater4 = StringCol(length=25, default=None, dbName='NWater4')
    #RemoteID = StringCol(length=6, default='passwo', dbName='RemoteID')
    #LocationID = StringCol(length=15, default=None, dbName='LocationID')
    #Reference = StringCol(length=6, default='000000', dbName='Reference')
    Offset = IntCol(default=0, dbName='Offset')
    #Sungai = StringCol(length=25, default=None, dbName='Sungai')
    LRain = StringCol(length=25, default=None, dbName='LRain')
    wilayah = IntCol(default=1)
    lbi = FloatCol(default=0, notNone=False)  # Luas Baku Irigasi, utk bendungan
    volume = FloatCol(default=0, notNone=False)  # volume untuk bendungan
    lengkung_kapasitas = StringCol(length=1024, default=None)  # data lengkung
    expose = BoolCol(default=True)
    cname = StringCol(length=50) # Common Name
    kab = StringCol(length=35) # Kabupaten / Kota
    latest_siaga = IntCol(default=0)
    urutan = IntCol()
    tinggi_sonar = IntCol() # jarak sonar ke dasar sungai, dlm CM
    prima_id = StringCol(length=12) # ID Logger prima, mis: '1711-2'
    logger_model = IntCol() # GPA, SCU, Cuwin, BPPT, Prima
    #gates = MultipleJoin('Gate', joinColumn='bendung_id')
    #curahhujans = MultipleJoin('CurahHujan', orderBy=['-waktu'])
    #tmas = MultipleJoin('TinggiMukaAir', orderBy=['-waktu'])
    #daily = MultipleJoin('WadukDaily', joinColumn='pos_id', orderBy=['-waktu'])
    elev_puncak = FloatCol()
    batas_rembesan = FloatCol()
    vn_tin1_limit = FloatCol()
    vn_tin2_limit = FloatCol()
    vn_tin3_limit = FloatCol()
    vn_q1_limit = FloatCol()
    vn_q2_limit = FloatCol()
    vn_q3_limit = FloatCol()
    vn1_panjang_saluran = FloatCol()
    vn2_panjang_saluran = FloatCol()
    vn3_panjang_saluran = FloatCol()
    pie1a_elev_dasar_pipa = IntCol()
    pie1b_elev_dasar_pipa = IntCol()
    pie1c_elev_dasar_pipa = IntCol()
    pie2a_elev_dasar_pipa = IntCol()
    pie2b_elev_dasar_pipa = IntCol()
    pie2c_elev_dasar_pipa = IntCol()
    pie3a_elev_dasar_pipa = IntCol()
    pie3b_elev_dasar_pipa = IntCol()
    pie3c_elev_dasar_pipa = IntCol()
    pie4a_elev_dasar_pipa = IntCol()
    pie4b_elev_dasar_pipa = IntCol()
    pie4c_elev_dasar_pipa = IntCol()
    pie5a_elev_dasar_pipa = IntCol()
    pie5b_elev_dasar_pipa = IntCol()
    pie5c_elev_dasar_pipa = IntCol()
    pie1a_panjang_pipa = IntCol()
    pie1b_panjang_pipa = IntCol()
    pie1c_panjang_pipa = IntCol()
    pie2a_panjang_pipa = IntCol()
    pie2b_panjang_pipa = IntCol()
    pie2c_panjang_pipa = IntCol()
    pie3a_panjang_pipa = IntCol()
    pie3b_panjang_pipa = IntCol()
    pie3c_panjang_pipa = IntCol()
    pie4a_panjang_pipa = IntCol()
    pie4b_panjang_pipa = IntCol()
    pie4c_panjang_pipa = IntCol()
    pie5a_panjang_pipa = IntCol()
    pie5b_panjang_pipa = IntCol()
    pie5c_panjang_pipa = IntCol()
    pie1a_batas_tek_pori = FloatCol()
    pie1b_batas_tek_pori = FloatCol()
    pie1c_batas_tek_pori = FloatCol()
    pie2a_batas_tek_pori = FloatCol()
    pie2b_batas_tek_pori = FloatCol()
    pie2c_batas_tek_pori = FloatCol()
    pie3a_batas_tek_pori = FloatCol()
    pie3b_batas_tek_pori = FloatCol()
    pie3c_batas_tek_pori = FloatCol()
    pie4a_batas_tek_pori = FloatCol()
    pie4b_batas_tek_pori = FloatCol()
    pie4c_batas_tek_pori = FloatCol()
    pie5a_batas_tek_pori = FloatCol()
    pie5b_batas_tek_pori = FloatCol()
    pie5c_batas_tek_pori = FloatCol()
 
    def get_status_rembesan1(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q1
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]
    def get_status_rembesan2(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q2
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]
    def get_status_rembesan3(self, tanggal=datetime.date.today()):
        statuses = "-_Normal_Anomali".split('_')
        ret = 0
        rwaktu = datetime.datetime(tanggal.year, tanggal.month, tanggal.day, 0, 0)
        try:
            rs = [d for d in self.daily if d.waktu == rwaktu][0]
            rembesan = rs.vnotch_q3
        except:
            rembesan = None
        print rembesan, self.batas_rembesan
        if self.batas_rembesan and rembesan:
            ret = (self.batas_rembesan > rembesan) and 1 or 2
        return statuses[ret]


    def lengkung(self):
        return self.lengkung_kapasitas.split('\n')

    def get_scale_elev(self, base=10):
        '''Return list of scalled mab, man, mamin, curr'''
        ret = {'smab': base + (base * 0.1), 'sman': 0,
                'smamin': 0, 'selev': 0}
        ret['sman'] = base / (self.siaga3 - self.siaga4) * (self.normal - self.siaga4)
        return ret


    def get_flows(self, dari=None, hingga=None):
        '''Return tanggal, pintu1..n, spillway, inflow'''
        if self.AgentType != 3.0:
            return []
        if not hingga and type(hingga) is not datetime.date:
            for gate in self.gates:
                try:
                    flow = gate.flows[0]
                    if flow.waktu:
                        if hingga:
                            if hingga < flow.waktu:
                                hingga = flow.waktu
                        else:
                            hingga = flow.waktu
                except IndexError:
                    pass
        if not hingga:
            return []
        dari = hingga - datetime.timedelta(days=30)
        sehari = datetime.timedelta(days=1)
        dates = []
        tgl = dari
        while tgl <= hingga:
            dates.append(tgl)
            tgl += sehari
        inf = {}
        outf = {}
        tma = {}
        ch = {}
        for gate in self.gates:
            flows = Flow.select(AND(Flow.q.gate == gate,
                                  Flow.q.waktu >= dari,
                                  Flow.q.waktu <= hingga))
            for r in flows:
                if gate.io == 'o':
                    outf.update({r.waktu: r.value * r.timed})
                else:
                    inf.update({r.waktu: r.value * r.timed})
        curahhujans = [c for c in self.curahhujans if c.waktu >= dari and c.waktu <= hingga]
        for curahhujan in curahhujans:
            ch.update({curahhujan.waktu: curahhujan.manual or 0})

        tmas = [tm for tm in self.tmas if tm.jam == '07' and
                tm.waktu >= dari and tm.waktu <= hingga]
        for tm in tmas:
            tma.update({tm.waktu: tm.manual})
        return dict(dari=dari, hingga=hingga,
                    dates=dates,
                    flows={'inflow': inf, 'outflow': outf,
                           'curahhujans': ch, 'tmas': tma})

    def get_log_tma(self, dari=None, hingga=datetime.datetime.now()):
        '''Return list of TMA '''
        if not dari:
            dari = hingga - datetime.timedelta(days=3)
            dari = dari.replace(hour=7, minute=0, second=0)
        # DPL dikalikan 100 untuk jadi Centimeter
        sql = "SELECT SamplingDate, SamplingTime, WLevel + " \
            "" + str(self.DPL*100) + " \
            FROM %(table_name)s \
            WHERE CONCAT(SamplingDate, ' ', SamplingTime) \
            BETWEEN '%(dari)s' AND '%(hingga)s' \
            ORDER BY SamplingDate, SamplingTime"
        sql = sql % ({'table_name': self.table_name, 'dari': dari,
                      'hingga': hingga})
        return self._connection.queryAll(sql)

    def get_log(self, dari=None, hingga=datetime.datetime.now(), awlr=True):
        '''Return list of TMA or Hujan
        setiap setengah jam, default rentang 24jam'''
        if not dari:
            dari = hingga - datetime.timedelta(days=14)
            dari = dari.replace(hour=7, minute=0, second=0)
        if awlr:
            # DPL dikalikan 100 untuk jadi Centimeter
            sql = "SELECT SamplingDate, SamplingTime, WLevel + " \
                + str(self.DPL*100) + " \
                FROM %(table_name)s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) \
                BETWEEN '%(dari)s' AND '%(hingga)s' \
                ORDER BY SamplingDate, SamplingTime"

        elif self.AgentType == 1 or self.AgentType == 0:
            # hitung curah hujan
            sql = "SELECT SamplingDate, HOUR(SamplingTime), \
                SUM(Rain * " + str(self.TippingFactor) + ") \
                FROM %(table_name)s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) \
                BETWEEN '%(dari)s' AND '%(hingga)s' \
                GROUP BY SamplingDate, HOUR(SamplingTime) \
                ORDER BY SamplingDate, HOUR(SamplingTime)"
        sql = sql % ({'table_name': self.table_name, 'dari': dari,
                      'hingga': hingga})
        return self._connection.queryAll(sql)

    @property
    def sh(self):
        return (self.siaga1 or 0) + self.DPL

    @property
    def sk(self):
        return (self.siaga2 or 0) + self.DPL

    @property
    def sm(self):
        return (self.siaga3 or 0) + self.DPL

    def get_segmented_klimatologi(self, tanggal=datetime.date.today()):
        '''Return dict
        mulai dari jam 7:00, 24 jam dibagi (segmented) jadi 8 (3 jam),
        data: Suhu, Kelembaban, arah angin, kec. angin, radiasi mthr, penguapan
        table column: Rain1=Batt, Rain2=Arahangin, Rain3=Kec. Angin, Rain4=Radiasi'''
        ret = {'suhu': [], 'kelembaban': [], 'arah_angin': [],
                'kec_angin': [], 'radiasi_mthr': [], 'penguapan': []}
        ONLIMO_CLIMATE = ('pabelan', )
        dari = datetime.datetime.combine(tanggal, (datetime.datetime.min + datetime.timedelta(hours=7)).time())
        hingga = dari + datetime.timedelta(days=1)
        sql = "SELECT SamplingDate, SamplingTime, Temperature, Humidity, Rain1*0.01, Rain2*0.01, Rain3*0.1, Rain4*0.1 \
                FROM %s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN '%s' AND '%s' \
                ORDER BY SamplingDate, SamplingTime" % (self.table_name, str(dari), str(hingga))
        if self.table_name in ONLIMO_CLIMATE:
            sql = "SELECT SamplingDate, SamplingTime, Temperature, Humidity, Rain1, Rain2, Rain3, Rain4 \
                    FROM %s \
                    WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN '%s' AND '%s' \
                    ORDER BY SamplingDate, SamplingTime" % (self.table_name, str(dari), str(hingga))
        # kolom jam 7, 10, 13, 16, 19, 21, 2, 4
        kols = [25200, 36000, 46800, 57600, 68400, 79200, 7200, 14400]
        rst = self._connection.queryAll(sql)
        dict_result = dict([(r[1].seconds, list(r)) for r in rst])
        jarak_data = 10 # menit
        for k in kols:
            data = dict_result.get(k, [])
            if not data:
                # Mundurkan jamnya bertahap
                detik = int(k)
                i = 1
                while i > 2:
                    i += 1
                    detik -= jarak_data * 60
                    data = dict_result.get(detik, [])
                    if data:
                        break
            if data:
                ret['suhu'].append(data[2])
                ret['kelembaban'].append(data[3])
                ret['arah_angin'].append(data[4])
                ret['kec_angin'].append(data[-2])
                ret['radiasi_mthr'].append(data[-1])
            else:
                ret['suhu'].append(None)
                ret['kelembaban'].append(None)
                ret['arah_angin'].append(None)
                ret['kec_angin'].append(None)
                ret['radiasi_mthr'].append(None)
        return ret

    def get_aday_ch(self, tanggal=datetime.date.today()):
        if self.AgentType not in (0, 1):
            return []
        dari = datetime.datetime.combine(tanggal, (datetime.datetime.min + datetime.timedelta(hours=7)).time())
        jams = []
        for j in range(0, 24):
            jams.append(dari + datetime.timedelta(hours=j))
        hingga = dari + datetime.timedelta(hours=24)
        sql = "SELECT SamplingDate, HOUR(SamplingTime), \
                SUM(Rain * %(tipping_factor)s) FROM %(table_name)s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN \
                '%(dari)s' AND '%(hingga)s' \
                GROUP BY SamplingDate, HOUR(SamplingTime)" % dict(tipping_factor=self.TippingFactor,
                        table_name=self.table_name, dari=dari, hingga=hingga)
        print sql
        def timedelta_to_time(td):
            secs = td.seconds
            hour = int(secs / 3600)
            minute = int(secs / 60) % 60
            return datetime.time(hour, minute, 0)
        return [(datetime.datetime.combine(r[0], timedelta_to_time(r[1])), r[2]) for r in self._connection.queryAll(sql)]

    def get_aday_klimatologi(self, tanggal=datetime.date.today()):
        '''Return dict
        mulai dari jam 7:00, 24 jam dibagi (segmented) jadi 8 (3 jam),
        data: Suhu, Kelembaban,arah angin, kec. angin, radiasi mthr, penguapan
        table column: Rain1=Batt, Rain2=Arahangin, Rain3=Kec. Angin, Rain4=Radiasi'''
        ONLIMO_CLIMATE = ('pabelan', )
        ret = {'sampling': [],
                'suhu': [], 'kelembaban': [], 'arah_angin': [],
                'kec_angin': [], 'radiasi_mthr': [], 'penguapan': []}
        dari = datetime.datetime.combine(tanggal, (datetime.datetime.min + datetime.timedelta(hours=7)).time())
        hingga = dari + datetime.timedelta(days=1)
        sql = "SELECT SamplingDate, SamplingTime, Temperature, Humidity, Rain1*0.01, Rain2*0.01, Rain3*0.1, Rain4*0.1 \
                FROM %s \
                WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN '%s' AND '%s' \
                ORDER BY SamplingDate, SamplingTime" % (self.table_name, str(dari), str(hingga))
        if self.table_name in ONLIMO_CLIMATE:
            sql = "SELECT SamplingDate, SamplingTime, Temperature, Humidity, Rain1, Rain2, Rain3, Rain4 \
                    FROM %s \
                    WHERE CONCAT(SamplingDate, ' ', SamplingTime) BETWEEN '%s' AND '%s' \
                    ORDER BY SamplingDate, SamplingTime" % (self.table_name, str(dari), str(hingga))
        rst = self._connection.queryAll(sql)
        for r in rst:
            ret['sampling'].append(str(r[0])+ " " + str(r[1]))
            ret['suhu'].append(r[2])
            ret['kelembaban'].append(r[3])
            ret['arah_angin'].append(r[4])
            ret['kec_angin'].append(r[-2])
            ret['radiasi_mthr'].append(r[-1])
        return ret


    def get_segmented_tma_bendungan(self, tanggal=datetime.date.today()):
        '''
        mengambil data WL (Tinggi Muka) Bendungan, default hari ini
        '''
        if self.AgentType != 3:
            return {}

        rst = TinggiMukaAir.selectBy(agent=self, waktu=tanggal)
        pagi = Struct(
            **dict(manual=None, mtime=None, telemetri=None, ttime=None))
        siang = Struct(
            **dict(manual=None, mtime=None, telemetri=None, ttime=None))
        sore = Struct(
            **dict(manual=None, mtime=None, telemetri=None, ttime=None))
        for r in rst:
            if r.jam.endswith('7') or r.jam.endswith('6'):
                pagi = Struct(**dict(manual=r.manual,
                                     mtime=r.mtime,
                                     telemetri=None, ttime=None))
            elif r.jam == '12':
                siang = Struct(**dict(manual=r.manual,
                                      mtime=r.mtime,
                                      telemetri=None, ttime=None))
            elif r.jam == '18':
                sore = Struct(**dict(manual=r.manual,
                                     mtime=r.mtime,
                                     telemetri=None, ttime=None))

#--------------------menampilkan volume ADM per jam (6,12,18)--------------------

        rst_1 = WadukDaily.selectBy(pos=self, waktu=tanggal)
        vol_jam = None

        if pagi.manual:
            latest = pagi.manual
            for r in rst_1 :
                vol_jam = commify('%.3f' % ((r.vol6 or 0)/1000000.0))

        if siang.manual:
            latest = siang.manual
            for r in rst_1 :
                vol_jam = commify('%.3f' % ((r.vol12 or 0)/1000000.0))

        if sore.manual:
            latest = sore.manual
            for r in rst_1 :
                vol_jam = commify('%.3f' % ((r.vol18 or 0)/1000000.0))
#----------------------------------------------------------------------------------

        latest = None
        if sore.manual:
            latest = sore.manual
        elif siang.manual:
            latest = siang.manual
        elif pagi.manual:
            latest = pagi.manual
        kondisi = 'normal'
        if latest > self.siaga3:
            kondisi = 'limpas'
        elif latest < self.siaga4:
            kondisi = 'defisit'
        if not latest:
            kondisi = '-'

        try:
            kap_series = [map(float, l.split('\t'))
                          for l in self.lengkung_kapasitas.split('\n')
                          if '\t' in l]
        except:
            kap_series = []

        kapasitas = None
        p1 = p2 = None
        if latest:
            ukur_elevasi = latest
            try:
                p1 = min(kap_series, key=lambda x: abs(x[0] - ukur_elevasi))[0:2]

                p2 = kap_series[kap_series.index(p1) + 1][0:2]
                x1, y1, x2, y2 = p1[1], p1[0], p2[1], p2[0]
                kapasitas = x1 + (ukur_elevasi - y1) / (y2 - y1) * (x2 - x1)
                if kapasitas < 0:
                    kapasitas = 0
                    #kondisi = 'defisit'
            except:
                pass
        if kapasitas:
            kapasitas = commify('%.3f' % (kapasitas/1000000.0))
        if pagi.manual:
            pagi.manual = commify('%.2f' % (pagi.manual or 0.0))
        if siang.manual:
            siang.manual = commify('%.2f' % (siang.manual or 0.0))
        if sore.manual:
            sore.manual = commify('%.2f' % (sore.manual or 0.0))

        # ambil nilai inflow, outflow, curahhujan dari waduk_daily
        try:
            wd = WadukDaily.select(AND(WadukDaily.q.waktu==tanggal, WadukDaily.q.pos==self))[0]
            inflow = wd.inflow_q
            outflow_intake_q = wd.intake_q
            outflow_spillway_q = wd.spillway_q
            vnotch = (wd.vnotch_tin1 or 0) + (wd.vnotch_tin2 or 0) + (wd.vnotch_tin3 or 0)
            vnotchq = (wd.vnotch_q1 or 0) + (wd.vnotch_q2 or 0) + (wd.vnotch_q3 or 0)
        except:
            inflow = None
            outflow_intake_q = None
            outflow_spillway_q =None
            vnotch = None
            vnotchq = None

        #manipulasi tanggal curah hujan waduk daily
        tanggal_ch_wd = tanggal + datetime.timedelta(days=1)
        try:
            wd = WadukDaily.select(AND(WadukDaily.q.waktu==tanggal_ch_wd, WadukDaily.q.pos==self))[0]
            curahhujan = wd.curahhujan
        except:
            curahhujan = None

        # ambil nilai tma darurat banjir dari tabel waduk_daily dan bendung_alert
        try:
            if latest > self.siaga3:
                tmab = latest
                jam = r.jam + ":00:00"

            else: 
                ba = BendungAlert.select(AND(BendungAlert.q.tanggall==tanggal, BendungAlert.q.bendungan==self)).orderBy('-jam')[0]
                tmab = ba.tmab
                jam = ba.jam
        except:
            tmab = None
            jam = None
        
        # hitung nilai banjir/limpas dari tma darurat
        if tmab != None:
            limpass = tmab - self.siaga1
        else:
            limpass = None



        # ambil nilai curahhujan harian dan curahhujan terkini
        try:
            chkini = CurahHujanTerkini.select(AND(CurahHujanTerkini.q.tanggall==tanggal, CurahHujanTerkini.q.bendungan==self)).orderBy('-jam')[0]
            if curahhujan:
                ch_latest = curahhujan
                jamm = None
            else :
                ch_latest = chkini.ch_terkini
                jamm = chkini.jam
        except:
            ch_latest = curahhujan
            jamm = None
        

        return dict(waktu=tanggal, pagi=pagi, siang=siang, sore=sore,
                    kondisi=kondisi, kapasitas_series=kap_series,
                    elevasi=latest, vol=vol_jam, p1=p1, p2=p2,
                    inflow=inflow, tmab = tmab, jam = jam, limpass = limpass, awas = self.bts_elev_awas, siaga = self.bts_elev_siaga, waspada = self.bts_elev_waspada, ch_latest = ch_latest, jamm = jamm, curahhujan = curahhujan, outflow_intake_q=outflow_intake_q, outflow_spillway_q=outflow_spillway_q, vnotch=vnotch, vnotchq = vnotchq)

    def status_tma_telemetri(self, _tma):
        for i in (3, 2, 1):
            if _tma > getattr(self, 'siaga%s' % (i,), None):
                return 's%s' % (i, )

    def get_segmented_wl(self, tanggal=datetime.date.today()):
        '''
        mengambil data WL (Tinggi Muka), default hari ini
        '''
        if self.AgentType == 1:
            return {}

        rst = TinggiMukaAir.selectBy(agent=self, waktu=tanggal)
        pagi = Struct(
            **dict(manual=None, mtime=None, mstatus='s1',
                   telemetri=None, ttime=None, tstatus='s0',
                   ttg=None, lokal=None, manual_lokal=None))
        siang = Struct(
            **dict(manual=None, mtime=None, mstatus='s1',
                   telemetri=None, ttime=None, tstatus='s0',
                   ttg=None, lokal=None, manual_lokal=None))
        sore = Struct(
            **dict(manual=None, mtime=None, mstatus='s1',
                   telemetri=None, ttime=None, tstatus='s0',
                   ttg=None, lokal=None, manual_lokal=None))
        tmalam = Struct(
            **dict(manual=None, mtime=None, mstatus='s1',
                   telemetri=None, ttime=None, tstatus='s0',
                   ttg=None, lokal=None, manual_lokal=None))
        for r in rst:
            if r.manual and self.DPL:
                ttg_manual = r.manual + self.DPL
            else:
                ttg_manual = r.manual
            if r.jam.endswith('6'):
                pagi.manual = commify('%.2f' % ttg_manual)
                pagi.manual_lokal = r.manual
                pagi.mtime = r.mtime
                pagi.mstatus = r.status_tma()
            elif r.jam == '12':
                siang.manual = commify('%.2f' % ttg_manual)
                siang.manual_lokal = r.manual
                siang.mtime = r.mtime
                siang.mstatus = r.status_tma()
            elif r.jam == '18':
                sore.manual = commify('%.2f' % ttg_manual)
                sore.manual_lokal = r.manual
                sore.mtime = r.mtime
                sore.mstatus = r.status_tma()

        # jam_dipilih = ('06:00:00', '12:00:00', '18:00:00', '23:55:00')
        jam_dipilih = (86100, 64800, 43200, 21600)
        sql = "SELECT WLevel*0.01 AS WLevel, SamplingTime FROM %s \
               WHERE SamplingDate='%s'" % (self.table_name, tanggal)
        rst = self._connection.queryAll(sql)
        hasil = {}
        dict_rst = dict([(r[1].seconds, r[0]) for r in rst])
        at_least = 90 / 5 # 90=1.5jam
        for i, segment in enumerate(jam_dipilih):
            j = 0
            while j < at_least:
                tma_ = dict_rst.get(segment, None)
                if tma_:
                    tma_ = float(tma_)
                    if i == 3:
                        pagi.telemetri = commify('%.2f' % (tma_ or 0.0))
                        pagi.tstatus = self.status_tma_telemetri(tma_)
                        pagi.ttg = commify('%.2f' % (float(tma_) + self.DPL))
                        pagi.ttime = datetime.timedelta(seconds=segment)
                        pagi.lokal = commify('%.2f' % (float(tma_)))
                    elif i == 2:
                        siang.telemetri = commify('%.2f' % (tma_ or 0.0))
                        siang.tstatus = self.status_tma_telemetri(tma_)
                        siang.ttg = commify('%.2f' % (float(tma_) + self.DPL))
                        siang.ttime = datetime.timedelta(seconds=segment)
                        siang.lokal = commify('%.2f' % (float(tma_)))
                    elif i == 1:
                        sore.telemetri = commify('%.2f' % (tma_ or 0.0))
                        sore.tstatus = self.status_tma_telemetri(tma_)
                        sore.ttg = commify('%.2f' % (float(tma_) + self.DPL))
                        sore.ttime = datetime.timedelta(seconds=segment)
                        sore.lokal = commify('%.2f' % (float(tma_)))
                    elif i == 0:
                        tmalam.telemetri = commify('%.2f' % (tma_ or 0.0))
                        tmalam.tstatus = self.status_tma_telemetri(tma_)
                        tmalam.ttg = commify('%.2f' % (float(tma_) + self.DPL))
                        tmalam.ttime = datetime.timedelta(seconds=segment)
                        tmalam.lokal = commify('%.2f' % (float(tma_)))
                    break
                j += 1
                segment -= 300


        # menampilkan tma terakhir yg terbaca oleh telemetri hari ini
        sql_last = "SELECT WLevel*0.01 AS WLevel, SamplingTime FROM %s \
               WHERE SamplingDate='%s' ORDER BY SamplingDate DESC, SamplingTime DESC" % (self.table_name, tanggal)
        rst_last = self._connection.queryAll(sql_last)
        hasil_last = {}
        dict_rst_last = dict([(r[1].seconds, d[0]) for d in rst_last])
        try:
            last = dict_rst_last.items()[0]
            jam = last[0]
            lastma = last[1]
            
            if last:
                last_tma = commify('%.2f' % (float(lastma) + self.DPL))
                jam = datetime.datetime.utcfromtimestamp(jam).strftime('%H:%M')

        except:
            last_tma = None
            jam = None



        return dict(waktu=tanggal, pagi=pagi, siang=siang, sore=sore,
                    tmalam=tmalam, last_tma=last_tma, jam = jam )

    def sync_segmented_rain(self):
        '''
        sinkronkan table 'curahhujan' (pagi, sore, malam) dg table_name
        '''
        tgls = self.temukan_tanggal_curah_hujan()
        ch_tgls = ''
        if self.AgentType == 2:
            return {}
        return self._connection.queryAll("SELECT Rain, SamplingDate, \
            SamplingTime FROM %s \
            ORDER BY SamplingDate, SamplingTime" % (self.table_name,))

    def get_segmented_rain(self, tanggal=datetime.date.today()):
        '''
        Menghitung curah hujan 3 segment: pagi(7-12), sore(12-18), malam
        @rows = (Rain, SamplingDate, SamplingTime)
        '''
        if self.AgentType == 2:
            return {}
        result = self._connection.queryAll("SELECT Rain * %s AS Rain, SamplingDate, SamplingTime \
            FROM %s WHERE SamplingDate BETWEEN '%s' AND '%s' \
            ORDER BY SamplingDate, SamplingTime" % (
                self.TippingFactor,
                self.table_name, str(tanggal),
                str(tanggal + datetime.timedelta(days=1))))
        if not result:
            data_pagi = data_sore = data_malam = data_tmalam = []
            pagi = sore = malam = tmalam = 0
        else:
            # 25200 = 07:00
            # 46800 = 13:00
            # 68400 = 19:00
            # 3600 = 01:00
            data_pagi = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds >= 25200) and (
                    r[1] == tanggal and r[2].seconds <= 46800)]
            pagi = sum(data_pagi)

            data_sore = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds > 46800) and (
                    r[1] == tanggal and r[2].seconds <= 68400)]
            sore = sum(data_sore)

            data_malam = [r[0] or 0 for r in result if (
                r[1] == tanggal and r[2].seconds > 68400) or (
                    r[1] == tanggal+datetime.timedelta(days=1) and
                    r[2].seconds < 3600)]
            malam = sum(data_malam)
            data_tmalam = [r[0] or 0 for r in result if (
                r[1] == tanggal+datetime.timedelta(days=1) and r[2].seconds > 3600) and (r[1] == tanggal+datetime.timedelta(days=1) and r[2].seconds <= 25200)]
            tmalam = sum(data_tmalam)
        rst = self._connection.queryAll("SELECT manual, mtime_manual, \
                                        origin_manual FROM curahhujan \
                                        WHERE agent_id=%s AND \
            waktu='%s'" % (self.AgentId, str(tanggal)))
        if rst:
            manual = rst[0][0]
            mtime_manual = rst[0][1]
            origin_manual = rst[0][2]
        else:
            manual = None
            mtime_manual = None
            origin_manual = None
        # Kategori hujan
        kat = ("Sangat Ringan", "Ringan", "Sedang", "Lebat", "Sangat Lebat")
        idx = 0
        if 5 > manual < 20:
            idx = 1
        elif 20 > manual < 50:
            idx = 2
        elif 50 > manual < 100:
            idx = 3
        elif manual > 100:
            idx = 4
        result = {'agent_id': self.AgentId, 'waktu': tanggal, 'pagi': pagi,
                  'sore': sore, 'malam': malam, 'tmalam': tmalam,
                  'total': sum(filter(None, [pagi, sore, malam, tmalam])),
                  'manual': manual, 'mtime_manual': mtime_manual,
                  'kategori': kat[idx], 'num_t': len(data_pagi) + len(data_sore) + len(data_malam) + len(data_tmalam),
                  'origin_manual': origin_manual}
        return result

    def get_absolute_url(self):
        return "/pos/%s" % (self.AgentId)

    @property
    def type(self):
        return POS_TYPE[self.AgentType]

    @property
    def table_name(self):
        return self.AgentName.lower().replace('.', '_').replace(' ', '_')

    def get_ch(self, tahun=datetime.date.today().year, bulan=''):
        '''
        Mengambil data Curah hujan selama setahun
        '''
        if self.AgentType == 2:  # 1.0 = Tinggi Muka Air
            return ()
        SEBELUM = 2
        tahun = int(tahun)
        if bulan and int(bulan) in range(1, 12):
            sql = "SELECT waktu, SUM(pagi+sore+malam) AS telemetri, manual \
                    FROM curahhujan \
                WHERE agent_id=%s AND YEAR(waktu)=%s AND MONTH(waktu)=%s \
                GROUP BY DAY(waktu);" % (
                    self.AgentId, tahun, bulan)
            return conn.queryAll(sql)

        tahun = ','.join([str(t) for t in range(tahun-SEBELUM, tahun+1)])
        sql = "SELECT waktu, SUM(pagi+sore+malam) AS telemetri, SUM(manual) from curahhujan \
            WHERE agent_id=%s AND YEAR(waktu) IN (%s) \
            GROUP BY YEAR(waktu), MONTH(waktu);" % (self.AgentId, tahun)
        ret = conn.queryAll(sql)
        return ret

    def hari_hujan(self, waktu, sebulan=True):
        '''return banyaknya hari hujan dalam bulan(waktu),
        sebulan=False berarti dua mingguan'''
        sql = "SELECT COUNT(*) FROM curahhujan \
            WHERE agent_id=%(agent_id)s AND total>0 AND \
            YEAR(waktu)=%(tahun)s AND MONTH(waktu)=%(bulan)s"
        return sql

    def hujan_tertinggi(self, waktu, sebulan=True):
        '''return curahhujan tertinggi (mm, tgl) dalam bulan(waktu
        sebulan=False berarti dua mingguan'''
        pass

    def akumulasi_hujan(self, waktu, sebulan=False):
        '''return banyaknya curahhujan (mm) dalan bulan(waktu),
        sebulan=False berarti dua mingguan'''
        pass

    def get_ch_stats(self):
        '''
        Hasilkan statistik curah hujan
        - rata-rata
        - tertinggi, termasuk tanggal
        - jumlah hujan setahun
        - data paling awal
        - data paling akhir
        - banyak data
        '''
        sql = "SELECT YEAR(waktu), AVG(pagi+sore+malam) AS telemetri, \
            AVG(manual) AS manual FROM curahhujan \
            WHERE agent_id=%s GROUP BY YEAR(waktu)" % self.AgentId
        return {}

    def get_tma(self):
        '''
        Mengambil data Tinggi Muka Air TERAKHIR dan Pos Curah Hujan
        '''
        try:
            rq = conn.queryAll("SELECT COUNT(*) FROM %s" % self.table_name)
        except:
            # Table 'log' belum ada, salin dari table 'tpl_agent'
            rq = conn.queryAll("CREATE TABLE %s LIKE tpl_agent" % self.table_name)
            rq = conn.queryAll("SELECT COUNT(*) FROM %s" % self.table_name)

        rq = conn.queryAll("SELECT * FROM %s ORDER BY SamplingDate DESC, SamplingTime DESC LIMIT 0, 1" % (self.table_name))
        try:
            data_log = rq[0]
        except IndexError:
            return {'id': self.AgentId,
                    'name': self.AgentName,
                    'type': self.AgentType,
                    'latlng': self.ll,
                    'normal': self.sh,
                    'siaga1': self.sk,
                    'siaga2': self.sm,
                    'siaga3': self.siaga4,
                    'sampling': '-',
                    'received': None,
                    'temp': 0,
                    'hum': 0,
                    'rain': 0,
                    'tma': 0,
                    'status_tma': 'siaga1',
                    'wilayah': 1}

        status_tma = 'siaga1'
        for i in (4, 3, 2):
            if data_log[14] and (data_log[14]/100.0 > eval('self.siaga%s' % i)):
                status_tma = 'siaga%s' % i
                break
        if not data_log[14]:
            status_tma = None
        status_tma = 'siaga1'
        return {'id': self.AgentId,
                'name': self.AgentName,
                'type': self.AgentType,
                'latlng': self.ll,
                'normal': self.sh,
                'siaga1': self.sk,
                'siaga2': self.sm,
                'siaga3': self.siaga4,
                'sampling': str(data_log[5]) + ' ' + str(
                    data_log[6])[0:str(data_log[6]).rfind(':')],
                'received': str(data_log[1]) + ' ' + str(
                    data_log[2])[0:str(data_log[2]).rfind(':')],
                'temp': data_log[7],
                'hum': data_log[8],
                'rain': data_log[20] or 0,
                'tma': (data_log[14] or 0) * 0.01 + self.DPL or 0,
                'status_tma': status_tma,
                'wilayah': self.wilayah}

    def logs(self, offset=0, num=30):
        ret = []
        try:
            rq = conn.queryAll("SELECT * FROM %s \
                               ORDER BY SamplingDate DESC, SamplingTime DESC \
                               LIMIT %s, %s" % (self.table_name, offset, num))
            for r in rq:
                rec = datetime.datetime.strptime(str(r[1]) + ' ' + str(
                    r[2]), '%Y-%m-%d %H:%M:%S')
                sam = datetime.datetime.strptime(str(r[5]) + ' ' + str(
                    r[6]), '%Y-%m-%d %H:%M:%S')
                dict = {'received': rec, 'sampling': sam, 'temperature': r[7],
                        'humidity': r[8], 'rain': r[9], 'wlevel': r[14]}
                ret.append(Struct(**dict))
        except:
            pass
        return ret

    @property
    def get_num_log(self):
        try:
            return conn.queryAll("SELECT COUNT(*) \
                                 FROM %s" % self.table_name)[0][0]
        except:
            return 0

    def get_last_log(self):
        try:
            return conn.queryAll("SELECT * FROM %s WHERE SamplingDate <= CURDATE() \
                                 AND SamplingTime <= CURTIME() \
                                 ORDER BY SamplingDate DESC, \
                                 SamplingTime DESC \
                                 LIMIT 0, 1" % self.table_name)[0]
        except:
            return None

    class sqlmeta:
        idName = 'AgentID'
        defaultOrder = ('wilayah', 'AgentName')


class Gate(SQLObject):
    bendung = ForeignKey('Agent')
    name = StringCol(length=35)
    io = EnumCol(enumValues=('i', 'o'))
    flows = MultipleJoin('Flow', orderBy=['-waktu'])

    class sqlmeta:
        table = 'gate'


class Flow(SQLObject):
    gate = ForeignKey('Gate')
    waktu = DateCol()
    opened = FloatCol(notNull=False)  # Bukaan Pintu dalam satuan meter
    value = FloatCol()  # Debit air yang lewat (Q) dalam meter kubik per detik
    timed = IntCol()  # Lamanya pintu dibuka (T) dalam satuan detik

    class sqlmeta:
        table = 'flow'


class WadukDaily(SQLObject):
    '''Data harian Waduk/Bendungan'''
    pos = ForeignKey('Agent')
    waktu = DateTimeCol()
    tma6 = FloatCol(default=None)
    vol6 = FloatCol(default=None)
    tma12 = FloatCol(default=None)
    vol12 = FloatCol(default=None)
    tma18 = FloatCol(default=None)
    vol18 = FloatCol(default=None)
    rembesan = FloatCol(default=None)
    curahhujan = FloatCol(default=0)
    intake_q = FloatCol(default=0)
    intake_v = FloatCol(default=0)
    inflow_q = FloatCol(default=0)
    inflow_v = FloatCol(default=0)
    outflow_q = FloatCol(default=0)
    outflow_v = FloatCol(default=0)
    spillway_q = FloatCol(default=0)
    spillway_v = FloatCol(default=0)
    vnotch_tin = FloatCol(default=None)
    vnotch_q = FloatCol(default=None)
    vnotch_tin1 = FloatCol(default=None)
    vnotch_q1 = FloatCol(default=None)
    vnotch_tin2 = FloatCol(default=None)
    vnotch_q2 = FloatCol(default=None)
    vnotch_tin3 = FloatCol(default=None)
    vnotch_q3 = FloatCol(default=None)
    mtime = DateTimeCol(default=datetime.datetime.now)
    a1 = FloatCol(default=None)
    b1 = FloatCol(default=None)
    c1 = FloatCol(default=None)
    a2 = FloatCol(default=None)
    b2 = FloatCol(default=None)
    c2 = FloatCol(default=None)
    a3 = FloatCol(default=None)
    b3 = FloatCol(default=None)
    c3 = FloatCol(default=None)
    a4 = FloatCol(default=None)
    b4 = FloatCol(default=None)
    c4 = FloatCol(default=None)
    a5 = FloatCol(default=None)
    b5 = FloatCol(default=None)
    c5 = FloatCol(default=None)
    po_outflow_q = FloatCol(default=None)
    po_inflow_q = FloatCol(default=None)
    po_tma = FloatCol(default=None)
    po_vol = FloatCol(default=None)
    po_outflow_v = FloatCol(default=None)
    po_inflow_v = FloatCol(default=None)
    po_bona = FloatCol(default=None)
    po_bonb = FloatCol(default=None)
    vol_bona = FloatCol(default=0)
    vol_bonb = FloatCol(default=0)
    

    class sqlmeta:
        table = 'waduk_daily'


class BendungAlert(SQLObject):
    '''TMA / Kondisi banjir Waduk'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    tanggall = DateCol()
    jam = TimeCol()
    tmab = FloatCol(default=None)
    spillwayb_q = FloatCol(default=None)

    class sqlmeta:
        table = 'bendung_alert'

class CurahHujanTerkini(SQLObject):
    '''Curah Hujan sewaktu-waktu'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    tanggall = DateCol()
    jam = TimeCol()
    ch_terkini = FloatCol(default=None)

    class sqlmeta:
        table = 'curahhujan_terkini'

#-----------class Form Petugas Bendungan-----------------------
class BendungFormA(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    bukaan_pintu1 = FloatCol(default=None)
    vol_pintu1 = FloatCol(default=0)
    debit_rerata_pintu1 = FloatCol(default=0)
    jam_pintu1 = TimeCol(default=None)
    bukaan_pintu2 = FloatCol(default=None)
    vol_pintu2 = FloatCol(default=0)
    debit_rerata_pintu2 = FloatCol(default=0)
    jam_pintu2 = TimeCol(default=None)
    h_pelimpahutama = FloatCol(default=None)
    vol_pelimpahutama = FloatCol(default=0)
    debit_pelimpahutama = FloatCol(default=0)
    jam_pelimpahutama = TimeCol(default=None)
    vol_total_pelepasan = FloatCol(default=0)
    debit_rerata_total_pelepasan = FloatCol(default=0)
    keterangan = StringCol(default=None)
   

    class sqlmeta:
        table = 'bendung_form_a'

class BendungFormA1(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    luas_baku = FloatCol(default=None)
    nama_di = StringCol(default=None)
    luas_terlayani = FloatCol(default=None)
    padi_jenistanaman = StringCol(default=None)
    palawija_jenistanaman = StringCol(default=None)
    bero_jenistanaman = StringCol(default=None)
    padi_umurtanaman = StringCol(default=None)
    palawija_umurtanaman = StringCol(default=None)
    padi_sisaumur = StringCol(default=None)
    palawija_sisaumur = StringCol(default=None)
    keterangan = StringCol(default=None)
   

    class sqlmeta:
        table = 'bendung_form_a1'

class BendungFormB(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    retakan_puncak_bendung = StringCol(default=None)
    penurunan_puncak_bendung = StringCol(default=None)
    kelurusan_puncak_bendung = StringCol(default=None)
    retakan_lereng_hulu = StringCol(default=None)
    penurunan_lereng_hulu = StringCol(default=None)
    tonjolan_lereng_hulu = StringCol(default=None)
    retakan_lereng_hilir = StringCol(default=None)
    penurunan_lereng_hilir = StringCol(default=None)
    tonjolan_lereng_hilir = StringCol(default=None)
    retakan_pd_beton = StringCol(default=None)
    gerusan_ujung_hilir = StringCol(default=None)
    mengetahui_petugas = IntCol(default=None)
    mengetahui_koordinator = IntCol(default=None)
    

    class sqlmeta:
        table = 'bendung_form_b'

class BendungFormB1_1(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    kondisi_cuaca = StringCol(default=None)
    tinggi = FloatCol(default=None)
    panjang = FloatCol(default=None)
    kond_jln_atas_mercu = StringCol(default=None)
    tanda_penurunan_mercu = StringCol(default=None)
    tanda_pergerakan_mercu = StringCol(default=None)
    kond_pembuang_mercu = StringCol(default=None)
    kond_pagar_mercu = StringCol(default=None)
    tanda_gerakan_lerenghulu = StringCol(default=None)
    tonjolan_lubangbenam_retakan_lerenghulu = StringCol(default=None)
    erosi_penurunan_lerenghulu = StringCol(default=None)
    dimana_kedalaman_lebarpanjangretakan_lerenghulu = StringCol(default=None)
    tumbuhan_sarangbinatang_lerenghulu = StringCol(default=None)
    tanda_retak_platbeton = StringCol(default=None)
    dimana_kedalaman_lebarpanjangretakan_platbeton = StringCol(default=None)
    parimeter_joint_platbeton = StringCol(default=None)
    kond_beton_platbeton = StringCol(default=None)
    erosi_platbeton = StringCol(default=None)
    kond_permukaan_buitmen = StringCol(default=None)
    erosi_buitmen = StringCol(default=None)
    tanda_gerakan_riprap = StringCol(default=None)
    rusak_krn_cuaca_riprap = StringCol(default=None)
    pelapukan_riprap = StringCol(default=None)
    erosi_riprap = StringCol(default=None)
    slip_dbwhair_riprap = StringCol(default=None)
    tanda_gerakan_lerenghilir = StringCol(default=None)
    tonjolan_lubangbenam_retak_lerenghilir = StringCol(default=None)
    erosi_penurunan_longsorantanah_lerenghilir = StringCol(default=None)
    dimana_kedalaman_lebarpanjangretakan_lerenghilir = StringCol(default=None)
    slip_dbwhair_lerenghilir = StringCol(default=None)
    tanda_rembesan = StringCol(default=None)
    dimana_kuantitas_warna_rembesan = StringCol(default=None)
    kondtumbuhan = StringCol(default=None)
    jns_plindung_lereng = StringCol(default=None)
    

    class sqlmeta:
        table = 'bendung_form_b1_1'

class BendungFormB1_2(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    jenis_bendung = StringCol(default=None)
    pintu_jml_jenis_bendung = StringCol(default=None)
    pengoperasian_bendung = StringCol(default=None)
    operasidarurat_bendung = StringCol(default=None)
    pelimpahbantu_bendung = StringCol(default=None)
    jplimphbantu_bendung = StringCol(default=None)
    kondisi_salpengahantar = StringCol(default=None)
    lantdasar_salpenghantar = StringCol(default=None)
    lereng_salpenghantar = StringCol(default=None)
    kondisi_spillweir = StringCol(default=None)
    auserosi_spillweir = StringCol(default=None)
    lokasi_spillweir = StringCol(default=None)
    kondisi_dinding = StringCol(default=None)
    auserosi_dinding = StringCol(default=None)
    dmn_dinding = StringCol(default=None)
    kondisijoint_dinding = StringCol(default=None)
    kondisisaluran_dinding = StringCol(default=None)
    kond_salcuram = StringCol(default=None)
    auserosi_salcuram = StringCol(default=None)
    lapbasah_salcuram = StringCol(default=None)
    dmn_salcuram = StringCol(default=None)
    jenis_kolam = StringCol(default=None)
    kondisi_kolam = StringCol(default=None)
    auserosi_kolam = StringCol(default=None)
    lapbasah_kolam = StringCol(default=None)
    dmn_kolam = StringCol(default=None)
    ketidakwajaran_kinerja = StringCol(default=None)
    tandaslip_dsekitar = StringCol(default=None)
    tandarembesan_dsekitar = StringCol(default=None)
    jenistumbuhan_dsekitar = StringCol(default=None)
    gangguan_dsekitar = StringCol(default=None)

    class sqlmeta:
        table = 'bendung_form_b1_2'

class BendungFormB1_3(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    lok_piezometer = StringCol(default=None)
    jumlah_piezometer = StringCol(default=None)
    jenis_piezometer = StringCol(default=None)
    kond_baik_piezometer = StringCol(default=None)
    kond_tdkbaik_piezometer = StringCol(default=None)
    lok_alt_rembesan = StringCol(default=None)
    jml_alt_rembesan = StringCol(default=None)
    jns_alt_rembesan = StringCol(default=None)
    kond_altbaik_rembesan = StringCol(default=None)
    kond_alttdkbaik_rembesan = StringCol(default=None)
    lok_altpnurunan = StringCol(default=None)
    jml_altpnurunan = StringCol(default=None)
    jns_altpnurunan = StringCol(default=None)
    kond_altbaikpnurunan = StringCol(default=None)
    kond_alttdkbaikpnurunan = StringCol(default=None)
    lok_multilayer = StringCol(default=None)
    jml_multilayer = StringCol(default=None)
    jns_multilayer = StringCol(default=None)
    kond_baikmultilayer = StringCol(default=None)
    kond_tdkbaikmultilayer = StringCol(default=None)
    lok_observasi = StringCol(default=None)
    jml_observasi = StringCol(default=None)
    jns_observasi = StringCol(default=None)
    kond_baikobservasi = StringCol(default=None)
    kond_tdkbaikobservasi = StringCol(default=None)
    lok_inclinometer = StringCol(default=None)
    jml_inclinometer = StringCol(default=None)
    jns_inclinometer = StringCol(default=None)
    kond_baikinclinometer = StringCol(default=None)
    kond_tdkbaikinclinometer = StringCol(default=None)
    tandaerosi_kakibendung = StringCol(default=None)
    aliranlubang_kakibendung = StringCol(default=None)
    lapsbasah_kakibendung = StringCol(default=None)
    dmn_kakibendung = StringCol(default=None)
    lihat_lubang_benam_tumpuanbendung = StringCol(default=None)
    slip_tumpuanbendung = StringCol(default=None)
    tndapatahan_tumpuanbendung = StringCol(default=None)
    retakan_tumpuanbendung = StringCol(default=None)


    class sqlmeta:
        table = 'bendung_form_b1_3'

class BendungFormB1_4(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    lok_inlet = StringCol(default=None)
    jns_inlet = StringCol(default=None)
    akses_inlet = StringCol(default=None)
    kond_inlet = StringCol(default=None)
    auserosi_inlet = StringCol(default=None)
    lapbas_inlet = StringCol(default=None)
    dmnlok_inlet = StringCol(default=None)
    kondsamb_inlet = StringCol(default=None)
    kondsalbuang_inlet = StringCol(default=None)
    pintu_hidromekanik = StringCol(default=None)
    katupjenis_hidromekanik = StringCol(default=None)
    metodoperasi_hidromekanik = StringCol(default=None)
    pengoperasiandarurat_hidromekanik = StringCol(default=None)
    kond_hidromekanik = StringCol(default=None)
    lok_outlet = StringCol(default=None)
    jns_outlet = StringCol(default=None)
    akses_outlet = StringCol(default=None)
    kond_outlet = StringCol(default=None)
    auserosi_outlet = StringCol(default=None)
    lapsbas_outlet = StringCol(default=None)
    dmnlok_outlet = StringCol(default=None)
    kondsamb_outlet = StringCol(default=None)
    kondsalbuang_outlet = StringCol(default=None)
    ukur_gorong = StringCol(default=None)
    kond_gorong = StringCol(default=None)
    auserosi_gorong = StringCol(default=None)
    lapsbas_gorong = StringCol(default=None)
    dmnlok_gorong = StringCol(default=None)
    kondsamb_gorong = StringCol(default=None)
    kondsalbuang_gorong = StringCol(default=None)
    endapan_gorong = StringCol(default=None)
    endapan_waduk = StringCol(default=None)
    tebingsungai_hilir = StringCol(default=None)
    erosipengikisan_hilir = StringCol(default=None)
    pengaruhtumbuhan_hilir = StringCol(default=None)
    habitatterdekat_hilir = StringCol(default=None)
    jumlahpenduduk_hilir = StringCol(default=None)

    class sqlmeta:
        table = 'bendung_form_b1_4'

class BendungFormB3(SQLObject):
    '''Form petugas bendungan tentang kondisi bendungan'''
    bendungan = ForeignKey('Agent', dbName='bendungan_id')
    waktu = DateCol()
    mslah_pbendung = StringCol(default=None)
    tndkan_pbendung = StringCol(default=None)
    mslah_lerhulubend = StringCol(default=None)
    tndkan_lerhulubend = StringCol(default=None)
    mslah_lerhilirbend = StringCol(default=None)
    tndkan_lerhilirbend = StringCol(default=None)
    mslah_instrumentasi = StringCol(default=None)
    tndkan_instrumentasi = StringCol(default=None)
    mslah_pmbuang = StringCol(default=None)
    tndkan_pmbuang = StringCol(default=None)
    mslah_tumpuan = StringCol(default=None)
    tndkan_tumpuan = StringCol(default=None)
    mslah_plimpah = StringCol(default=None)
    tndkan_plimpah = StringCol(default=None)
    mslah_inlet = StringCol(default=None)
    tndkan_inlet = StringCol(default=None)
    mslah_hidromekanik = StringCol(default=None)
    tndkan_hidromekanik = StringCol(default=None)
    mslah_outlet = StringCol(default=None)
    tndkan_outlet = StringCol(default=None)
    mslah_waduk = StringCol(default=None)
    tndkan_waduk = StringCol(default=None)
    mslah_bagsungai = StringCol(default=None)
    tndkan_bagsungai = StringCol(default=None)
    mslah_lain = StringCol(default=None)
    tndkan_lain = StringCol(default=None)

    class sqlmeta:
        table = 'bendung_form_b3'


class TinggiMukaAir(SQLObject):
    '''
    Table ini berisi data kiriman dari petugas (manual)
    '''
    agent = ForeignKey('Agent', notNull=True)
    waktu = DateCol(notNull=True)
    jam = StringCol(notNull=True, default='6')  # berisi 6, 12, 18
    manual = FloatCol(notNull=False, default=None)  # nilai TinggiMuka Kiriman
    telemetri = FloatCol(notNull=False, default=None)  # nilai telemetri pd jam
    mtime = DateTimeCol(notNull=False, default=None)  # Waktu data diterima
    origin = StringCol(length=35, default=None)  # No HP Pengirim
    num_t = IntCol(default=0) # Banyaknya data dari logger 24 jam, jam=12

    def status_tma(self):
        ret = 'siaga1'
        for i in (3, 2, 1):
            if self.manual and self.manual > eval('self.agent.siaga%s' % i):
                ret = 'siaga%s' % i
        return ret

    class sqlmeta:
        table = 'tma'
        defaultOrder = ('-waktu', 'agent_id', )
        lazyUpdate = True


class CurahHujan(SQLObject):
    '''
    Table ini berisi hasil hitung Curah Hujan dan table 'Agent'

    Intensitas Hujan    1 jam   24 jam
    Sangat Ringan       <1      <5
    Ringan              1 - 5   5 - 20
    Normal / Sedang     5 - 10  20 - 50
    Lebat               10 - 20 50 - 100
    Sangat Lebat        >20     >100

    '''
    agent = ForeignKey('Agent', notNull=True)
    waktu = DateCol(notNull=True)
    pagi = FloatCol(notNull=False, default=None)  # 7 - 12, data telemetri
    sore = FloatCol(notNull=False, default=None)  # 12 - 18, data telemetri
    malam = FloatCol(notNull=False, default=None)  # 18 - 7, data telemetri
    tmalam = FloatCol(notNull=False, default=None)  # 18 - 7, data telemetri
    total = FloatCol(notNull=False, default=None)
    manual = FloatCol(notNull=False, default=None)
    mtime_total = DateTimeCol(notNull=False, default=None)
    origin_manual = StringCol(length=35, default=None)
    mtime_manual = DateTimeCol(notNull=False, default=None)
    num_t = IntCol(default=0) # Banyaknya data dari logger 24 jam

    @property
    def kategori(self, range=24):
        kat = ("Sangat Ringan", "Ringan", "Sedang", "Lebat", "Sangat Lebat")
        idx = 0
        if 5 > self.manual < 20:
            idx = 1
        elif 20 > self.manual < 50:
            idx = 2
        elif 50 > self.manual < 100:
            idx = 3
        elif self.manual > 100:
            idx = 4

        return kat[idx]

    def hari_hujan(self, bulan):
        '''Return banyaknya hari terjadi hujan dalam `bulan`'''
        pass

    def tertinggi(self, bulan):
        '''Return hujan tertinggi dalam `bulan`'''
        pass

    def akumulasi(self, bulan):
        '''Return jumlah hujan dalam `bulan`'''
        pass

    class sqlmeta:
        defaultOrder = ('-waktu', 'agent_id', )
        table = 'curahhujan'
        lazyUpdate = True


class Latlondas(SQLObject):
    AgentName = StringCol(alternateID=True, dbName='AgentName')
    lat = StringCol()
    lon = StringCol()

    class sqlmeta:
        idName = 'AgentName'


class Authuser(SQLObject):
    username = StringCol()
    realname = StringCol()
    password = StringCol()
    is_admin = IntCol(default=0)
    table_name = StringCol(notNone=False, default=None)

    class sqlmeta:
        table = 'passwd'


class NewsTicker(SQLObject):
    body = StringCol(length=250)
    tanggal = DateTimeCol()
    is_show = BoolCol(default=True)
    user = StringCol(length=20, default=None)

    def get_absolute_url(self):
        return '/message/%s' % self.id


class Alert(SQLObject):
    no = StringCol(dbName='No', alternateID=True)
    atype = IntCol(dbName='AlertType')
    sms = StringCol(length=25, dbName='APhoneNumber')
    location = StringCol(length=25, dbName='AlertLocation')

    def get_sms(self, atype=1):
        sql = "SELECT DISTINCT(APhoneNumber) \
            FROM alerttable \
            WHERE AlertType=%s" % atype
        return [a[0] for a in self._connection.queryAll(sql)]

    def set_sms(self, hp, atype=1):
        pass

    class sqlmeta:
        table = 'alerttable'
        idName = 'no'
        idType = str


def set_sms_alert(atype, hp):
    data = [(atype, hp, a.table_name) for a in Agent.select() if a.AgentType != KLIMATOLOGI]
    for d in data:
        conn.queryAll("INSERT INTO alerttable (AlertType, APhoneNumber, AlertLocation, AlertStatus, No) VALUES (%s, '%s', '%s', '234', '999')" % d)

def set_sms_alert_remove(atype, hp):
    conn.queryAll("DELETE FROM alerttable WHERE AlertType=%s AND APhoneNumber='%s'" % (atype, hp))
