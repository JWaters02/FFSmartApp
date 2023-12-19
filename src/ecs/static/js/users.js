
document.addEventListener("DOMContentLoaded", function () {
    const removeButtons = document.querySelectorAll('.remove-user-btn');
    const editButtons = document.querySelectorAll('.edit-user-btn');

    removeButtons.forEach(function (button) {
        button.addEventListener('click', async function () {
            const formData = new FormData();
            formData.append('usernameToDelete', this.getAttribute('data-username'));
            formData.append('accessToken', sessionStorage.getItem('accessToken'));

            const response = await fetch('/remove-user', {
                method: 'DELETE',
                body: formData
            });

            if (!response.ok) {
                alert('User was not removed correctly, please try again later.');
                console.error('Error:', 'Network response was not ok: ' + response.statusText);
                return;
            }

            alert('User removed successfully.');
            window.location.href = "/users";
        })
    })

    editButtons.forEach(function (button) {
        button.addEventListener('click', async function () {
            const username = this.getAttribute('data-username');
            const email = this.getAttribute('data-email');
            const jobRole = this.getAttribute('data-role');

            window.location.href = `/edit-user?username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}&jobRole=${encodeURIComponent(jobRole)}`;
        })
    })
})

document.getElementById("create-new-user").addEventListener("click", async function () {

    if(document.getElementById("role").value === "") {
        alert("Please select a job role.");
        return;
    }

    let emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/;
    if(!document.getElementById("email").value.match(emailPattern)) {
        alert("Email field must be a valid email address.");
        return;
    }

    const formData = new FormData();
    formData.append('username', document.getElementById("username").value);
    formData.append('email', document.getElementById("email").value);
    formData.append('role', document.getElementById("role").value);
    formData.append('restaurant_id', sessionStorage.getItem("username"));
    formData.append('accessToken', sessionStorage.getItem('accessToken'));

    const response = await fetch('/register-user', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        alert('User was not created, please ensure that the entered values are correct.');
        console.error('Error:', 'Network response was not ok: ' + response.statusText);
        return;
    }

    alert('User created successfully.');
    window.location.href = "/users";
});
