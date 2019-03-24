"""
    map.py
    Aplikasi menampilkan Peta

    @author: Widoyo
    @date: 28 Nop 2017
"""
import datetime
import web
from sqlobject import AND, OR
from models import Agent, KLIMATOLOGI, WILAYAH, conn
from models import HIDROLOGI

urls = (
    '/curahhujan', 'MapCurahhujan',
    '/tma', 'MapTma',
    '/bendungan', 'MapBendungan'
)

app_map = web.application(urls, locals())
session = web.session.Session(app_map, web.session.DiskStore('sessions'),
                              initializer={'username': None, 'role': None,
                                           'flash': None})
globals = {'session': session}
render = web.template.render('templates/', base='base', globals=globals)


class MapBendungan:
    def GET(self):
        agents = Agent.select(Agent.q.AgentType == 3)
        agents = [a for a in agents]
        all_pos = [{'id': a.AgentId, 'name': a.cname, 'll': a.ll} for a in agents]
        js_foot = """
        <script type="text/template" id="pos_infowindow">
          <div class="item infowindow" id="pos_<%= index %>">
            <span class="pos"><%= name %> </span>
            <span class="meter">
            </span>
          </div>
        </script>
        <script>
        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
    {
        "featureType": "all",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "weight": "2.00"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "color": "#9c9c9c"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "all",
        "stylers": [
            {
                "color": "#f2f2f2"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "landscape.man_made",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "saturation": -100
            },
            {
                "lightness": 45
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#eeeeee"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#7b7b7b"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "road.highway",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "elementType": "labels.icon",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "transit",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "all",
        "stylers": [
            {
                "color": "#46bcec"
            },
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#88b6f2" /* "#c8d7d4" */
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#000000"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    }
],
          mapTypeId: google.maps.MapTypeId.TERRAIN };
            var map = new google.maps.Map(document.getElementById('map'), my_options);
            var lamong_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/lamong.kml?v=1',
                preserveViewport: true, map: map});
            var pantura_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/pantura.kml',
                preserveViewport: true, map: map});
            var hilir_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hilir.kml',
                preserveViewport: true, map: map});
            var madiun_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/madiun.kml',
                preserveViewport: true, map: map});
            var hulu_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hulu.kml',
                preserveViewport: true, map: map});
          var allPos = """ + str(all_pos) + """;
          var markers = {};
          var infoWindow = new google.maps.InfoWindow;
          _.each(allPos, function(pos) {
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                map: map,
                position: point
            });
            markers[pos.id] = marker;
            bind_info_window(marker, map, infoWindow, "<a href='/tma/"+pos.id+"' style='font-weight: bold;font-size: 16px;'>"+ pos.name + "</a>");
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        <script type="text/javascript">
        </script>
        """
        return render.map.bendungan({'poses': agents, 'js_foot': js_foot})


