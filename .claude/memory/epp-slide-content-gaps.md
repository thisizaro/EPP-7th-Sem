---
name: epp-slide-content-gaps
description: Which EPP slides are image-only or have missing equation values, and the reconstructed numbers for the productivity worked examples
metadata:
  type: project
---

Several EPP slides carry their content as **pictures or equation objects**, so text
extraction returns blank slides. When helping with these, the content must be supplied
from standard theory rather than read off the deck:

- **LECTURE 1** slides 5-12 - the "7 essential skills of an engineer" section is all images.
- **LECTURE 4 (Reliability)** slides 2-4, 8-19 are images. Critically, slides 15-19 are titled
  "Reliability Calculation" and contain **the only numerical worked examples** - so all
  reliability formulas (R(t)=e^-λt, series/parallel, MTBF=1/λ, bathtub curve) must be
  reconstructed externally. Deck also duplicates slides 5-7 as 20-23.
- **Lecture 6 (Productivity)** - example slides show the formula but the **numeric answers are
  equation objects that extract as blank**. Reconstructed answers:
  - Ex.1: 10,000 calculators / (50 x 8 x 25 = 10,000 person-hours) = **1 calculator/person-hour**;
    with 60 persons and 12,000 calculators it is still 1 - production rises, productivity does not.
  - Efficiency ex.: 120/180 = **66.67%**.
  - Ex.2 (deflation, base 2020, indices 105/110/115/120/125 for 2021-25):
    materials 121,000/1.10 = 110,000 for 10 plates -> **55,000** for the 5 used;
    labour+energy (2024) 32,000/1.20 = **26,666.67**; output 100,000/1.20 + 100,000/1.25
    = 83,333.33 + 80,000 = **163,333.33**; productivity = 163,333.33/81,666.67 = **2.0**
    (the exact 2.0 confirms both years' sales are counted).
  - Slide 9: Labour prod = 1000/300 = 3.33; Capital prod = 1000/300 = 3.33;
    TFP = (1000-350)/(300+300) = **1.083**; Total prod = 1000/950 = **1.053**.
- **Lecture 9** slide 37 ("Operation Wrath of God") is a stray slide unrelated to quality - ignore it.
- "Lecture 8 Project Mnagement (1).ppt" is a **byte-identical duplicate** of the non-(1) file.

The legacy `.ppt` files need `.claude/tools/extract-slides.py` to read (no libreoffice,
no pip, no sudo on this machine). See [[epp-course-and-exam-structure]].
