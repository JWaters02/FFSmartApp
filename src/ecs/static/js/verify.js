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
    const poolData = JSON.parse(localStorage.getItem('userPool'));
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
            alert(err);
            return;
        }

        console.log('call result: ' + result);
        if(result === 'SUCCESS') {
            alert('Verification was successful.');
            window.location.href = "/";
        } else {
            alert('An issue occurred, please try again.');
        }
    });
});