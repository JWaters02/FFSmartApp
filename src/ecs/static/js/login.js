/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview login.js - contains all the logic for logging in using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let cognitoUser;
let userPool;
let accessToken;

function updateLogin() {
    if (accessToken) {
        cognitoUser.getUserAttributes(function (err, result) {
            if (err) {
                return;
            }

            for (let i = 0; i < result.length; i++) {
                switch (result[i].getName()) {
                    case "email":
                        sessionStorage.setItem("email", result[i].getValue());
                        break;
                    case "sub":
                        sessionStorage.setItem("sub", result[i].getValue());
                        break;
                }
            }
        });
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    const poolData = JSON.parse(localStorage.getItem("poolData"));
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    cognitoUser = JSON.parse(sessionStorage.getItem("cognitoUser"));
    accessToken = sessionStorage.getItem("accessToken");
});

async function updateCredentials(username, userData, accessToken) {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('userData', userData);
    formData.append('accessToken', accessToken);

    try {
        const response = await fetch('/update-credentials', {
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

document.getElementById("login").addEventListener("click", function () {
    let username = document.getElementById("usernameLogin").value;
    let password = document.getElementById("passwordLogin").value;

    var authenticationData = {
        Username: username,
        Password: password,
    }
    var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
    var userData = {
        Username: username,
        Pool: userPool,
    }
    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: async function (result) {
            accessToken = result.getAccessToken().getJwtToken();
            sessionStorage.setItem("accessToken", accessToken);
            sessionStorage.setItem("userData", JSON.stringify(userData));
            sessionStorage.setItem("username", username);
            await updateCredentials(username, JSON.stringify(userData), accessToken);
            updateLogin();

            window.location.href = "/home";
        },
        newPasswordRequired: function (userAttributes, requiredAttributes) {
            sendFlashMessage('New password required.', 'warning').then(() => {
                window.location.href = "/new-password";
            });
        },
        onFailure: function (err) {
            if (err.code === "InvalidParameterException") {
                sendFlashMessage('Please fill in username and password!', 'warning').then(() => {
                    window.location.href = "/";
                });
            } else if (err.code === "NotAuthorizedException") {
                sendFlashMessage('Incorrect username or password!', 'warning').then(() => {
                    window.location.href = "/";
                });
            }
        }
    });
});
