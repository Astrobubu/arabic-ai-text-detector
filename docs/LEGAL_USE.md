# Using This Tool In a Legal Context

This tool produces a **risk estimate**, not forensic proof of authorship. Read this before
handing a report to a lawyer or using it to inform any decision with real consequences for a
person.

## What the report actually claims

Every report combines two independent, automated signals:

1. **Layer 1 - rule-based heuristics** (`report.heuristic`): sentence-length variation,
   formulaic AI phrase matching, discourse-transition density, lexical diversity, structural
   shape (lists/headings), and text compressibility. Fully explainable - every number traces
   back to a concrete, inspectable pattern in the text. Works offline with no extra
   dependencies, for both Arabic and English.
2. **Layer 2 - a local ML classifier** (`report.ml`): a small pretrained model
   (AraBERT-based for Arabic, RoBERTa-based for English, trained on the public HC3 dataset)
   that estimates the probability the text was AI-generated. This runs fully offline once its
   weights are cached (see "Offline guarantee" below), but it is an opaque model - it does not
   explain *why* it reached a conclusion the way Layer 1 does.

The report never blends these into one hidden number. It shows both, plus an `agreement`
field describing whether they point the same way (`both_layers_flag_ai_like`,
`both_layers_flag_human_like`) or conflict (`layers_disagree`, `uncertain_or_mixed`). **Disagreement
between the layers is itself useful information** - it means the sample is genuinely ambiguous
and should not be leaned on either way without human review.

## Why this is not forensic proof

- Both layers are trained/tuned on general text and can be wrong on domain-specific writing,
  translated text, heavily edited text, or text written by a non-native speaker.
- Paraphrasing tools, light AI-assisted editing, or simply a formal writing style can inflate
  either layer's score without the text being AI-generated.
- Neither layer has been validated against a forensic linguistics standard or peer-reviewed
  for admissibility. Courts in most jurisdictions do not currently recognize automated
  AI-detection scores as expert testimony on their own.
- The ML layer's accuracy figures (as reported by the model authors) come from their own
  benchmark datasets, which may not resemble the specific documents you're analyzing.

## How to use it responsibly

1. Treat every report as a **starting point for review**, not a conclusion.
2. When the two layers agree, that's a stronger (but still not certain) signal than either
   alone.
3. When the two layers disagree, do not pick whichever one supports the conclusion you want -
   treat the sample as unresolved and prioritize other evidence.
4. For anything with real consequences for a named person, compare against **known writing
   samples** from that person (their emails, prior filings, messages) rather than relying on
   the score in isolation.
5. Keep the report's `input_sha256` alongside the original document. It lets you later prove a
   specific report corresponds to a specific piece of text, without needing to duplicate
   storage of the (potentially confidential) content itself.
6. Every report's `caveats` field restates these limits in plain language - don't strip it out
   when forwarding the report.

## Offline guarantee

- Layer 1 never makes a network call, ever.
- Layer 2 downloads its model weights from Hugging Face **once**, the first time it runs (or
  ahead of time via `scripts/prefetch_models.py` before packaging the desktop app). After that
  first download, all inference happens entirely on the local machine - **the text you analyze
  is never sent anywhere.**
- The desktop installer is built to bundle the model weights ahead of time (see
  `scripts/prefetch_models.py` + `scripts/build_backend.py`), so a fresh install needs no
  internet access at all, which matters for confidential client material.

## Report fields reference

See [references/api-reference.md](../references/api-reference.md) for the full JSON contract.
