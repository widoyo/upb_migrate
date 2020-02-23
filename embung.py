'''
Aplikasi Embung

Embung BPA
Embung Air Baku

Widoyo
21 Juni 2019
'''
import web

from models import Embung

urls = (
    '', 'Index'
)

app_embung = web.application(urls, locals())
session = web.session.Session(app_embung, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'err': None})

globals = {'session': session, 'eval': eval}
render = web.template.render('templates/', base='base', globals=globals)

class Index:
    def GET(self):
        '''Showing list of Embung'''
        embung_bpa = Embung.select(Embung.q.jenis=='b')
        embung_ab = Embung.select(Embung.q.jenis=='a')
        return render.embung.index({'bpas': embung_bpa, 'abs': embung_ab})
