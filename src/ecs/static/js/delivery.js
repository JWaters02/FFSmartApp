document.getElementById("doorButton").addEventListener("click", function(event) {
    event.preventDefault();

    var isBackDoorOpen = "{{ is_back_door_open }}" === 'true';
    console.log("isBackDoorOpen: ", isBackDoorOpen);
    var url = isBackDoorOpen 
        ? "/delivery/close_door/{{ restaurant_id }}/{{ token }}/"
        : "/delivery/open_door/{{ restaurant_id }}/{{ token }}/"; 

    fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    }).then(response => response.json())
    .then(data => {
        if(data.success) {
            location.reload();
        } else {
            sendFlashMessage("Operation failed!");
        }
    }).catch(error => {
        console.error("Error:", error);
        sendFlashMessage("Error:", error);
    });
});
