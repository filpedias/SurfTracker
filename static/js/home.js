const weekday = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];

/**
 * Updates data from Strava by making an AJAX request to the Strava sync API.
 * Displays success or error messages using Toastr library.
 * After a successful update, it fetches GPX data for sessions.
 */
function update_data_from_strava() {
    let url = "/api/i/strava/sync/";

    $.ajax({
        url: url,
        type: "GET",
        async: true,
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            /**
             * Handles the response from the Strava sync API.
             * If the status is "ok," displays a success message.
             * If the status is "error," displays error messages.
             * Finally, fetches sessions GPX data.
             * @param {Object} response - The response from the Strava sync API.
             */
            if (response["status"] == "ok") {
                toastr.success('Activities synced with Strava', 'Updated', { timeOut: 2000 })
            } else if (response["status"] == "error") {
                response["msg"].forEach(function(error_msg) {
                    toastr.error(error_msg, 'Error', { timeOut: 2000 })
                })
            }
            fetch_sessions_gpx_data()
        }
    });
}


/**
 * Processes GPX data for sessions by iterating through each session and drawing the session map.
 * After processing, hides Leafleet logos on the map.
 * @param {Array} gpxs_data - Array of GPX data for sessions.
 */
function process_sessions_data(gpxs_data) {
    gpxs_data.forEach(function(s) {
        draw_session_map(s)
    });
    hide_leafleet_logos()
}

/**
 * Hides Leafleet logos on the map.
 */
function hide_leafleet_logos() {
    leafleet_logos = document.getElementsByClassName("leaflet-control-attribution")
    for (var i = 0; i < leafleet_logos.length; i++) {
        leafleet_logos[i].style.display = 'none';
    }
}

/**
 * Draws a session map using Leaflet library and Google Satellite tiles.
 * Calculates the average coordinates and sets the map view accordingly.
 * @param {Object} session - Session data containing wave points.
 */
function draw_session_map(session) {
    map = L.map('map_' + session.session_id)
    google_sat_url = 'http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
    googleSat = L.tileLayer(google_sat_url, {
        maxZoom: 18,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
    }).addTo(map);

    sum_lat = 0
    sum_long = 0
    count_points = 0

    session["wave_points"].forEach(function(array_of_points) {
        wave_line = []
        array_of_points.forEach(function(point) {
            wave_line.push([point.latitude, point.longitude])
            count_points += 1
            sum_lat += point.latitude
            sum_long += point.longitude
        })
        polyline = L.polyline(wave_line, { color: 'blue' }).addTo(map)
    })
    if (count_points > 0) {
        avg_lat = sum_lat / count_points
        avg_long = sum_long / count_points
        map.setView([avg_lat, avg_long], 19)
    }
}

/**
 * Fetches GPX data for sessions by making an AJAX request to the sessions GPX data API.
 * Processes the response data and calls the process_sessions_data function.
 */
function fetch_sessions_gpx_data() {

    $.ajax({
        url: "/api/i/sessions/gpx_data/",
        type: "GET",
        async: true,
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            /**
             * Handles the response from the sessions GPX data API.
             * If the status is "ok," processes the sessions data.
             * @param {Object} response - The response from the sessions GPX data API.
             */
            if (response["status"] == "ok") {
                user_sessions_data = response["data"]["gpxs_data"]
                process_sessions_data(user_sessions_data)
            }
        }
    });
}

const last_sessions_chart_options = {
    scales: {
        y: {
            grid: {
                display: false
            }
        }, x: {
            grid: {
                display: false
            }
        }
    },
    plugins: {
        scales: {
            y: {
                beginAtZero: true                
            }
        }, legend: {
            display: false
        }
    }
}

function draw_chart(ctx_last_sessions, labels_days, data){
    if (typeof last_sessions_chart !== 'undefined') {
        last_sessions_chart.destroy()
    }
    
    last_sessions_chart = new Chart(ctx_last_sessions, {
        type: 'bar',
        data: {
          labels: labels_days,
          datasets: [{            
            data: data,
            borderWidth: 1
          }]
        },
        options: last_sessions_chart_options
      });
}


function AddOrSubractDays(startingDate, number, add) {
    if (add) {
      return new Date(new Date().setDate(startingDate.getDate() + number));
    } else {
      return new Date(new Date().setDate(startingDate.getDate() - number));
    }
}

function get_last_days_sessions() {

    const ctx_last_sessions = document.getElementById('last_days_chart');
    
    labels_days = []
    for (let i=6; i >= 0; i--){
        day = AddOrSubractDays(new Date(), i, false)
        //labels_days.push(w/eekday[day.getDay()])
        labels_days.push(`${day.getDate()}/${day.getMonth() + 1}`);
    }
    
    // fill div with default data
    draw_chart(ctx_last_sessions, labels_days, [2, 0, 3, 1, 0, 1.5])


    $.ajax({
        url: `/api/i/sessions/last_days/${7}`,
        type: "GET",
        async: true,
        contentType: 'application/json; charset=utf-8',
        success: function(response) {
            if (response["status"] == "ok") {
                data = response["data"]["sessions"]
            }
        }, error: function(response){
            alert("Error drawing last days sessions chart")
            data = [0,0,0,0,0,0,0]
        }, complete: function(response){
            $("#div_last_7_days").removeClass("loading-div")
            draw_chart(ctx_last_sessions, labels_days, data)
        }
        
    });
    

    
}