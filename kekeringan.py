"""
    kekeringan.py
    Aplikasi Kekeringan

    @author: Widoyo
    @date: 05 Mei 2017
"""
import datetime
import web

urls = (
    '$', 'Index',
)

app_kekeringan = web.application(urls, locals())
session = web.session.Session(app_kekeringan, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class Index:
    def GET(self):
        return render.kekeringan.index()
