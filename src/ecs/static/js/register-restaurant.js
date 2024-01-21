/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview register-restaurant.js - contains all the logic for registering using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let cognitoUser;
let userPool;

async function registerRestaurant(restaurantName) {
    const formData = new FormData();
    formData.append('username', restaurantName);

    console.log('Register rest has been called')

    try {
        const response = await fetch('/register-restaurant', {
            method: 'POST',
            body: formData
        });

        console.log(response)

        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }

        const data = await response.text();
        console.log('Success:', data);

    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    const poolData = JSON.parse(localStorage.getItem('poolData'));
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));
});

document.getElementById("register").addEventListener("click", async function () {
    let username = document.getElementById("usernameRegister").value;
    let password = document.getElementById("passwordRegister").value;
    let email = document.getElementById("emailRegister").value;

    let attributeList = [];

    let dataEmail = {
        Name: 'email',
        Value: email,
    }

    let attributeEmail = new AmazonCognitoIdentity.CognitoUserAttribute(dataEmail);

    attributeList.push(attributeEmail);

    userPool.signUp(username, password, attributeList, null, async function(err, result) {
        if (err) {
            sendFlashMessage(err)
            console.log(err);
        } else {
            sendFlashMessage('Registered successfully, please verify your account, and check your email.');
            window.location.href = "/verify";
            let cognitoUser = result.user;
            sessionStorage.setItem('cognitoUser', JSON.stringify(cognitoUser));

            await registerRestaurant(username);
        }
    });
});
