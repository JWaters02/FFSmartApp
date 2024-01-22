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
            var itemName = card.querySelector('.item-name');
            var quantityInput = card.querySelector('.item-quantity');
            var expiryDateInput = card.querySelector('.item-expiry-date');

            var expiryDateParts = expiryDateInput.value.split('-');
            var expiryDateUTC = Date.UTC(expiryDateParts[0], expiryDateParts[1] - 1, expiryDateParts[2]);
            var expiryTimestamp = Math.floor(expiryDateUTC / 1000);

            var item = {
                order_id: orderId,
                item_name: itemName.value,
                quantity: quantityInput.value,
                expiry_date: expiryTimestamp
            };
            orderItems.push(item);
        });
        console.log(orderItems)

        fetch('/delivery/complete_order/' + getRestaurantId() + '/' + getToken(), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({items: orderItems})
        }).then(response => response.json())
        .then(data => {
            if(data.success) {
                changeDoorState(false);
                location.reload();
                sendFlashMessage(data.message, 'success');

                setTimeout(function() {
                    endDelivery();
                }, 5000);
            } else {
                sendFlashMessage(data.message, 'danger');
            }
        }).catch(error => {
            console.error('Error:', error);
            sendFlashMessage(error, 'danger');
        });
    });
}

function endDelivery() {
    fetch('/delivery/end_delivery/' + getRestaurantId() + '/' + getToken(), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
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