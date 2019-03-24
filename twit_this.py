import json
import twitter
import logging
import logging.handlers


HS_CONSUMER_KEY = 'HK21JDLtY0Us5hzAbVxDA'
HS_CONSUMER_SECRET = 'KtPsHcRotjWl1wAu2Cdf1exnWoGacqnxPB9ATDp0EHE'
HS_ACCESS_TOKEN_KEY = '512650477-FhDIx6a7rAo4dsqkBrZrBsVWoLiHKhgr0Zpg967c'
HS_ACCESS_TOKEN_SECRET = '48J1NWiCqrlBAXIE1Qr64ap1fSPBvy5EqmbkQOg58Q'

LOG_FILENAME = 'twitter.log'
LOG_LEVEL = logging.ERROR

log = logging.getLogger('twit_this')
lh = logging.handlers.RotatingFileHandler(filename=LOG_FILENAME, maxBytes=5000, backupCount=5)
lh.setLevel(LOG_LEVEL)
lf = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
lh.setFormatter(lf)
log.setLevel(LOG_LEVEL)
log.addHandler(lh)

tapi = twitter.Api(consumer_key=HS_CONSUMER_KEY,
                  consumer_secret=HS_CONSUMER_SECRET,
                  access_token_key=HS_ACCESS_TOKEN_KEY,
                  access_token_secret=HS_ACCESS_TOKEN_SECRET)


status_teks = ('Normal', 'Siaga Hijau', 'Siaga Kuning', 'Siaga Merah')

def twit_this(data):
    log.info("Into twit_this function, data: %s" % str(data))
    tma = float(data['tma'] or 0) / 100.0
    status_tma = 4
    for i in (1,2,3,4):
        if tma < eval("data['agent']['siaga%s']" % i):
            status_tma = i
            break
    batas = eval("data['agent']['siaga%s']" % status_tma)
    teks = "%s, %s, tinggi muka air %s meter, %.1f%% dari batas %s (%s meter)" % (data['agent']['AgentName'], data['sampling'], tma, tma / float(batas or 0) * 100, status_teks[status_tma-1], batas)
    log.info(teks)
    try:
        tapi.PostUpdate(teks)
    except Exception, err:
        log.error(err)

