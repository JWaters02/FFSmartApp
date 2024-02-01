document.addEventListener('DOMContentLoaded', async function () {
    await fetchConfig();
});

async function fetchConfig() {

    // no need to get fetch data if we already have it
    if(localStorage.getItem('userPoolId') != null &&
        localStorage.getItem('clientId') != null &&
        localStorage.getItem('region') != null) {
        return
    }

    try {
        const response = await fetch('/config');
        const data = await response.json();

        // local storage is used over session storage, because this data will be redundant on host
        localStorage.setItem('userPoolId', data.user_pool_id);
        localStorage.setItem('clientId', data.client_id);
        localStorage.setItem('region', data.region);

        const poolData = {
            UserPoolId: data.user_pool_id,
            ClientId: data.client_id,
        };

        localStorage.setItem('poolData', JSON.stringify(poolData));
        console.log(localStorage.getItem('poolData'));
        console.log(localStorage.getItem('region'));

    } catch (error) {
        console.error('Error:', error);
    }
}

function sendFlashMessage(message, category) {
    return fetch('/flash', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message, category: category })
    })
    .then(response => response.json())
    .then(data => {
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