class MapCurahhujan:
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_ARR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == KLIMATOLOGI, Agent.q.AgentType == 0.0),
                                  Agent.q.expose == True))
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        sql = "SELECT prima_id, AgentName FROM agent WHERE AgentType IN (0, 1) AND LENGTH(prima_id)>4"
        try:
            rst = Agent._connection.queryAll(sql)
            all_prima = dict([(a[1].lower().replace('.', '_').replace(' ', '_'), a[0]) for a in rst])
        except:
            all_prima = {}
        #all_prima = dict(map(lambda x: (x[1], x[0]), [p.strip().split('\t') for p in open('PRIMA_ID.txt').readlines()]))
        all_pos = []
        for a in agents:
            sql = "SELECT Rain, CONCAT(SamplingDate, ' ', SamplingTime) AS sampling FROM %s ORDER BY SamplingDate DESC, SamplingTime DESC LIMIT 0, 1" % (a.table_name,)
            try:
                rst = Agent._connection.queryAll(sql)
            except:
                rst = None
            if rst:
                rain, sampling = rst[0]
                print rst[0]
                sampling = datetime.datetime.strptime(sampling, '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() - sampling > datetime.timedelta(minutes=10):
                    rain = 0
                else:
                    rain = float(rain or 0)
            else:
                rain = 0
            p_ = {'id': a.AgentId, 'lrain': rain, 'name': a.cname, 'll': a.ll, 'tname': a.table_name}
            if a.table_name in all_prima.keys():
                p_.update({'device': all_prima.get(a.table_name)})
            all_pos.append(p_)
        js_foot = """
        <script type="text/template" id="pos_infowindow">
          <div class="item infowindow" id="pos_<%= index %>">
            <span class="pos"><%= name %> </span>
            <span class="meter">
            </span>
            <div class="">
              <ul>
                <li><i class="fa fa-bar-chart"></i> <a href="/curahhujan/<%= id %>">Hujan Tahunan</a></li>
                <li><i class="fa fa-calendar"></i> <a href="/curahhujan/<%= id %><% print('/' + sampling.split('-')[0] + '/' + sampling.split('-')[1]) %>">Hujan Bulan</a></li>
            </div>
          </div>
        </script>
        <script>
        var ws = new WebSocket('ws://mqtt.bbws-bsolo.net:22286');
        ws.onmessage = function (event) {
            var data = JSON.parse(event.data);
            if (data.device === undefined) { return; }
            var device_id = data.device.split('/')[1];
            var marker = undefined;
            for (m in markers) {
                if (markers[m].did == device_id) {
                    marker = markers[m].markerObj;
                    break;
                }
            }
            var icon_src = 'http://maps.google.com/mapfiles/ms/icons/green-dot.png';
            if (data.tick > 0) {
                // put did into rains_in
                var index = rains_in.indexOf(device_id);
                if (index == -1) {
                    rains_in.push(device_id);
                }
                icon_src = 'http://maps.google.com/mapfiles/ms/icons/yellow-dot.png';
                //icon_src = '/static/images/marker/gray_rain_2.gif';
            } else {
                var index = rains_in.indexOf(device_id);
                if (index > -1) {
                    rains_in.splice(device_id, 1);
                }

            }
            if (marker != undefined) {
                setIcon(marker, icon_src);
            }
        }
        var markers = [];
        var rains_in = [];
        var primaIds = """ + str(all_prima) + """;
        function setIcon(marker, icon_src='http://maps.google.com/mapfiles/ms/icons/green-dot.png') {
            marker.setIcon(icon_src);
        }
        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
    {
        "featureType": "all",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "weight": "2.00"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "color": "#9c9c9c"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "all",
        "stylers": [
            {
                "color": "#f2f2f2"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "landscape.man_made",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "saturation": -100
            },
            {
                "lightness": 45
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#eeeeee"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#7b7b7b"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "road.highway",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "elementType": "labels.icon",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "transit",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "all",
        "stylers": [
            {
                "color": "#46bcec"
            },
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#88b6f2" /* "#c8d7d4" */
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#000000"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    }
],
                mapTypeId: google.maps.MapTypeId.TERRAIN };
            var map = new google.maps.Map(document.getElementById('map'), my_options);
            var lamong_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/lamong.kml?v=1',
                preserveViewport: true, map: map});
            var lamong_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/grindulu_lorog.kml?v=1',
                preserveViewport: true, map: map});
            var pantura_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/pantura.kml?v=2',
                preserveViewport: true, map: map});
            var hilir_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hilir.kml?v=2',
                preserveViewport: true, map: map});
            var madiun_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/madiun.kml?v=2',
                preserveViewport: true, map: map});
            var hulu_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hulu.kml?v=2',
                preserveViewport: true, map: map});
          var allPos = """ + str(all_pos) + """;
          var infoWindow = new google.maps.InfoWindow;
          _.each(allPos, function(pos) {
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
                map: map,
                optimized: false,
                title: pos.name + ' (' + pos.device + ')',
                position: point
            })
            markers.push({id: pos.id, did: pos.device, markerObj: marker});
            bind_info_window(marker, map, infoWindow, "<a href='/curahhujan/"+pos.id+"' style='font-weight: bold;font-size: 16px;'>"+ pos.name + "</a>");
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        """
        return render.map.curahhujan({'poses': agents, 'js_foot': js_foot})


class MapTma:
    def GET(self):
        HIDE_THIS = [a.strip() for a in open('HIDE_AWLR.txt').read().split(',')]
        agents = Agent.select(AND(OR(Agent.q.AgentType == HIDROLOGI,
                                     Agent.q.AgentType == 0),
                                  Agent.q.expose == True)).orderBy(
                                      ["wilayah", "-DPL", "-siaga3"])
        agents = [a for a in agents if a.table_name not in HIDE_THIS]
        all_pos = [{'id': a.AgentId, 'name': a.cname, 'll': a.ll} for a in agents]
        js_foot = """
        <script type="text/template" id="pos_infowindow">
          <div class="item infowindow" id="pos_<%= index %>">
            <span class="pos"><%= name %> </span>
            <span class="meter">
            </span>
          </div>
        </script>
        <script>
        var ws = new WebSocket('ws://mqtt.bbws-bsolo.net:22286');
        ws.onmessage = function (event) {
            var data = JSON.parse(event.data);
            if (data.device === undefined) { return; }
            var device_id = data.device.split('/')[1];
            var marker = undefined;
            for (m in markers) {
                if (markers[m].did == device_id) {
                    marker = markers[m].markerObj;
                    break;
                }
            }
        }
        function init_map() {
            var my_options = {
                center: new google.maps.LatLng(-7.49592,111.568909),
                zoom: 9,
                styles: [
    {
        "featureType": "all",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "weight": "2.00"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "geometry.stroke",
        "stylers": [
            {
                "color": "#9c9c9c"
            }
        ]
    },
    {
        "featureType": "all",
        "elementType": "labels.text",
        "stylers": [
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "all",
        "stylers": [
            {
                "color": "#f2f2f2"
            }
        ]
    },
    {
        "featureType": "landscape",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "landscape.man_made",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "poi",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "all",
        "stylers": [
            {
                "saturation": -100
            },
            {
                "lightness": 45
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#eeeeee"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#7b7b7b"
            }
        ]
    },
    {
        "featureType": "road",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    },
    {
        "featureType": "road.highway",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "simplified"
            }
        ]
    },
    {
        "featureType": "road.arterial",
        "elementType": "labels.icon",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "transit",
        "elementType": "all",
        "stylers": [
            {
                "visibility": "off"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "all",
        "stylers": [
            {
                "saturation": 100
            },
            {
                "lightness": 15
            },
            {
                "color": "#88b6f2" /* "#466cec" */
            },
            {
                "visibility": "on"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "geometry.fill",
        "stylers": [
            {
                "color": "#88b6f2"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.fill",
        "stylers": [
            {
                "color": "#000000"
            }
        ]
    },
    {
        "featureType": "water",
        "elementType": "labels.text.stroke",
        "stylers": [
            {
                "color": "#ffffff"
            }
        ]
    }
],
                mapTypeId: google.maps.MapTypeId.TERRAIN };
            var map = new google.maps.Map(document.getElementById('map'), my_options);
            var lamong_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/lamong.kml?v=1',
                preserveViewport: true, map: map});
            var pantura_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/pantura.kml?v=1',
                preserveViewport: true, map: map});
            var hilir_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hilir.kml?v=1',
                preserveViewport: true, map: map});
            var madiun_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/madiun.kml?v=1',
                preserveViewport: true, map: map});
            var hulu_line = new google.maps.KmlLayer(
                {url: 'http://hidrologi.bbws-bsolo.net/static/hulu.kml?v=1',
                preserveViewport: true, map: map});
          var allPos = """ + str(all_pos) + """;
          var markers = {};
          var infoWindow = new google.maps.InfoWindow;
          _.each(allPos, function(pos) {
            var lat = parseFloat(pos.ll.split(',')[0]);
            var lng = parseFloat(pos.ll.split(',')[1]);
            var point = new google.maps.LatLng(lat, lng);
            var marker = new google.maps.Marker({
                icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                map: map,
                position: point
            });
            markers[pos.id] = marker;
            bind_info_window(marker, map, infoWindow, "<a href='/tma/"+pos.id+"' style='font-weight: bold;font-size: 16px;'>"+ pos.name + "</a>");
          });
        };
        function bind_info_window(marker, map, infowindow, html) {
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(html);
                infowindow.open(map, marker);
            })
        };
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAmnJGdC-ZhVd98H3mwMRv2GU2dlv1D7IA&callback=init_map"></script>
        """
        return render.map.tma({'poses': agents, 'js_foot': js_foot})
