'''
Aplikasi menampilkan foto
1) dari aplikasi Kegiatan Petugas
2)

tables:
    kegiatan
    foto
'''
import web
from models import Foto, Agent


urls = (
    '$', 'Index'
)


app_galeri = web.application(urls, locals())
session = web.session.Session(app_galeri, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'table_name': None, 'err': None})
globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Index:
    def GET(self):
        fotos = Foto.select().orderBy('-cdate')[:5]
        return render.galeri.index({'fotos': fotos})
