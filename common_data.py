'''
Data Umum bersama
'''
BENDUNGAN_DICT = {'bd_gebyar': 113, 'bd_botok': 94, 'bd_pacal': 110, 'bd_songputri': 83, 'bd_plumbon': 84, 'bd_telaga_ngebel': 100, 'bd_gonggang': 102, 'bd_nawangan': 81, 'bd_kedung_brubus': 105, 'bd_telaga_pasir': 101, 'bd_krisak': 88, 'bd_brambang': 95, 'bd_notopuro': 106, 'bd_delingan': 91, 'bd_sangiran': 107, 'bd_jombor': 89, 'bd_saradan': 104, 'bd_prijetan': 111, 'bd_parangjoho': 85, 'bd_gembong': 96, 'bd_dawuhan': 103, 'bd_kedunguling': 86, 'bd_lalung': 92, 'bd_gondang': 112, 'bd_wonogiri': 87, 'bd_ngancar': 82, 'bd_cengklik': 93, 'bd_mulur': 90, 'bd_ketro': 99, 'bd_kedung_bendo': 109, 'bd_blimbing': 97, 'bd_pondok': 108, 'bd_kembangan': 98}

NO_VNOTCH = ('kedunguling', 'jombor', 'mulur', 'blimbing', 'brambang', 'gembing', 'saradan')

FAIL_VNOTCH = ('plumbon', 'lalung', 'botok', 'ketro', 'dawuhan', 'notopuro', 'prijetan')

KLIMATOLOGI_POS = ('pabelan', 'bendung_colo', 'baturetno', 'wonogiri', 'madiun', 'bojonegoro')

FTP_HOST = '117.20.58.227'
CCTV_IMG_DIR = 'cctv-3g'
CCTV_POS = ('jurug', )

DEBIT_POS = {
    'serenan': {'a': 66.24, 'b': 0.1, 'c': 1.69},
    'jurug': {'a': 19.156, 'b': 0.4, 'c': 1.799},
    'kajangan': {'a': 75.85, 'b': 0.2, 'c': 1.6},
    'sekayu': {'a': 37.39, 'b': 0.03, 'c': 2.042},
    'ahmadyani': {'a': 28.98, 'b': 0.1, 'c': 2.097},
    'ketonggo': {'a': 10.876, 'b': -0.6, 'c': 1.836},
    'pacitan': {'a': 35.698, 'b': 0.15, 'c': 2.1},
    'napel': {'a': 36.485, 'b': 0.1, 'c': 2.062},
    'cepu': {'a': 115.015, 'b': -0.58, 'c': 1.473},
    'bojonegoro_awlr': {'a': 98.52, 'b': -1.6, 'c': 1.278},
    'kedungupit': {'a': 19.512, 'b': -0.6, 'c': 1.705}
    }

BSOLO_LOGGER = {
}

CAUSE_TABLE = {  # Hulu
               'colo_weir': ('gunungan', 'wonogiri'),
               'jarum': ('klaten', 'rejoso'),
               'jurug': ('wonogiri', 'bendung_colo', 'pabelan'),
               'kedungupit': ('jurug2', 'kalijambe', 'sragen'),
               'ngadipiro': ('jatisrono',),
               'wonogiri_dam': ('wonogiri', 'baturetno', 'songputri'),
               'ngrembang': ('giriwoyo',),
               'peren': ('karangpandan', 'tawangmangu'),
               'serenan': ('gunungan', 'wonogiri', 'bendung_colo', 'klaten'),
               'tangen_bridge': ('jurug', 'kalijambe', 'sragen'),
               #  Madiun
               'badegan': ('purwantoro', 'kenteng'),
               'bendo': ('sooko',),
               'ahmadyani': ('bangunsari', 'slahung', 'madiun'),
               'jati_weir': ('slahung', 'bangunsari'),
               'kajangan': ('tangen_bridge_2', 'sragen'),
               'ketonggo': ('ngrambe', 'madiun'),
               'ketonggo_bridge': ('ngrambe', 'madiun'),
               'napel': ('ngawi', 'ngrambe'),
               'pacitan': ('nawangan', 'pacitan_arr'),
               'sekayu': ('slahung', 'sooko'),
               'winongo_bridge': ('bangunsari', 'slahung'),
               'babat': ('bojonegoro',),
               'babat_barrage': ('bojonegoro',),
               'malo_bridge': ('randublatung', 'padangan'),
               'bojonegoro_barrage': ('padangan', ),
               'bojonegoro_awlr': ('padangan', ),
               'brangkal': ('randublatung', 'padangan'),
               'cepu': ('ngawi', ),
               'kalilamong': ('balongpanggang', 'putat'),
               'karanggeneng': ('lamongan', 'bojonegoro'),
               'karangnongko': ('ngawi', 'ngrambe')}
