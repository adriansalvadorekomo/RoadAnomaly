// The paper's navigation, driven by ScrollTrigger:
// - the running head names the section being read (as a printed paper's header does);
// - the contents rail marks that section and appears once the title block has been read;
// - a filled bar under the running head shows how far the reader is.
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const head = document.querySelector("[data-running-head]");
const rail = document.querySelector(".rail");
const links = new Map([...document.querySelectorAll("[data-toc]")].map((a) => [a.dataset.toc, a]));
const title = head?.textContent ?? "";
const still = window.matchMedia("(prefers-reduced-motion: reduce)");

function setHead(text) {
  if (!head || head.textContent === text) return;
  if (still.matches) { head.textContent = text; return; }
  gsap.timeline()
    .to(head, { autoAlpha: 0, yPercent: -40, duration: 0.16, ease: "power2.in" })
    .call(() => { head.textContent = text; })
    .fromTo(head, { autoAlpha: 0, yPercent: 40 }, { autoAlpha: 1, yPercent: 0, duration: 0.28, ease: "power3.out" });
}

function setCurrent(id) {
  links.forEach((a, key) => (key === id ? a.setAttribute("aria-current", "true") : a.removeAttribute("aria-current")));
}

// Each section takes over the running head while its body crosses the middle of the screen
document.querySelectorAll("[data-section]").forEach((section) => {
  ScrollTrigger.create({
    trigger: section, start: "top 50%", end: "bottom 50%",
    onToggle: ({ isActive }) => {
      if (!isActive) return;
      setHead(section.dataset.section);
      if (section.id) setCurrent(section.id);
    },
  });
});

// Back above the abstract: the title returns, the rail hides. The state is applied on load and on every
// refresh too, so a visitor who arrives mid-page (anchor link, reload) gets the rail straight away.
let railShown = null;
function showRail(show, animate = true) {
  if (!rail || railShown === show) return;
  railShown = show;
  const duration = animate && !still.matches ? 0.3 : 0;
  if (show) {
    rail.classList.add("is-shown");
    gsap.fromTo(rail, { autoAlpha: 0, x: -12 }, { autoAlpha: 1, x: 0, duration, ease: "power2.out" });
  } else {
    gsap.to(rail, { autoAlpha: 0, x: -12, duration, ease: "power2.in", onComplete: () => rail.classList.remove("is-shown") });
  }
}
ScrollTrigger.create({
  trigger: ".hero", start: "top bottom", end: "bottom 40%",
  onToggle: ({ isActive }) => {
    if (isActive) { setHead(title); setCurrent(null); }
    showRail(!isActive);
  },
  onRefresh: (self) => showRail(!self.isActive, false),
});

// Reading progress: a filled bar scrubbed by the scroll
gsap.to(".runhead__progress", { scaleX: 1, ease: "none", scrollTrigger: { start: 0, end: "max", scrub: 0.3 } });

// Closing the contents menu after a choice on phones
document.querySelectorAll(".toc-menu a").forEach((a) => a.addEventListener("click", () => a.closest("details")?.removeAttribute("open")));
