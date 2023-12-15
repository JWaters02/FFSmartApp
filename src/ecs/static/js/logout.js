/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview logout.js - contains all the logic logging out using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));
let accessToken = sessionStorage.getItem('accessToken');

document.getElementById("logout").addEventListener("click", function () {
    accessToken = null;
    fetch('/logout/', {})
        .then(function (response) {
            if (response.status !== 200) {
                console.log('Error: ' + response.status);
                return;
            }
            console.log('Logged out');
        });
    cognitoUser.signOut();
    sessionStorage.clear();
});