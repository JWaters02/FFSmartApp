
document.getElementById("edit-user").addEventListener("click", async function () {
    const formData = new FormData();
    formData.append('username', this.getAttribute('data-username'));
    formData.append('newRole', document.getElementById("role").value);
    formData.append('accessToken', sessionStorage.getItem('accessToken'));

    const response = await fetch('/edit-user', {
        method: 'POST',
        body: formData
    });

    if(!response.ok) {
        sendFlashMessage('User was not updated.', 'danger');
    } else {
        window.location.href = "/users";
        sendFlashMessage('User updated successfully.', 'success');
    }
});
