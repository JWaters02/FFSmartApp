let cognitoUser;
let userPool;
let accessToken;

document.addEventListener("DOMContentLoaded", async function () {
    const poolData = JSON.parse(localStorage.getItem("poolData"));
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
            sendFlashMessage('An error occured setting your new password, please check your details are correct.', 'danger').then(() => {
                window.location.href = "/new-password";
            });
        },
        newPasswordRequired: function(userAttributes, requiredAttributes) {
            delete userAttributes.email_verified;
            delete userAttributes.email;

            cognitoUser.completeNewPasswordChallenge(newPassword, userAttributes, {
                onSuccess: function(result) {
                    sendFlashMessage('Password updated successfully, please login.', 'success').then(() => {
                        window.location.href = "/";
                    });
                },
                onFailure: function(err) {
                    sendFlashMessage('An error occured setting your new password, please check your details are correct.', 'danger').then(() => {
                        window.location.href = "/new-password";
                    });
                }
            });
        }
    });
});