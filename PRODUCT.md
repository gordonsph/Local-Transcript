# Product

## Register

product

## Users

The primary user is the Mac owner running long Cantonese and mixed Cantonese-English audio transcriptions locally. They are usually in a focused work context, uploading recordings, checking whether the Mac is busy, and returning later to collect transcript files.

Future agents may also maintain this workflow. They need clear, predictable controls and enough status detail to understand what the system is doing without reading logs first.

## Product Purpose

Local Transcript turns audio or video files into timestamped transcript outputs through a local `whisper.cpp` `large-v3` workflow. Success means the user can open a stable local bookmark, upload audio, choose language and output format, choose where results are saved, and monitor or control the job without needing terminal knowledge.

The product optimizes for local privacy, maximum practical transcription accuracy, and operational clarity over speed or visual novelty.

## Brand Personality

Quiet, precise, trustworthy.

The interface should feel like a well-made local utility: calm enough for long-running jobs, specific enough to explain system state, and restrained enough that the work stays centered on the transcript.

## Anti-references

Do not make this look like a marketing landing page, a chatbot product demo, a neon AI dashboard, or a decorative SaaS hero. Avoid purple gradients, glassmorphism, oversized metric theatrics, nested cards, ornamental illustrations, and copy that explains obvious UI mechanics.

Do not hide important operational state. A long transcription job should never feel like a black box.

## Design Principles

1. Show the workflow first. The upload and job controls are the product.
2. Make long-running work legible. Progress, remaining time, elapsed time, save location, and system pressure should be visible when they matter.
3. Keep choices few and meaningful. Language, output format, result folder, and terminology hints are enough for day 1; quality settings stay fixed.
4. Prefer familiar product UI over invention. Standard selects, inputs, buttons, progress bars, and logs are appropriate here.
5. Preserve trust through restraint. Visual polish should improve scanning, hierarchy, and confidence, not decorate the surface.

## Accessibility & Inclusion

Target WCAG AA contrast for text and controls. Preserve keyboard focus indicators, use semantic form controls, keep touch targets at least 44px on mobile, support reduced-motion preferences, and ensure long file paths or filenames wrap without breaking layout.
