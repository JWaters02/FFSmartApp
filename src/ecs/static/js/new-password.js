let cognitoUser;
let userPool;
let accessToken;

document.addEventListener("DOMContentLoaded", async function () {
    const poolData = JSON.parse(localStorage.getItem("userPool"));
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
});

document.getElementById("UpdatePassword").addEventListener("click", function () {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;
    let newPassword = document.getElementById("newPassword").value;

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
        onSuccess: function (result) {},
        onFailure: function (err) {
            console.error(err);
        },
        newPasswordRequired: function(userAttributes, requiredAttributes) {
            delete userAttributes.email_verified;
            delete userAttributes.email;

            cognitoUser.completeNewPasswordChallenge(newPassword, userAttributes, {
                onSuccess: function(result) {
                    alert('Password updated successfully, please login');
                    window.location.href = "/";
                },
                onFailure: function(err) {
                    alert(err);
                }
            });
        }
    });
});