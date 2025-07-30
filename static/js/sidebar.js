// Sidebar toggle
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebar = document.getElementById("sidebar");
const mainContainer = document.getElementById("main-container");
sidebarToggle.style.color = "#000000";

sidebarToggle.addEventListener("click", () => {
  console.log(sidebarToggle.style.color);
  const color = {
    "rgb(0, 0, 0)": "rgb(255, 255, 255)",
    "rgb(255, 255, 255)": "rgb(0, 0, 0)",
  };

  sidebarToggle.style.color = color[sidebarToggle.style.color];
  sidebarToggle.style.display = "inline";
});

function hideHero() {
  const hero = document.getElementById("hero");
  if (!hero.classList.contains("hidden")) {
    hero.classList.add("hidden");
  } else return;
}

// Sidebar population
