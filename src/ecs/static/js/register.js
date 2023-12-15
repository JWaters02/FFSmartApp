/**
 * @author ben lewis-jones
 * @author joshua waters
 * @version 1.0
 * @fileoverview register.js - contains all the logic for registering using aws cognito
 *
 * @requires NPM:aws-sdk
 * @note to add more cognito logic to the login page, please look at https://github.com/aws-amplify/amplify-js/tree/master/packages/amazon-cognito-identity-js
 * */

const region = "{{ region }}";
const userPoolId = "{{ user_pool_id }}";
const clientId = "{{ client_id }}";
let cognitoUser = JSON.parse(sessionStorage.getItem('cognitoUser'));

var poolData = {
    UserPoolId: userPoolId,
    ClientId: clientId,
};
var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

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
            // flash the error message (from flask)
            console.log(err);
            return;
        }
        var cognitoUser = result.user;
        sessionStorage.setItem('cognitoUser', JSON.stringify(cognitoUser));
        console.log('user name is ' + cognitoUser.getUsername());
    });
});
