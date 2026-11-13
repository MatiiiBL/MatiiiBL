<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.svg">
  <img alt="Matías Blanco. Computer Engineering at Columbia University. I build fast, verified systems from scratch: a RISC-V SoC, driverless racing, a tensor compiler." src="assets/banner-light.svg" width="100%">
</picture>

I'm a Computer Engineering student at Columbia (AI minor, class of 2029), originally from Montevideo. I like problems where the system has to be fast *and* right, from RTL and robotics to ML compilers and LLM pipelines. I profile before I optimize, check every fast path against a slow reference, and benchmark against the libraries people already use.

Right now I'm an AI engineer at **Forva Systems**, building the AI backend of an EMS platform for ambulance crews, and I'm on **Columbia Formula Racing**.

[LinkedIn](https://www.linkedin.com/in/matias-blanco-uy/) · [matias.blancobalaguer@columbia.edu](mailto:matias.blancobalaguer@columbia.edu)

### Selected work

<a href="https://github.com/MatiiiBL/riscv-npu-soc">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/pulse-dark.svg">
    <img alt="Pulse: a RISC-V SoC in SystemVerilog, a 5-stage RV32IM CPU driving an 8×8 INT8 systolic-array NPU. MNIST runs 115× faster on the NPU than on the CPU, the NPU sustains 58.9 of 64 MACs per cycle, and the CPU scores 2.86 CoreMark/MHz at 40 MHz on an ECP5 FPGA." src="assets/pulse-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MatiiiBL/apex-driverless">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/apex-dark.svg">
    <img alt="Apex: an autonomous Formula Student Driverless stack in C++20 and the simulator it races in. Lap 1 maps an unseen cone track with LiDAR, camera and EKF-SLAM; laps 2 to 10 race a minimum-curvature raceline with MPC. 33 of 33 ten-lap runs on unseen tracks finished with no cone hit, the map is accurate to 1.4 cm (median), and the MPC runs in 341 microseconds at p99." src="assets/apex-light.svg" width="100%">
  </picture>
</a>

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

<a href="https://github.com/MatiiiBL/tessera">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/tessera-dark.svg">
    <img alt="Tessera: a tensor compiler for Apple silicon that compiles ONNX models through graph fusion, a TensorIR-style loop IR and a learned-cost-model autotuner to C (NEON and SME) or Metal. On the M4 GPU it beats PyTorch and ONNX Runtime on ResNet-50, MobileNetV2, BERT and GPT-2 (GPT-2 1.56 times faster than PyTorch MPS), with outputs within 3e-6 of ONNX Runtime." src="assets/tessera-light.svg" width="100%">
  </picture>
</a>

<a href="https://github.com/MatiiiBL/precis">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/precis-dark.svg">
    <img alt="Précis: LLM agents that read and verify thousands of research papers in parallel. 166 papers/min under simulated API rate limits, no request paid twice after a SIGKILL, 2,896 arXiv papers parsed." src="assets/precis-light.svg" width="100%">
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
    <img alt="WattsGood, 1st place at an 8-hour hackathon: a bilingual web app where Claude and web search match NYC households to energy assistance programs." src="assets/wattsgood-light.svg" width="100%">
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

**Hardware** &nbsp; `SystemVerilog` `RISC-V` `Verilator` `cocotb` `Yosys / nextpnr` `ECP5 FPGA`<br>
**Robotics** &nbsp; `EKF-SLAM` `MPC` `QP solvers` `motion planning` `Eigen`<br>
**Systems** &nbsp; `C++20` `C` `CMake` `NEON / SME SIMD` `POSIX` `Linux`<br>
**Correctness** &nbsp; `ASan` `UBSan` `TSan` `libFuzzer` `Valgrind` `GitHub Actions`<br>
**ML** &nbsp; `PyTorch` `ONNX` `Metal` `NumPy` `pybind11` `MediaPipe` `LLM agents & evals`<br>
**Product** &nbsp; `TypeScript` `React` `Node.js` `C# / ASP.NET Core` `PostgreSQL` `Flutter`

Spanish (native) · English (fluent) · Portuguese (advanced) · Chinese (learning)

<sub>The graphics on this page are drawn by <a href="scripts/render.py">scripts/render.py</a>; the vecdex and Tessera charts plot each project's benchmark results, and the Apex track is one of its evaluation circuits.</sub>
