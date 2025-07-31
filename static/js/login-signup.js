function signup() {
  console.log("signing up!");
  form = document.getElementById("sign-up-form");
  formData = new FormData(form);
  fetch("/sign-up-acc", {
    method: "POST",
    body: formData,
  }).then((res) => {
    if (res.redirected) {
      window.location.href = res.url;
    }
  });
}

function login() {
  form = document.getElementById("login-form");
  formData = new FormData(form);
  console.log("Authenticating...");
  fetch("/login-acc", {
    method: "POST",
    body: formData,
  }).then((res) => {
    if (res.redirected) {
      window.location.href = res.url;
    }
  });
}
