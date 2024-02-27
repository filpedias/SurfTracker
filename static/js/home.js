
update_data_from_strava();



function update_data_from_strava() {
    let url = "/api/i/strava/sync/"; 
    
    $.ajax({
      url: url,
      type: "GET",
      async: true,
      contentType: 'application/json; charset=utf-8',
      success: function(response) {
        if (response["status"] == "ok"){
            toastr.success('Activities synced with strava', 'Updated', {timeOut: 2000})
        } else if (response["status"] == "error"){
            response["msg"].forEach(function(error_msg){
                toastr.error(error_msg, 'Error', {timeOut: 2000})
            })                
        }
        fetch_sessions_gpx_data()
      }
    });
   
}

function click_update_strava(){
    window.location='/strava/login/';
}

// iterar as atividades, aponta para as coordenadas do spot e desenha o GPX
function process_sessions_data(gpxs_data) {
    gpxs_data.forEach(function(s){
        draw_session_map(s)
    });
    hide_leafleet_logos()
}


function hide_leafleet_logos(){
    leafleet_logos = document.getElementsByClassName("leaflet-control-attribution")
    for(var i=0; i < leafleet_logos.length; i++){
        leafleet_logos[i].style.display = 'none';
    }
}

function draw_session_map(session) {
    map = L.map('map_' + session.session_id)
    google_sat_url = 'http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
    googleSat = L.tileLayer(google_sat_url, {
        maxZoom: 18,
        subdomains:['mt0','mt1','mt2','mt3']
    }).addTo(map);

    // avg coordinates
    sum_lat = 0
    sum_long = 0
    count_points = 0

    session["wave_points"].forEach(function(array_of_points){
        wave_line = []
        array_of_points.forEach(function(point){
            wave_line.push([point.latitude, point.longitude])
            count_points += 1
            sum_lat += point.latitude
            sum_long += point.longitude
        })
        polyline = L.polyline(wave_line, {color: 'blue'}).addTo(map)
    })
    if(count_points > 0) {
        avg_lat = sum_lat/count_points
        avg_long = sum_long/count_points
        map.setView([avg_lat, avg_long], 19)
    }
}


function fetch_sessions_gpx_data() {
    let url = "/api/i/sessions/gpx_data/"; 
    
    $.ajax({
      url: url,
      type: "GET",
      async: true,
      contentType: 'application/json; charset=utf-8',
      success: function(response) {
        if (response["status"] == "ok"){
            process_sessions_data(response["data"]["gpxs_data"])         
        }
      }
    });
   
}