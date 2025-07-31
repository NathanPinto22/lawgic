function adjustLayout() {
  const inputCard = document.getElementById("input-card");
  const hero = document.getElementById("hero");
  if (document.getElementById("chat-container").innerHTML.trim() != "") {
    if (!hero.classList.contains("hidden")) hero.classList.add("hidden");
    if (inputCard.classList.contains("fixed-input-card")) return;
    inputCard.classList.add("fixed-input-card");
  } else {
    if (hero.classList.contains("hidden")) hero.classList.remove("hidden");
    if (!inputCard.classList.contains("fixed-input-card")) return;
    inputCard.classList.remove("fixed-input-card");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  adjustLayout();
});

const targetNode = document.getElementById("chat-container");

const observer = new MutationObserver((mutationsList, observer) => {
  for (let mutation of mutationsList) {
    if (mutation.type === "childList" || mutation.type === "characterData") {
      console.log("innerHTML changed:", targetNode.innerHTML);
      adjustLayout();
    }
  }
});

observer.observe(targetNode, {
  childList: true,
  characterData: true,
  subtree: true,
});

function updateChatIdInUrl(chatId) {
  const url = new URL(window.location);
  url.pathname = chatId;
  window.history.replaceState({}, "", url);
}

function handleSubmit() {
  const form = document.getElementById("chat-form");
  const queryTextInput = document.getElementById("query-text");
  const queryText = queryTextInput.value;
  const chatContainer = document.getElementById("chat-container");

  if (queryText) {
    const userChatBubble = document.createElement("div");
    userChatBubble.classList.add(...["chat-bubble", "user-bubble"]);

    userChatBubble.innerText = queryText;
    chatContainer.appendChild(userChatBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  } else return;

  formData = new FormData(form);

  const chatID = window.location.pathname.substring(1);

  formData.append("chat-id", chatID);
  console.log(formData);

  fetch("/chat", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (window.location.pathname.substring(1) == "")
        updateChatIdInUrl(data.chatID);

      const aiChatBubble = document.createElement("div");
      aiChatBubble.classList.add(...["chat-bubble", "ai-bubble"]);

      aiChatBubble.innerHTML = data.reply;

      chatContainer.appendChild(aiChatBubble);

      chatContainer.scrollTop = chatContainer.scrollHeight;
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

document.getElementById("send-btn").addEventListener("click", handleSubmit);

shiftDown = false;
document.addEventListener("keydown", (e) => {
  if (e.key == "Shift") shiftDown = true;
  const queryTextInput = document.getElementById("query-text");

  if (shiftDown && e.key == "Enter") return;
  else if (e.key == "Enter" && queryTextInput.focus) {
    const queryTextInput = document.getElementById("query-text");
    handleSubmit();
    queryTextInput.value = "";
  } else return;
});

document.addEventListener("keyup", (e) => {
  if (e.key == "Shift") shiftDown = false;
  console.log("Shift released");
});
