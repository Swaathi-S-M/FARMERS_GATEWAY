const API_URL = "http://127.0.0.1:5000";

console.log("✅ script.js loaded successfully!");

// ✅ Ensure script runs only when DOM is fully loaded
document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();  // Prevent page refresh

            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            if (email && password) {
                alert("Login successful!");
                window.location.href = "location.html";  // ✅ Redirect to location selection
            } else {
                alert("Please enter a valid email and password.");
            }
        });
    } else {
        console.error("⚠️ Login form not found!");
    }
});

// ✅ Map Variables
let map;
let marker;
let selectedLocation = null; // Stores user's selected location

// ✅ Global Function: Initialize Google Map
window.initMap = function (lat = 28.6139, lng = 77.2090) {  
    console.log("Initializing map at:", { lat, lng });

    map = new google.maps.Map(document.getElementById("map"), {
        center: { lat, lng },
        zoom: 14,
    });

    marker = new google.maps.Marker({
        position: { lat, lng },
        map: map,
        draggable: true
    });

    // ✅ Update location when marker is moved
    marker.addListener("dragend", () => {
        selectedLocation = {
            lat: marker.getPosition().lat(),
            lng: marker.getPosition().lng()
        };
        console.log("📌 Marker moved:", selectedLocation);
    });

    selectedLocation = { lat, lng };
};

// ✅ Global Function: Get Current Location (GPS)
window.getCurrentLocation = function () {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                selectedLocation = { lat, lng };
                console.log("📍 Current location:", selectedLocation);
                initMap(lat, lng);
            },
            () => alert("⚠️ Location access denied!")
        );
    } else {
        alert("⚠️ Geolocation is not supported by this browser.");
    }
};

// ✅ Global Function: Google Places API (Search Box)
window.initAutocomplete = function () {
    const input = document.getElementById("searchBox");
    const autocomplete = new google.maps.places.Autocomplete(input);

    autocomplete.addListener("place_changed", function () {
        const place = autocomplete.getPlace();
        if (place.geometry) {
            const lat = place.geometry.location.lat();
            const lng = place.geometry.location.lng();
            selectedLocation = { lat, lng };
            console.log("🔎 Location selected:", selectedLocation);
            initMap(lat, lng);
        }
    });
};

// ✅ Global Function: Confirm Location & Proceed
window.confirmLocation = function () {
    if (selectedLocation) {
        alert(`✅ Location confirmed:\nLatitude: ${selectedLocation.lat}\nLongitude: ${selectedLocation.lng}`);
        console.log("✔️ Location confirmed:", selectedLocation);
    } else {
        alert("⚠️ Please select a location first.");
    }
};

// ✅ Ensure Map & Autocomplete load properly
window.onload = function () { 
    initMap(); 
    initAutocomplete();
};
