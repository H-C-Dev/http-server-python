document.addEventListener("DOMContentLoaded", function () {
  const p = document.querySelector("p");
  if (p) {
    p.textContent += " with app.js";
  }
});
