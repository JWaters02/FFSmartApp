/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview verify.js - contains all the logic for verification using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

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

document.getElementById("verify").addEventListener("click", function () {
    let username = document.getElementById("usernameVerify").value;
    let code = document.getElementById("codeVerify").value;

    console.log(username);
    console.log(code);

    var userData = {
        Username: username,
        Pool: userPool
    };

    var cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    cognitoUser.confirmRegistration(code, true, function (err, result) {
        if (err) {
            alert(err);
            return;
        }
        console.log('call result: ' + result);
    });
});