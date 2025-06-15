// Frontend fix for Autonomous Monitor
// Clear WebSocket cache and reconnect

// Add this to browser console on Autonomous Monitor page:
if (window.autonomousWS) {
    window.autonomousWS.close();
    window.autonomousWS = null;
}

// Force data refresh
localStorage.removeItem('autonomousData');
sessionStorage.clear();

// Reload the page
window.location.reload();