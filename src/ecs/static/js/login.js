/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview login.js - contains all the logic for logging in using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));
let accessToken = sessionStorage.getItem('accessToken');
let userPoolId, clientId, region, userPool;

fetchConfig();

function fetchConfig() {
    fetch('/config')
        .then(response => response.json())
        .then(data => {
            userPoolId = data.user_pool_id;
            clientId = data.client_id;
            region = data.region;
            var poolData = {
                UserPoolId: userPoolId,
                ClientId: clientId,
            };
            userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

function updateLogin() {
    if (accessToken) {
        // get the username
        cognitoUser.getUserAttributes(function (err, result) {
            // check for error
            if (err) {
                alert(err);
                return;
            }
            console.log("result");
            for (let i = 0; i < result.length; i++) {
                switch (result[i].getName()) {
                    case 'email':
                        sessionStorage.setItem("email", result[i].getValue());
                        break;
                    case 'sub':
                        sessionStorage.setItem("sub", result[i].getValue());
                        break;
                }
            }
        });
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
        onSuccess: function (result) {
            accessToken = result.getAccessToken().getJwtToken();
            sessionStorage.setItem('accessToken', accessToken);
            sessionStorage.setItem('cognitoUser', JSON.stringify(cognitoUser));
            sessionStorage.setItem("username", username);
            updateLogin();
            document.getElementById("current-login").innerHTML = "Logged in as: " + username;
        },
        onFailure: function (err) {
            alert(err.message);
        }
    });
});