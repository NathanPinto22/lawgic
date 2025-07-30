function sessionValid() {
  return false;
}

function toggleClass(element, className) {
  console.log("toggling");
  if (element.classList.contains(className)) {
    element.classList.remove(className);
  } else {
    element.classList.add(className);
  }
}

const accTray = document.getElementById("account-tray");
document.addEventListener("DOMContentLoaded", () => {
  if (sessionValid()) {
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
      console.log("Clicked!");
      toggleClass(optionList, "d-flex");
      console.log("toggled");
    });
    accTray.appendChild(profileIcon);
    accTray.appendChild(optionList);
  } else {
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
