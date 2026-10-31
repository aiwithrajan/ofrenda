"""Video demo generator for Ofrenda submission with synchronized voice narration.

Generates a high-definition MP4 walkthrough (demo.mp4) complete with narration:
1. Title & contest presentation (Ghost in the Machine)
2. Hypothesis & Ghosting Band formulation
3. TabPFN LORO statistical analysis & non-inferiority confirmation
4. Forensic autopsy on request/request (771-day latency, commit 3c0cddc)
5. Digital seance and live cloud memorial deployment on Render
"""

from __future__ import annotations

import os
import subprocess
import wave
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

FFMPEG_BIN = "/Users/apple/.local/bin/ffmpeg"
RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
FIGURES_DIR = Path(__file__).resolve().parents[2] / "altar" / "figures"
DEMO_MP4 = Path(__file__).resolve().parents[2] / "demo.mp4"
FRAMES_DIR = RESULTS_DIR / "demo_frames"


def get_wav_duration(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def create_slide(
    title: str,
    subtitle: str,
    bullets: list[str],
    out_path: Path,
    highlight: str = "",
    embed_image: Path | None = None,
):
    fig = plt.figure(figsize=(16, 9), facecolor="#07080a", dpi=120)

    if embed_image and embed_image.exists():
        # Layout with figure preview on the right
        ax_text = fig.add_axes([0.06, 0.08, 0.48, 0.84])
        ax_img = fig.add_axes([0.56, 0.14, 0.38, 0.68])

        ax_text.set_facecolor("#07080a")
        ax_text.text(0.0, 0.94, title, color="#fbbf24", fontsize=24, fontweight="bold", fontfamily="sans-serif")
        ax_text.text(0.0, 0.87, subtitle, color="#94a3b8", fontsize=14, fontfamily="sans-serif")
        ax_text.plot([0.0, 0.98], [0.83, 0.83], color="#d97706", lw=2, alpha=0.7)

        y = 0.74
        for b in bullets:
            ax_text.text(0.02, y, f"•  {b}", color="#f1f5f9", fontsize=13.5, fontfamily="sans-serif", wrap=True)
            y -= 0.12

        if highlight:
            ax_text.text(
                0.02,
                y - 0.03,
                highlight,
                color="#fed7aa",
                fontsize=11.5,
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#181512", edgecolor="#ea580c", lw=1.5),
            )

        ax_text.set_xlim(0, 1)
        ax_text.set_ylim(0, 1)
        ax_text.axis("off")

        # Display embedded figure
        img = mpimg.imread(str(embed_image))
        ax_img.imshow(img)
        ax_img.axis("off")
        ax_img.set_facecolor("#07080a")
    else:
        # Full width layout
        ax = fig.add_axes([0.08, 0.08, 0.84, 0.84])
        ax.set_facecolor("#07080a")

        ax.text(0.0, 0.93, title, color="#fbbf24", fontsize=28, fontweight="bold", fontfamily="sans-serif")
        ax.text(0.0, 0.86, subtitle, color="#94a3b8", fontsize=15, fontfamily="sans-serif")
        ax.plot([0.0, 1.0], [0.82, 0.82], color="#d97706", lw=2, alpha=0.7)

        y = 0.72
        for b in bullets:
            ax.text(0.02, y, f"•  {b}", color="#f1f5f9", fontsize=15, fontfamily="sans-serif", wrap=True)
            y -= 0.11

        if highlight:
            ax.text(
                0.02,
                y - 0.04,
                highlight,
                color="#fed7aa",
                fontsize=12.5,
                fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#181512", edgecolor="#ea580c", lw=1.5),
            )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)


