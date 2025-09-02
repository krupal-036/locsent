document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const storedTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.body.setAttribute('data-theme', storedTheme);
    themeToggle.addEventListener('click', () => {
        let newTheme = document.body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    if (document.getElementById('send-location-btn')) {
        setInterval(sendLocation, 3600000);
    }

    if (document.getElementById('live-map')) {
        initializeAdminMap();
    } else if (document.getElementById('user-map')) {
        initializeUserMap();
    }

    const openGuideBtn = document.getElementById('open-guide-btn');
    const closeGuideBtn = document.getElementById('close-guide-btn');
    const guideModal = document.getElementById('guide-modal');

    if (openGuideBtn && closeGuideBtn && guideModal) {
        openGuideBtn.addEventListener('click', (e) => {
            e.preventDefault();
            guideModal.classList.add('modal-active');
        });

        closeGuideBtn.addEventListener('click', () => {
            guideModal.classList.remove('modal-active');
        });

        guideModal.addEventListener('click', (e) => {
            if (e.target === guideModal) {
                guideModal.classList.remove('modal-active');
            }
        });
    }
});

let userMap;
let userMarker;
function initializeUserMap() {
    userMap = L.map('user-map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(userMap);
    drawGeofences(userMap);
    updateUserMarker();
    setInterval(updateUserMarker, 20000);
}
function updateUserMarker() {
    navigator.geolocation.getCurrentPosition(position => {
        const { latitude, longitude } = position.coords;
        const latLng = [latitude, longitude];
        if (userMarker) {
            userMarker.setLatLng(latLng);
        } else {
            userMarker = L.marker(latLng).addTo(userMap).bindPopup('<b>Your Location</b>').openPopup();
            userMap.setView(latLng, 13);
        }
    }, (error) => {
        console.error("Could not get user location:", error.message);
    }, { enableHighAccuracy: true });
}
async function sendLocation() {
    const statusEl = document.getElementById('status-message');
    const buttonEl = document.getElementById('send-location-btn');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    if (!navigator.geolocation) {
        if (statusEl) statusEl.textContent = 'Geolocation is not supported.';
        return;
    }
    if (buttonEl) buttonEl.disabled = true;
    if (statusEl) statusEl.textContent = 'Getting your location...';
    try {
        const position = await new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
        });
        const { latitude, longitude } = position.coords;
        let batteryInfo = 'N/A';
        if ('getBattery' in navigator) {
            const battery = await navigator.getBattery();
            batteryInfo = `Charging: ${battery.charging ? 'Yes' : 'No'}, Level: ${Math.round(battery.level * 100)}%`;
        }
        const deviceInfo = navigator.userAgent;
        if (statusEl) statusEl.textContent = 'Sending to admin...';
        const response = await fetch('/user/send_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ latitude, longitude, battery: batteryInfo, deviceInfo: deviceInfo })
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'Request failed with status: ' + response.status }));
            throw new Error(errorData.message || 'Failed to send location.');
        }
        const data = await response.json();
        if (statusEl) statusEl.textContent = data.message;
    } catch (error) {
        if (statusEl) statusEl.textContent = `Error: ${error.message}`;
    } finally {
        if (buttonEl) buttonEl.disabled = false;
        setTimeout(() => {
            if (statusEl) statusEl.textContent = '';
        }, 5000);
    }
}

let adminMap;
let userMarkers = {};
function initializeAdminMap() {
    adminMap = L.map('live-map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(adminMap);
    drawGeofences(adminMap);
    updateAdminMapMarkers();
    setInterval(updateAdminMapMarkers, 30000);
}
async function updateAdminMapMarkers() {
    try {
        const response = await fetch('/admin/api/get_all_latest_locations');
        if (!response.ok) throw new Error('Failed to fetch locations');
        const locations = await response.json();
        locations.forEach(user => {
            const { username, latitude, longitude, timestamp, battery } = user;
            if (latitude && longitude) {
                const popupContent = `<b>${username}</b><br>Updated: ${new Date(timestamp).toLocaleString()}<br>Battery: ${battery}`;
                if (userMarkers[username]) {
                    userMarkers[username].setLatLng([latitude, longitude]).setPopupContent(popupContent);
                } else {
                    userMarkers[username] = L.marker([latitude, longitude]).addTo(adminMap).bindPopup(popupContent);
                }
            }
        });
    } catch (error) {
        console.error("Admin Map Marker Update Error:", error);
    }
}

async function drawGeofences(mapInstance) {
    try {
        const response = await fetch('/api/get_geofences');
        if (!response.ok) throw new Error('Failed to fetch geofences');
        const zones = await response.json();
        zones.forEach(zone => {
            if (zone.lat && zone.lon && zone.radius) {
                L.circle([zone.lat, zone.lon], {
                    color: '#ff4d4d',
                    fillColor: '#ff8080',
                    fillOpacity: 0.2,
                    radius: zone.radius
                }).addTo(mapInstance).bindPopup(`<b>Geofence:</b> ${zone.name}`);
            }
        });
    } catch (error) {
        console.error("Geofence Drawing Error:", error);
    }
}
async function fetchLocationHistory(userPageId, username) {
    const detailsCard = document.getElementById('location-details-card');
    const contentDiv = document.getElementById('location-details-content');
    const usernameSpan = document.getElementById('details-username');
    detailsCard.classList.remove('hidden');
    usernameSpan.textContent = username;
    contentDiv.innerHTML = '<p class="loading-text">Fetching location data...</p>';
    try {
        const response = await fetch(`/admin/get_location_history/${userPageId}`);
        if (!response.ok) throw new Error('Network response was not ok.');
        const data = await response.json();
        if (data.length > 0) {
            const latest = data[0];
            const googleMapsUrl = `https://www.google.com/maps?q=${latest.latitude},${latest.longitude}`;
            let historyHtml = data.map(log => {
                const mapUrl = `https://www.google.com/maps?q=${log.latitude},${log.longitude}`;
                return `<li><div class="history-item-details"><span>${new Date(log.timestamp).toLocaleString()}</span><span>Lat: ${log.latitude.toFixed(4)}, Lon: ${log.longitude.toFixed(4)}</span></div><a href="${mapUrl}" target="_blank" class="btn-map">Open Map</a></li>`;
            }).join('');
            contentDiv.innerHTML = `<div class="location-info"><p><strong>Latest Coordinates:</strong> ${latest.latitude}, ${latest.longitude}</p><p><strong>IP Address:</strong> ${latest.ip_address}</p><p><strong>Battery Status:</strong> ${latest.battery}</p><a href="${googleMapsUrl}" target="_blank" class="btn btn-secondary">Open Latest in Google Maps</a></div><hr><h4>Location History (Last 10)</h4><ul class="location-history-list">${historyHtml}</ul>`;
        } else {
            contentDiv.innerHTML = '<p>No location data found for this user.</p>';
        }
    } catch (error) {
        contentDiv.innerHTML = `<p class="alert alert-danger">Error fetching data: ${error.message}</p>`;
    }
}