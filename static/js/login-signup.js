function signup() {
  console.log("signing up!");
  form = document.getElementById("sign-up-form");
  formData = new FormData(form);
  fetch("/sign-up-acc", {
    method: "POST",
    body: formData,
  });
}

function login() {
  form = document.getElementById("login-form");
  formData = new FormData(form);
  fetch("/login-acc", {
    method: "POST",
    body: formData,
  });
}