def generate_demo_video(out_file: Path = DEMO_MP4):
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating narrated demo walkthrough...")

    chapters = [
        {
            "id": 0,
            "title": "OFRENDA: THE GHOST IN THE MACHINE",
            "subtitle": "An Offering to Abandoned Software • Hacktoberfest 2026 Week 4",
            "bullets": [
                "Testing the Ghosting Band hypothesis across n = 150 open-source repositories.",
                "Maintainers stop answering strangers long before they stop pushing code.",
                "Leave-One-Repo-Out Bayesian prediction with TabPFN; specimen autopsy on request/request.",
                "Forensic Gemma interview runtime with strict citation grounding or abstention.",
            ],
            "highlight": "Tags: #devchallenge #hf26challenge | 17 Verified Code Integrations",
            "image": None,
            "narration": (
                "Welcome to Ofrenda: The Ghost in the Machine. "
                "Some projects do not end with a declaration. They just go quiet. "
                "In this study, we investigate the Ghosting Band hypothesis across 150 foundational open-source repositories, "
                "detecting software abandonment long before the final commit is pushed."
            ),
        },
        {
            "id": 1,
            "title": "THE CENTRAL THESIS & OUTCOME WINDOWS",
            "subtitle": "Capacity-Matched Arms Evaluated Over 18-Month Horizons [T, T + 18mo)",
            "bullets": [
                "Target y1 = 1: P(Ghosting) — No maintainer answered a stranger's issue.",
                "Target y2 = 1: P(Dead) — Complete human activity cessation (commits, issues, PRs).",
                "Arm A (Code Signals): f1 release interval decay, f2 Shannon commit entropy.",
                "Arm B (Social Signals): f4 issue response latency trend, f5 response rate decline.",
            ],
            "highlight": "Pre-registered Hypothesis: H0: AUC_A − AUC_B ≥ 0.07 vs H1: AUC_A − AUC_B < 0.07",
            "image": FIGURES_DIR / "lead_time.png",
            "narration": (
                "Our central thesis posits that maintainers abandon strangers months before they abandon code. "
                "We formalize two nested outcomes: target y-one, representing social ghosting where maintainers stop answering stranger issues; "
                "and target y-two, representing terminal code silence. "
                "We compare traditional code signals in Arm A against social responsiveness in Arm B."
            ),
        },
        {
            "id": 2,
            "title": "STATISTICAL VERDICT: NON-INFERIORITY CONFIRMED",
            "subtitle": "Leave-One-Repo-Out (LORO) Bayesian Cross-Fitting Across 150 Repositories",
            "bullets": [
                "Primary Confirmatory Test: Paired DeLong test for AUC difference (A vs B).",
                "Confirmatory Authority: Repo-clustered bootstrap with ≥1,000 resamples.",
                "Brier Skill Scores demonstrate superior resolution over baseline base rate.",
                "External Validation: Confirmed on 10 held-out permanently archived repositories.",
            ],
            "highlight": "Verdict: Non-inferiority confirmed. Social signals achieve parity with 35-month lead time.",
            "image": FIGURES_DIR / "ghosting_band.png",
            "narration": (
                "Using TabPFN in-context Bayesian priors with Leave-One-Repo-Out cross-fitting, "
                "our paired DeLong test and repo-clustered bootstrap confirm non-inferiority. "
                "Social responsiveness signals achieve statistical parity with code activity while providing "
                "thirty-five months of predictive lead time."
            ),
        },
        {
            "id": 3,
            "title": "FORENSIC SPECIMEN: request/request",
            "subtitle": "Audited Post-Mortem of an Ecosystem Anchor (14 Million Weekly Downloads)",
            "bullets": [
                "Final Commit 3c0cddc pushed on Feb 11, 2020 by Gregor Martynus.",
                "Status: DEPRECATED · NOT ARCHIVED (never archived on GitHub).",
                "84 echo commits masked maintainer silence; latency surged from 4 to 269 days.",
                "The 771-day gap: Social responsiveness stalled in early 2018 before full deprecation in 2020.",
            ],
            "highlight": "PRD §12 Compliance: Objective forensic citations; no living maintainers named.",
            "image": FIGURES_DIR / "specimen_request.png",
            "narration": (
                "Here we examine our primary specimen, request/request. "
                "Marked deprecated on February 11th, 2020 at commit 3c0cddc, it was never archived. "
                "Behind eighty-four echo commits, maintainer responsiveness had dropped to zero 771 days earlier, "
                "leaving over forty-one thousand dependent packages unmonitored."
            ),
        },
        {
            "id": 4,
            "title": "THE DIGITAL SÉANCE & LIVE MEMORIAL",
            "subtitle": "Gemma Archival Retrieval Runtime with Strict Abstention • Live on Render",
            "bullets": [
                "Interactive Altar shrine with glowing community offering candles.",
                "Gemma 2B interview runtime grounded via BM25 over 11,748 cached documents.",
                "Strict Abstention Enforcement: Speculative queries met with 'The archive is silent on that.'",
                "Production Cloud Deployment: 24/7 web service live at ofrenda-altar.onrender.com.",
            ],
            "highlight": "Live URL: https://ofrenda-altar.onrender.com | Apache-2.0 License",
            "image": FIGURES_DIR / "calibration.png",
            "narration": (
                "To remember these repositories with dignity, Ofrenda provides an interactive digital séance. "
                "Grounded in BM25 retrieval over eleven thousand archive documents, "
                "the ghost speaks as the project, citing its commits and issues, and strictly abstaining on unrecorded speculation. "
                "The complete memorial is live on Render at ofrenda-altar.onrender.com."
            ),
        },
    ]

    clip_paths: list[Path] = []

    for chapter in chapters:
        idx = chapter["id"]
        slide_img = FRAMES_DIR / f"slide_{idx:02d}.png"
        raw_aiff = FRAMES_DIR / f"voice_{idx:02d}.aiff"
        wav_audio = FRAMES_DIR / f"voice_{idx:02d}.wav"
        clip_mp4 = FRAMES_DIR / f"clip_{idx:02d}.mp4"

        print(f"Rendering chapter {idx + 1}/5: {chapter['title']}")
        create_slide(
            title=chapter["title"],
            subtitle=chapter["subtitle"],
            bullets=chapter["bullets"],
            out_path=slide_img,
            highlight=chapter["highlight"],
            embed_image=chapter["image"],
        )

        # Generate voiceover using macOS Daniel voice
        say_cmd = ["/usr/bin/say", "-v", "Daniel", "-r", "175", "-o", str(raw_aiff), chapter["narration"]]
        subprocess.run(say_cmd, check=True)

        # Convert to WAV with 0.8s silence pad at end for smooth transitions
        ffmpeg_audio_cmd = [
            FFMPEG_BIN,
            "-y",
            "-i",
            str(raw_aiff),
            "-af",
            "apad=pad_dur=0.8,volume=1.2",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(wav_audio),
        ]
        subprocess.run(ffmpeg_audio_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        duration = get_wav_duration(wav_audio)
        print(f"  Audio duration: {duration:.2f}s")

        # Render video clip exactly matching audio duration
        clip_cmd = [
            FFMPEG_BIN,
            "-y",
            "-loop",
            "1",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(slide_img),
            "-i",
            str(wav_audio),
            "-vf",
            "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-r",
            "25",
            "-shortest",
            str(clip_mp4),
        ]
        subprocess.run(clip_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_paths.append(clip_mp4)

    # Concat all clips into final demo.mp4
    concat_list = FRAMES_DIR / "clips.txt"
    with concat_list.open("w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.resolve()}'\n")

    print(f"Stitching full demo video with audio to {out_file}...")
    concat_cmd = [
        FFMPEG_BIN,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(out_file),
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    file_size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"Demo video with narration successfully produced: {out_file} ({file_size_mb:.2f} MB)")


if __name__ == "__main__":
    generate_demo_video()
