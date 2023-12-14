/**
 * @author ben lewis-jones
 * @version 1.0
 * @fileoverview login.js - contains all the logic for signing in, registering and logging out using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

const region = 'eu-west-1'; // TODO: should be stored on the flask app
const userPoolId = 'eu-west-1_BGeP1szQM'; // TODO: should be stored on the flask app
const clientId = '3368pjmkt1q1nlqg48duhbikgn'; // TODO: should be stored on the flask app
let cognitoUser; // TODO: should be stored in session storage
let accessToken; // TODO: should be stored in session storage

var poolData = {
    UserPoolId: userPoolId,
    ClientId: clientId,
};
var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

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
            sessionStorage.setItem("username", username);
            updateLogin();
            document.getElementById("current-login").innerHTML = "Logged in as: " + username;
        },
        onFailure: function (err) {
            alert(err.message);
        }
    });
});

document.getElementById("register").addEventListener("click", function () {
    let username = document.getElementById("usernameRegister").value;
    let password = document.getElementById("passwordRegister").value;
    let email = document.getElementById("emailRegister").value;

    console.log(username);
    console.log(password);
    console.log(email);

    var attributeList = [];

    var dataEmail = {
        Name: 'email',
        Value: email,
    }

    var attributeEmail = new AmazonCognitoIdentity.CognitoUserAttribute(dataEmail);

    attributeList.push(attributeEmail);

    userPool.signUp(username, password, attributeList, null, function (err, result) {
        if (err) {
            console.log(err);
            return;
        }
        var cognitoUser = result.user;
        console.log('user name is ' + cognitoUser.getUsername());
    });
});

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
    document.getElementById("current-login").innerHTML = "Not logged in";
    sessionStorage.clear();
});
