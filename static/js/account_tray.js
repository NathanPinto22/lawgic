// function sessionValid() {
//   fetch("/session-valid", {
//     method: "POST",
//     body: "",
//   })
//     .then((response) => response.json())
//     .then((data) => {
//       console.log(data.valid);
//       return data.valid;
//     })
//     .catch((error) => {
//       console.error("Error validating session: ", error);
//       return false;
//     });
// }

function toggleClass(element, className) {
  if (element.classList.contains(className)) {
    element.classList.remove(className);
  } else {
    element.classList.add(className);
  }
}

const accTray = document.getElementById("account-tray");
document.addEventListener("DOMContentLoaded", async () => {
  const isValid = await sessionValid("account_tray.js");
  if (isValid) {
    console.log("Valid Session");
    const profileIcon = document.createElement("div");
    const profileImage = document.createElement("img");
    profileImage.src = "";
    const optionList = document.createElement("div");
    optionList.classList.add(...["options-list", "flex-column", "hidden"]);
    options = [
      { action: "Manage chats", link: "/manage-chats" },
      { action: "Sign out", link: "/sign-out" },
    ];
    for (option of options) {
      const opt = document.createElement("a");
      opt.innerText = option.action;
      opt.href = option.link;
      optionList.appendChild(opt);
    }

    profileIcon.appendChild(profileImage);
    profileIcon.classList.add(...["profile-icon"]);

    profileIcon.addEventListener("click", () => {
      toggleClass(optionList, "d-flex");
    });
    accTray.appendChild(profileIcon);
    accTray.appendChild(optionList);
  } else {
    console.log("Invalid Session");
    const signUpBtn = document.createElement("button");
    const loginBtn = document.createElement("button");

    signUpBtn.id = "sign-up";
    signUpBtn.classList.add(...["btn", "btn-light"]);
    signUpBtn.innerText = "Sign up";
    signUpBtn.onclick = () => {
      window.location.href = "/sign-up";
    };
    accTray.appendChild(signUpBtn);

    loginBtn.id = "login";
    loginBtn.classList.add(...["btn", "btn-dark"]);
    loginBtn.innerText = "Log in";
    loginBtn.onclick = () => {
      window.location.href = "/login";
    };
    accTray.appendChild(loginBtn);

    document.getElementById(
      window.location.pathname.substring(1)
    ).disabled = true;
  }
});
