// Motion layer, built with GSAP + ScrollTrigger (tokens and recipes from the taste skill's motion reference):
// - the title block arrives in 1.2 s: masked line rise, sentence and byline, the stage opening, the chips;
// - every section's parts enter once, staggered, as they reach the screen (ScrollTrigger.batch);
// - figures open like a shutter; the gallery photographs drift with the scroll (the moving picture);
// - the headline numbers roll up to their real values.
// Transform and opacity only. With prefers-reduced-motion, everything is shown at once and nothing travels.
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);
document.documentElement.classList.add("gsap");   // cancels the CSS failsafe

const EASE = { out: "power3.out", expo: "expo.out", inOut: "power4.inOut" };
const ALWAYS_VISIBLE = ".limits [data-reveal], .letter [data-reveal], .refs [data-reveal]";   // long lists never start invisible

// Numbers that roll up: "0.74", "21 ms", "60"; the final text is already in the HTML
function rollUp(el) {
  const match = el.textContent.trim().match(/^(\d+(?:\.\d+)?)(.*)$/);
  if (!match) return;
  const [, number, suffix] = match;
  const decimals = (number.split(".")[1] ?? "").length;
  const state = { value: 0 };
  gsap.to(state, {
    value: Number(number), duration: 1.4, ease: EASE.expo,
    onUpdate: () => { el.textContent = state.value.toFixed(decimals) + suffix; },
    scrollTrigger: { trigger: el, start: "top 90%", once: true },
  });
}

const mm = gsap.matchMedia();
mm.add({ motion: "(prefers-reduced-motion: no-preference)", still: "(prefers-reduced-motion: reduce)" }, ({ conditions }) => {
  if (conditions.still) {
    gsap.set(".hero [data-line], .hero [data-load], .chip, .stage", { clearProps: "transform,clipPath", opacity: 1, visibility: "inherit" });
    return;
  }

  // 1. Title block (the signature move: a masked headline), settled by about 1.2 s
  gsap.timeline({ defaults: { ease: EASE.expo } })
    // y: 0 on both ends: GSAP would otherwise read the CSS pre-paint translateY(105%) into y and keep it
    .fromTo(".hero [data-line]", { y: 0, yPercent: 105 }, { y: 0, yPercent: 0, duration: 0.9, stagger: 0.11 }, 0.15)
    .fromTo(".hero [data-load]", { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: 0.55, stagger: 0.05, ease: EASE.out }, 0.42)
    .fromTo(".stage", { clipPath: "inset(0% 0% 100% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.0, ease: EASE.inOut }, 0.15)
    .fromTo(".detector__photo", { scale: 1.06 }, { scale: 1, duration: 1.4 }, 0.12)
    .fromTo(".chip", { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.6, stagger: 0.08, ease: EASE.out }, 0.78);

  // 2. Entrances: heading, then text, then picture, 70 ms apart, once
  const enter = [...document.querySelectorAll("[data-reveal]:not(.wide)")].filter((el) => !el.matches(ALWAYS_VISIBLE));
  gsap.set(enter, { autoAlpha: 0, y: 24 });
  ScrollTrigger.batch(enter, {
    start: "top 92%", once: true,
    onEnter: (batch) => gsap.to(batch, { autoAlpha: 1, y: 0, duration: 0.7, stagger: 0.07, ease: EASE.out, overwrite: true }),
  });
  const soft = gsap.utils.toArray(ALWAYS_VISIBLE);
  gsap.set(soft, { y: 18 });
  ScrollTrigger.batch(soft, {
    start: "top 95%", once: true,
    onEnter: (batch) => gsap.to(batch, { y: 0, duration: 0.6, stagger: 0.04, ease: EASE.out, overwrite: true }),
  });

  // 3. Figures open like a shutter while their picture settles
  gsap.utils.toArray(".wide[data-reveal]").forEach((figure) => {
    const picture = figure.querySelector("img");
    gsap.timeline({ scrollTrigger: { trigger: figure, start: "top 85%", once: true } })
      .fromTo(figure, { clipPath: "inset(0% 0% 100% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 1.1, ease: EASE.inOut })
      .fromTo(picture, { scale: 1.08 }, { scale: 1, duration: 1.5, ease: "power2.out" }, 0);
  });

  // 4. The moving picture: gallery photographs drift with the scroll (scrubbed, linear)
  gsap.utils.toArray(".tile img").forEach((img) => {
    gsap.fromTo(img, { yPercent: -5, scale: 1.12 }, {
      yPercent: 5, scale: 1.12, ease: "none",
      scrollTrigger: { trigger: img.closest(".tile"), start: "top bottom", end: "bottom top", scrub: true },
    });
  });

  // 5. The proofs and the dataset total roll up to their real values
  gsap.utils.toArray(".proofs__figure, .receipt__figure").forEach(rollUp);

  // 6. The report sheet swaps with a short crossfade (the click handler lives in live.js)
  document.querySelectorAll("[data-report]").forEach((button) => button.addEventListener("click", () => {
    const sheet = document.querySelector(`[data-sheet="${button.dataset.report}"]`);
    if (sheet) gsap.fromTo(sheet, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.32, ease: EASE.out });
  }));
});

// Images that load late change the page height: keep every trigger in the right place
window.addEventListener("load", () => ScrollTrigger.refresh());
