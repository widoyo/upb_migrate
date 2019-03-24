import getopt
import sys

import web
import datetime


def json_serializer(obj):
    if type(obj) is datetime.date or type(obj) is datetime.datetime:
        return obj.isoformat()


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def to_datetime(datetimestring):
    """datetimestring harus berformat yyyy/mm/dd hh:mm"""
    _datetime = None
    _tg, _jam = datetimestring.split()
    (t, b, g) = _tg.split('/')
    (j, m, s) = _jam.split(':')
    _datetime = datetime.datetime(int(t), int(b), int(g),
                                  int(j), int(m), int(s))
    return _datetime


def to_date(datestring):
    """datestring harus berformat yyyy/mm/dd"""
    _date = None
    (t, b, g) = datestring.split('/')
    _date = datetime.date(int(t), int(b), int(g))
    return _date


def set_msg(msg, msg_type=None):
    if msg_type == 'error':
        msg += '$ERR$'
    elif msg_type == 'note':
        msg += '$NOTE$'
    web.setcookie('mc_msg', msg)


def get_delete_msg():
    msg = web.cookies().get('mc_msg', None)
    web.setcookie('mc_msg', '', expires=-1)

    msg_type = None
    if msg:
        if msg.endswith('$ERR$'):
            msg_type = 'error'
            msg = msg[:-5]
        elif msg.endswith('$NOTE$'):
            msg_type = 'note'
            msg = msg[:-6]
    return msg, msg_type


def f5(seq, idfun=None):
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def usage():
    print "Penggunaan:"
    print "  python " + sys.argv[0] + " <option>\n   option:\
        \n    -h : Help\n    -U : Update table grafik"


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hU", ["help", "update"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-U", "--update"):
            update_log_file()
            sys.exit()

    usage()

if __name__ == "__main__":
    main()
