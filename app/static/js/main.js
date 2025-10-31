// Presence monitoring popup and sound
function showPresenceAlert(message, soundEnabled) {
    alert(message);
    if (soundEnabled) {
        var audio = new Audio('/static/sound/notify.mp3');
        audio.play();
    }
}
// Future: implement periodic popup and auto-absent logic
