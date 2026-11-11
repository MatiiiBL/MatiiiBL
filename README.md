<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Matías Blanco. Computer Engineering at Columbia University. I build performance-critical software from scratch, from SIMD vector search to LLM inference engines." src="assets/banner-light.svg" width="100%">
</picture>

I'm a Computer Engineering student at Columbia (AI minor, class of 2029), originally from Montevideo. I like problems where the code has to be fast *and* right. I profile before I optimize, check every fast path against a slow reference, and benchmark against the libraries people already use.

Right now I'm an AI engineer at **Forva Systems**, building the AI backend of an EMS platform for ambulance crews, and I'm on **Columbia Formula Racing**.

[LinkedIn](https://www.linkedin.com/in/matias-blanco-uy/) · [matias.blancobalaguer@columbia.edu](mailto:matias.blancobalaguer@columbia.edu)

### Selected work

<a href="https://github.com/MatiiiBL/HNSW_vector_search">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/vecdex-dark.svg">
    <img alt="vecdex: HNSW vector search in C++20. 18,000 queries/s at 96.4% recall@10 on SIFT1M, 1.78× FAISS HNSW with the same parameters, and a 1M-vector build in 28 s on 10 threads." src="assets/vecdex-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MatiiiBL/LLM-inference-engine">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/minillm-dark.svg">
    <img alt="minillm: a from-scratch Llama-architecture inference engine in C++20 running SmolLM2-135M. Greedy tokens match PyTorch exactly; Q8_0 weights are 3.8× smaller." src="assets/minillm-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MateoVidalS/makecu-guante">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/memo-dark.svg">
    <img alt="memo, AI category winner at makeCU: a tendon-driven stroke-rehab glove. I owned the webcam hand tracking." src="assets/memo-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MatiiiBL/housing-energy-assistance">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/wattsgood-dark.svg">
    <img alt="WattsGood, 1st place at an 8-hour hackathon: three orchestrated Claude agents that match households to energy assistance." src="assets/wattsgood-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MatiiiBL/ShellC">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/shellc-dark.svg">
    <img alt="ShellC: a bash-like Unix shell in C with no heap allocation." src="assets/shellc-light.svg" width="100%">
  </picture>
</a>

### Experience

**Forva Systems** · AI Engineer · New York · Dec 2025 – present<br>
AI backend of an EMS platform for EMTs and paramedics. I designed the anti-hallucination guardrails for clinical LLM extraction (schema-constrained outputs, verbatim-quote provenance, gap-aware context windows, human sign-off on every medication) and a dev/held-out eval harness that scores word error rate, medical-term survival and number grounding.

**Y Combinator Startup School** · Selected participant · San Francisco · Jul 2026<br>
Picked from 30,000+ applicants. In the 48-hour build sprint I wrote an agentic Python pipeline that runs parallel LLM summarization over 2,000+ research PDFs.

**AdAstra** · Software Engineer Intern · Montevideo · Sep – Dec 2024<br>
Full-stack social platform in C#, React, PostgreSQL and Python. Deployed Gemma 3 on-premise to flag AI-generated images and stop fraud.

### Toolbox

**Systems** &nbsp; `C++20` `C` `CMake` `NEON SIMD` `POSIX` `Linux`<br>
**Correctness** &nbsp; `ASan` `UBSan` `TSan` `libFuzzer` `Valgrind` `GitHub Actions`<br>
**ML** &nbsp; `PyTorch` `NumPy` `pybind11` `safetensors` `MediaPipe` `LLM agents & evals`<br>
**Product** &nbsp; `TypeScript` `React` `Node.js` `C# / ASP.NET Core` `PostgreSQL` `Flutter`

Spanish (native) · English (fluent) · Portuguese (advanced) · Chinese (learning)

<sub>The graphics on this page are drawn by <a href="scripts/render.py">scripts/render.py</a>; the vecdex chart plots the project's raw benchmark CSVs.</sub>
