"""
    about.py
    Profile Organisasi

    @author: Widoyo
    @date: 05 Mei 2017
"""
import datetime
import web

urls = (
    '$', 'Index',
    '/wilayah-kerja', 'WilayahKerja',
    '/struktur-organisasi', 'StrukturOrganisasi',
    '/profil-tim', 'ProfilTim',
    '/kontak-kami', 'KontakKami'
)

app_about = web.application(urls, locals())
session = web.session.Session(app_about, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})

globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class WilayahKerja:
    def GET(self):
        return render.about.wilayah_kerja()


class StrukturOrganisasi:
    def GET(self):
        return render.about.struktur_organisasi()


class ProfilTim:
    def GET(self):
        return render.about.profil_tim()


class KontakKami:
    def GET(self):
        return render.about.kontak_kami()
