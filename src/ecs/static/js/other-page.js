
document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM loaded");
    let username = sessionStorage.getItem("username");
    document.getElementById("current-user").innerHTML = "Logged in as: " + username;
});
