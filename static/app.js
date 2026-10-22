document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash) => {
    const isError = flash.classList.contains("danger");
    flash.setAttribute("role", isError ? "alert" : "status");
    flash.setAttribute("aria-live", isError ? "assertive" : "polite");
  });

  const toggle = document.querySelector(".nav-toggle");
  const navigation = document.getElementById("primary-navigation");
  if (toggle && navigation) {
    toggle.addEventListener("click", () => {
      const isOpen = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!isOpen));
      toggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
      navigation.classList.toggle("is-open", !isOpen);
    });
  }
});
