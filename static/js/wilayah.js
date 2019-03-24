// This example creates a simple polygon representing the Bermuda Triangle.
// When the user clicks on the polygon an info window opens, showing
// information about the polygon's coordinates.

var map;
var infoWindow;

function initMap() {
    $.get(url, function (results, status) {

        var infoWindow = new google.maps.InfoWindow(), marker, i;
        var bounds = new google.maps.LatLngBounds();

        map = new google.maps.Map(document.getElementById('map'), {
            minZoom: 5,
            zoom: 8,
            center: {lat: -7.5871248, lng: 111.7464579},
            mapTypeId: 'terrain'
        });
        map.setOptions({
            scrollwheel: true,
            disableDoubleClickZoom: true
        });

        var image = base_url+'/static/images/marker/map-marker.png';

        if (typeof uri !== 'undefined') {
            switch(uri){
                case 'curahhujan':
                    image = base_url+'/static/images/marker/map-marker.png';
                    results = results.filter(function(el){ return el.type==1 || el.type==0});
                    break;
                case 'tma':
                    image = base_url+'/static/images/marker/map-marker-2.png';
                    results = results.filter(function(el){ return el.type==2 });
                    break;
                case 'kekeringan':
                    image = base_url+'/static/images/marker/map-marker-3.png';
                    break;
                case 'kualitasair':
                    image = base_url+'/static/images/marker/map-marker-4.png';
                    break;
                case 'bendungan':
                    image = base_url+'/static/images/marker/map-marker-5.png';
                    break;
            }
        }

        for (i = 0; i < results.length; i++) {
            var data = results[i];
            var coords = data.latlng.split(",");
            var position = new google.maps.LatLng(coords[0], coords[1]);
            bounds.extend(position);
            marker = new google.maps.Marker({
                position: position,
                map: map,
                icon: image,
                title: data.name
            });

            // Allow each marker to have an info window
            google.maps.event.addListener(marker, 'click', (function(marker, i) {
                return function() {
                    infoWindow.setContent('<a href="'+base_url+uri+'/'+results[i].id+'">'+results[i].name+'</a>');
                    infoWindow.open(map, marker);
                }
            })(marker, i));

            // Automatically center the map fitting all markers on the screen
            //map.fitBounds(bounds);
        }

        /*var boundsListener = google.maps.event.addListener((map), 'bounds_changed', function(event) {
            this.setZoom(14);
            google.maps.event.removeListener(boundsListener);
        });*/

        var strictBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(-8, 110.795596),
            new google.maps.LatLng(-6, 112.210146)
        );

        // Listen for the CENTER_CHANGED event

        google.maps.event.addListener(map, 'center_changed', function() {
            if (strictBounds.contains(map.getCenter())) return;

            // We're out of bounds - Move the map back within the bounds

            var c = map.getCenter(),
                x = c.lng(),
                y = c.lat(),
                maxX = strictBounds.getNorthEast().lng(),
                maxY = strictBounds.getNorthEast().lat(),
                minX = strictBounds.getSouthWest().lng(),
                minY = strictBounds.getSouthWest().lat();

            if (x < minX) x = minX;
            if (x > maxX) x = maxX;
            if (y < minY) y = minY;
            if (y > maxY) y = maxY;

            map.setCenter(new google.maps.LatLng(y, x));
        });

        // Construct the polygon.
        var wilayahHulu = new google.maps.Polygon({
            paths: hulu,
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'green',
            fillOpacity: 0.2
        });
        wilayahHulu.setMap(map);

        // Add a listener for the click event.
        wilayahHulu.addListener('click', showArrays, {wilayah: 'hulu'});

        // Construct the polygon.
        var wilayahGrindulu = new google.maps.Polygon({
            paths: grindulu,
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'yellow',
            fillOpacity: 0.2
        });
        wilayahGrindulu.setMap(map);

        // Add a listener for the click event.
        wilayahGrindulu.addListener('click', showArrays);

        // Construct the polygon.
        var wilayahLamong = new google.maps.Polygon({
            paths: lamong,
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'orange',
            fillOpacity: 0.2
        });
        wilayahLamong.setMap(map);

        // Add a listener for the click event.
        wilayahLamong.addListener('click', showArrays);


        // Construct the polygon.
        var wilayahPantai = new google.maps.Polygon({
            paths: pantai,
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'red',
            fillOpacity: 0.2
        });
        wilayahPantai.setMap(map);

        // Add a listener for the click event.
        wilayahPantai.addListener('click', showArrays);

        // Construct the polygon.
        var wilayahMadiun = new google.maps.Polygon({
            paths: madiun,
            wilayah: '2',
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'blue',
            fillOpacity: 0.2
        });
        wilayahMadiun.setMap(map);

        // Add a listener for the click event.
        wilayahMadiun.addListener('click', showArrays, {wilayah: 'madiun'});


        // Construct the polygon.
        var wilayahHilir = new google.maps.Polygon({
            paths: hilir,
            wilayah: '3',
            strokeColor: 'black',
            strokeOpacity: 1,
            strokeWeight: 1.75,
            fillColor: 'pink',
            fillOpacity: 0.2
        });
        wilayahHilir.setMap(map);

        // Add a listener for the click event.
        wilayahHilir.addListener('click', showArrays, {wilayah: 'hilir'});
    });

    // Replace the info window's content and position.
    infoWindow = new google.maps.InfoWindow();

}

/** {google maps Polygon} */
function showArrays(event) {
  console.log(this.wilayah);
  var vertices = this.getPath();
  var contentString = '<div id="iw-container">' +
                        '<div class="iw-title">Wilayah Hulu</div>' +
                        '<div class="iw-content">' +
                        '<div class="row">' +
                        '<div class="list-group">' +
                          '<div class="col-md-6">' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '1. Bendung Colo</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '2. Gunungan</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '3. Jatisrono</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '4. Jurug</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '5. Kalijambe</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '6. Karangpandan</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '7. Klaten</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '8. Nepen</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '9. Pabelan</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '10.Parangjoho</a>' +
                            '</div>' +
                          '<div class="col-md-6">' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '11.Pracimantoro Colo</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '12.Purwantoro</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '13.Rejoso</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '14.Sragen</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '15.Tangen Bridge 2</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '16.Twangmangu</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '17.Tritis</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '18.Waduk Delingan</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '19.Waduk_Nawangan</a>' +
                              '<a class="list-group-item" href="https://www.google.com">'+ '20.Wonogiri</a>' +
                            '</div>' +
                        '</div>' +
                        '</div>' +
                        '</div>' +
                        '<div class="iw-bottom-gradient"></div>' +
                      '</div>';

    infoWindow.setContent(contentString);
    infoWindow.setPosition(event.latLng);
    infoWindow.open(map);

}
