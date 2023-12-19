/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview logout.js - contains all the logic logging out using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

let accessToken;
let cognitoUser;

document.addEventListener('DOMContentLoaded', async function () {
    accessToken = sessionStorage.getItem('accessToken');

    const poolData = await JSON.parse(localStorage.getItem("userPool"));
    const username = sessionStorage.getItem("username");
    console.log(poolData);
    console.log(username);

    let userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    let userData = {
        Username: username,
        Pool: userPool,
    }
    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);
});

document.getElementById("logout").addEventListener("click", async function () {
    accessToken = null;

    try {
        const response = await fetch('/logout/', {});

        if (response.status !== 200) {
            console.log('Error: ' + response.status);
            return;
        }

        console.log('Logged out');
    } catch (error) {
        console.error('Error:', error);
    }

    if (cognitoUser) {
        cognitoUser.signOut();
    }

    console.log(sessionStorage.getItem("username"));
    sessionStorage.clear();
    console.log(sessionStorage.getItem("username"));

    alert('Logout successful.');
    window.location.href = "/";
});
