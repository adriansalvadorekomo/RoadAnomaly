// Static landing page; the demo (Streamlit) and the API (FastAPI) run separately (see the README).
import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static",
  site: "http://localhost:4321",
});
