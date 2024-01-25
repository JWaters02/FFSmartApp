function getRestaurantId() {
    var segments = window.location.pathname.split('/');
    return segments[2];
}

function getToken() {
    var segments = window.location.pathname.split('/');
    return segments[3];
}

var openDoorElement = document.getElementById("openDoor");
if (openDoorElement) {
    openDoorElement.addEventListener("click", function() {
        changeDoorState(true);
    });
}

var completeOrderButton = document.getElementById("completeOrderButton");
if (completeOrderButton) {
    completeOrderButton.addEventListener("click", function() {
        var orderItems = [];
        var itemCards = document.querySelectorAll('.card-body');
        itemCards.forEach(function(card) {
            var orderId = card.querySelector('.card-title').textContent;
            var itemName = card.querySelector('.item-name').getAttribute("data-item-name");
            var quantityInput = card.querySelector('.item-quantity');
            var expiryDateInput = card.querySelector('.item-expiry-date');

            var expiryDateParts = expiryDateInput.value.split('-');
            var expiryDateUTC = Date.UTC(expiryDateParts[0], expiryDateParts[1] - 1, expiryDateParts[2]);
            var expiryTimestamp = Math.floor(expiryDateUTC / 1000);

            var item = {
                order_id: orderId,
                item_name: itemName,
                quantity: quantityInput.value,
                expiry_date: expiryTimestamp
            };
            orderItems.push(item);
        });

        fetch('/delivery/complete_order/' + getRestaurantId() + '/' + getToken(), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({items: orderItems})
        }).then(response => response.json())
        .then(data => {
            if(data.success) {
                changeDoorState(false);
                sendFlashMessage(data.message, 'success');
                endDelivery();
            } else {
                if (data.retry_items && data.retry_items.length > 0) {
                    localStorage.setItem('retry_items', JSON.stringify(data.retry_items));
                    sendRetryItemsToServer().then(() => {
                        window.location.href = '/delivery/' + getRestaurantId() + '/' + getToken() + '/';
                    }).catch(error => {
                        console.error('Failed to send retry items:', error);
                    });
                } else {
                    alert(data.message);
                }
            }
        }).catch(error => {
            console.error('Error:', error);
            alert(error);
        });
    });
}

function sendRetryItemsToServer() {
    return new Promise((resolve, reject) => {
        const retryItems = localStorage.getItem('retry_items');
        if (retryItems) {
            fetch('/delivery/update_retry_items/' + getRestaurantId() + '/' + getToken(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ retry_items: JSON.parse(retryItems) }),
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                resolve(data);
            })
            .catch((error) => {
                console.error('Error:', error);
                reject(error);
            });
        } else {
            resolve();
        }
    });
}

function endDelivery() {
    fetch('/delivery/end_delivery/' + getRestaurantId() + '/' + getToken(), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    }).then(response => response.json())
    .then(data => {
        if(data.success) {
            window.location.href = '/404/'
        } else {
            window.location.href = '/404/'
            sendFlashMessage(data.message, 'danger');
        }
    }).catch(error => {
        location.reload();
        console.error('Error:', error);
        window.location.href = '/404/'
    });
}

function changeDoorState(state) {
    var payload = {
        is_back_door_open: state
    };

    console.log(payload);

    fetch('/delivery/' + getRestaurantId() + '/' + getToken() + '/', {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(response => response.json())
    .then(data => {
        if(data.success) {
            location.reload();
        } else {
            sendFlashMessage(data.message, 'danger');
        }
    }).catch(error => {
        console.error('Error:', error);
        sendFlashMessage(error, 'danger');
    });
}