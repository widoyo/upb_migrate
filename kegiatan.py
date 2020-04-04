'''Tampilan Kegiatan untuk Publik
'''

import datetime
import web
from sqlobject import func
from helper import to_date

from models import Kegiatan


urls = (
    '$', 'Index',
)

app_kegiatan = web.application(urls, locals())
session = web.session.Session(app_kegiatan, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'is_admin': None,
                                           'table_name': None, 'err': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Index:
    def GET(self):
        sampling = web.input().get('sampling')
        if not sampling:
            sampling = datetime.date.today()
        else:
            sampling = to_date(sampling)
        #sampling = datetime.date(2019, 11, 16)
        kegiatan = Kegiatan.select().filter(
            Kegiatan.q.sampling==sampling).orderBy('table_name, petugas')
        return render.kegiatan.index({'kegiatan': kegiatan, 'sampling':
                                      sampling})
