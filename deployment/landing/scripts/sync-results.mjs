// Copy the evaluation results and a few figures produced by the notebooks into the site,
// so every number on the page comes from reports/results/test_results.json (notebook 5).
import { copyFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..");
const results = join(repo, "reports", "results", "test_results.json");
const target = join(here, "..", "src", "data", "results.json");
mkdirSync(dirname(target), { recursive: true });
if (existsSync(results)) {
  copyFileSync(results, target);
  console.log("results: copied", results);
} else {
  writeFileSync(target, JSON.stringify({ models: {}, paired_differences: [] }));
  console.warn("results: reports/results/test_results.json not found (run notebook 5); the page shows no numbers");
}
const figures = ["A_01_learning_curves.png", "5_01_test_predictions.png", "6_01_xai_board_success.png"];
mkdirSync(join(here, "..", "public", "figures"), { recursive: true });
for (const name of figures) {
  const source = join(repo, "reports", "figures", name);
  if (existsSync(source)) copyFileSync(source, join(here, "..", "public", "figures", name));
}
