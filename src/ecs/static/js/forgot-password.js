let cognitoUser;
let userPool;

document.addEventListener("DOMContentLoaded", async function () {
    const poolData = {
        UserPoolId: localStorage.getItem('userPoolId'),
        ClientId: localStorage.getItem('clientId'),
    };
    console.log(poolData)
    userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
    console.log(userPool)
});

document.getElementById("submitResetPassword").addEventListener("click", () => {
    var username = document.getElementById('username').value;

    var userData = {
        Username: username,
        Pool: userPool
    }

    cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cognitoUser.forgotPassword({
        onSuccess: function(data) {
            console.log(data)
            console.log('CodeDeliveryData from forgotPassword: ' + data);
            document.getElementById('forgotPasswordRequest').style.display = 'none';
            document.getElementById('resetPassword').style.display = 'block';
        },
        onFailure: function(err) {
            console.log(err)
            alert(err.message || JSON.stringify(err));
        }
    });
})

document.getElementById("submitNewPassword").addEventListener("click", () => {
    var code = document.getElementById('code').value;
    var newPassword = document.getElementById('newPassword').value;

    document.getElementById('codeError').innerText = ''
    document.getElementById('passwordError').innerText = ''

    cognitoUser.confirmPassword(code, newPassword, {
        onSuccess() {
            sendFlashMessage('New password has been set.', 'success').then(() => {
                window.location.href = "/";
            });
        },
        onFailure(err) {
            console.log('Password not confirmed: ' + err);
            if (err.name === 'CodeMismatchException') {
                document.getElementById('codeError').innerText = 'The code provided is not valid.';
            } else if (err.name === 'InvalidParameterException' || err.name === 'InvalidPasswordException') {
                document.getElementById('passwordError').innerText = 'Password must have at least: 8 Characters, 1 number, 1 special character, 1 uppercase, and 1 lowercase';
            } else {
                document.getElementById('codeError').innerText = 'Something went wrong! Please try again.';
            }
        },
    });
})
