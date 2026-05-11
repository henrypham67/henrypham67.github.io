const fs = require('fs');
const path = require('path');

function getFormattedDate() {
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0'); // January is 0!
    const yyyy = today.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
}

function getDayOfWeek() {
    const today = new Date();
    // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
    return today.getDay();
}

const ROADMAP = {
    1: { skill: 'Listening', folder: 'listening', task: 'Practice with Section 4 monologues; review transcripts for distractors.' },
    2: { skill: 'Reading', folder: 'reading', task: 'Timed GT Reading passages (focus on Sections 1 & 2 for 100% accuracy).' },
    3: { skill: 'Writing', folder: 'writing', task: 'Rotate between Task 1 (Letters) and Task 2 (Essay) structure planning.' },
    4: { skill: 'Speaking', folder: 'speaking', task: 'Record yourself answering Part 2 cue cards and Part 3 abstract questions.' },
    5: { skill: 'Vocabulary', folder: 'vocabulary', task: 'Topic-specific words (work, travel, environment) and collocations.' },
    6: { skill: 'Simulation', folder: 'simulation', task: 'Intensive (2 hours): Full-length timed mock test under exam conditions.' },
    0: { skill: 'Review', folder: 'review', task: 'Error Log analysis: Why did you get those specific answers wrong?' }
};

function main() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error('Usage: node generate_task.cjs <base_dir>');
        process.exit(1);
    }

    const baseDir = args[0];
    const day = getDayOfWeek();
    const roadmapItem = ROADMAP[day];
    const dateStr = getFormattedDate();
    const fileName = `${dateStr}.md`;
    const targetDir = path.join(baseDir, roadmapItem.folder);
    const filePath = path.join(targetDir, fileName);

    if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
    }

    const content = `---
title: "IELTS Study Task - ${roadmapItem.skill}"
date: ${new Date().toISOString()}
draft: true
tags: ["ielts", "${roadmapItem.skill.toLowerCase()}"]
categories: ["english", "ielts"]
---

# Daily Task: ${roadmapItem.skill} (${dateStr})

## To-Do List
- [ ] ${roadmapItem.task}
- [ ] Update Error Log (Categorize as Vocabulary, Timing, or Misinterpretation)
- [ ] Review "Critical GT Success Strategies" in Roadmap

## Strategy Focus
- **${roadmapItem.skill} Target**: 7.0+ (GT)
- **Today's Focus**: ${roadmapItem.task}

## Notes
*(Write your practice notes, feedback, or reflections here)*
`;

    fs.writeFileSync(filePath, content);
    console.log(`✅ Task file created: ${filePath}`);
}

main();
