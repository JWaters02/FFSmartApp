/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview verify.js - contains all the logic for verification using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let userPool;

document.addEventListener('DOMContentLoaded', async function () {
    const poolData = JSON.parse(localStorage.getItem('poolData'));
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
});

document.getElementById("verify").addEventListener("click", function () {
    let username = document.getElementById("usernameVerify").value;
    let code = document.getElementById("codeVerify").value;

    var userData = {
        Username: username,
        Pool: userPool
    };

    var cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
    cognitoUser.confirmRegistration(code, true, function (err, result) {
        if (err) {
            if (err.code === 'InvalidParameterException') {
                sendFlashMessage('Invalid verification code, please check your details and try again.', 'danger').then(() => {
                    window.location.href = "/verify";
                });
            } else {
                sendFlashMessage('Verification error, please check your details and try again.', 'danger').then(() => {
                    window.location.href = "/verify";
                });
            }
            return;
        }

        console.log('call result: ' + result);
        if(result === 'SUCCESS') {
            sendFlashMessage('Verification successful.', 'success').then(() => {
                window.location.href = "/";
            });
        } else {
            sendFlashMessage('An issue occurred, please try again.', 'danger').then(() => {
                window.location.href = "/verify";
            });
        }
    });
});