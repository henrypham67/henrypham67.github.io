---
name: ielts-daily-task
description: Automates the creation of a daily IELTS study task file based on the Strategic Roadmap. It determines today's skill focus (e.g., Speaking on Thursdays), creates the corresponding markdown file in the correct subfolder (e.g., speaking/23-04-2026.md), and populates it with a tailored to-do list. Use when the user wants to generate today's IELTS study task.
---

# IELTS Daily Task Skill

This skill automates the creation of daily IELTS study tasks based on the "IELTS General Training Mastery: A 6-Month Strategic Roadmap".

## Workflow

1.  **Identify Today's Skill Focus**:
    *   Monday: Listening
    *   Tuesday: Reading
    *   Wednesday: Writing
    *   Thursday: Speaking
    *   Friday: Vocabulary
    *   Saturday: Simulation (Mock Test)
    *   Sunday: Review (Error Log)

2.  **Generate Task File**:
    *   File naming: `dd-MM-yyyy.md`
    *   Target folder: `content/posts/english/ielts/[skill_folder]/`
    *   Content: A to-do list specific to today's focus area and the strategic goals defined in the roadmap.

## Usage

When the user asks to "generate today's task" or "create a task for today", run the following script:

```bash
node scripts/generate_task.cjs <absolute_path_to_ielts_content_dir>
```

Example:
```bash
node scripts/generate_task.cjs /Users/henrypham/workspaces/henry/henrypham67.github.io/content/posts/english/ielts/
```

## Strategy Focus Areas

### Monday (Listening)
- **Target**: 8.0 (GT)
- **Task**: Practice with Section 4 monologues; review transcripts for distractors.
- **Rule**: Can afford at most 5 wrong answers.

### Tuesday (Reading)
- **Target**: 7.0 (GT)
- **Task**: Timed GT Reading passages (focus on Sections 1 & 2 for 100% accuracy).
- **Rule**: Accuracy matters more than speed.

### Wednesday (Writing)
- **Target**: 7.0 (GT)
- **Task**: Rotate between Task 1 (Letters) and Task 2 (Essay) structure planning.
- **Rule**: Formal vs. Informal tone consistency.

### Thursday (Speaking)
- **Target**: 7.0 (GT)
- **Task**: Record yourself answering Part 2 cue cards and Part 3 abstract questions.
- **Rule**: Extend answers using the "magic number 3" (give 3 examples).

### Friday (Vocabulary)
- **Task**: Topic-specific words (work, travel, environment) and collocations.
- **Rule**: Teach collocations (word groups of 3), not isolated vocabulary.

### Saturday (Simulation)
- **Task**: Intensive (2 hours): Full-length timed mock test under exam conditions.

### Sunday (Review)
- **Task**: Error Log analysis: Why did you get those specific answers wrong?
- **Rule**: Categorize mistakes as "Vocabulary", "Timing", or "Misinterpretation".
