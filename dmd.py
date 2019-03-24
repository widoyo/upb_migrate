"""
dmd.py
Dot Matrix Display

@author: Widoyo
@date: 15 Mar 2018
"""
import datetime
import web
from sqlobject import OR

from models import Agent, conn

urls = (
    '/(\w+\.*\-*\w+)', 'Show'
)


app_dmd = web.application(urls, locals())

class Show:
    def GET(self, loc):
        agents = dict([(r.table_name, r.AgentId) for r in Agent.select(OR(Agent.q.AgentType==3, Agent.q.AgentType==2))])
        if agents.get(loc):
            sql = "SELECT SamplingDate, SamplingTime, WLevel/100.0 FROM %s \
                ORDER BY SamplingDate DESC, SamplingTime DESC \
                LIMIT 0, 1" % loc
            rst = conn.queryAll(sql)
            if rst:
                pos = Agent.get(agents.get(loc))
                sampling = datetime.datetime.fromtimestamp(int(rst[0][0].strftime('%s')) + rst[0][1].seconds)
                web.header('Content-Type', 'text/plain')
                return pos.cname + '|' + sampling.strftime('%d%b%y|%H:%M') + '|' + 'TMA: %.2f' % (pos.DPL + float(rst[0][2] or 0))
        return web.notfound()
