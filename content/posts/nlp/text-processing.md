---
title: 'Text Processing'
date: 2026-03-21T06:57:27+07:00
draft: true
quiz:
  title: "Text Processing Quiz"
  questions:
    - q: "Sentence segmentation is a form of what?"
      options:
        - "Lemmatisation"
        - "Parsing"
        - "Tokenization"
        - "Stemming"
      correct: 2
    - q: "How should an email address such as fred@gmail.com be tokenized?"
      options:
        - "It depends on the purpose of your text processing application"
        - "As 3 tokens"
        - "As one token"
        - "As 2 tokens"
      correct: 0
    - q: "Stemming and lemmatisation are both forms of what?"
      options:
        - "Sentence segmentation"
        - "Text normalisation"
        - "Text tokenization"
        - "Syntactic parsing"
      correct: 1
    - q: "Which statement best describes how lemmatisation differs from stemming?"
      options:
        - "Lemmatisation is a more crude, heuristic process"
        - "Lemmatisation is informed by the linguistic context"
        - "Stemming requires access to a lexical database"
        - "Stemming only works for irregular verbs"
      correct: 1
    - q: "Which statement about stemming is accurate?"
      options:
        - "Stemming is a linguistically principled process"
        - "Stemming requires access to a lexical database"
        - "Stemming only works for regular verbs"
        - "Stemming is a more crude, heuristic process"
      correct: 3
    - q: "How many stop words are there in English?"
      options:
        - "More than 87"
        - "There is no universal list of stop words in English"
        - "Less than 87"
        - "Exactly 87"
      correct: 1
    - q: "Which regular expression matches both 'Set' and 'set'?"
      options:
        - '[Ss]et'
        - 'Set|set'
        - 'S|set'
        - '[S-s]et'
      correct: 0
    - q: "Which regular expression matches any characters that are not digits?"
      options:
        - '[^0-9]'
        - '^[0-9]'
        - '[0-9]'
        - '[0^9]'
      correct: 0
    - q: "Which regular expression matches both 'colour' and 'color'?"
      options:
        - 'colo.*r'
        - 'colo.r'
        - 'colo?ur'
        - 'colou?r'
      correct: 3
    - q: "Which regular expression matches both the string '123' and '321'?"
      options:
        - '\D'
        - '\d+'
        - '\d'
        - '\D*'
      correct: 1
    - q: "Which regular expression matches any non-word characters at the end of a string?"
      options:
        - '\w$'
        - '\W$'
        - '\W'
        - '\d$'
      correct: 1
    - q: "Which of the following is NOT a common way to structure a text corpus?"
      options:
        - "Isolated"
        - "Categorised"
        - "Overlapping"
        - "Conditional"
      correct: 3
    - q: "The study of systematic differences between language genres is known as:"
      options:
        - "Informatics"
        - "Stylistics"
        - "Text analytics"
        - "Mystics"
      correct: 1
    - q: "A collection of text samples used as research data is known as what?"
      options:
        - "Belles lettres"
        - "Habeas corpus"
        - "A text corpus"
        - "A text collocation"
      correct: 2
flashcards:
  - q: "What is the role of stemming in NLP?"
    a: "To group different inflected or derived forms of a word so they are treated as the same token, reducing vocabulary size and index size."
  - q: "Name two advantages of stemming."
    a: "Reduces vocabulary size (fewer unique tokens) and reduces index size, improving search efficiency."
  - q: "Name two disadvantages of stemming."
    a: "Can produce non-real words (e.g., 'argue' → 'argu'), and unrelated words may collapse to the same stem."
  - q: "How does lemmatization differ from stemming?"
    a: "Lemmatization is a linguistically principled process informed by syntactic context and requires a lexical database (e.g., WordNet). Stemming is a crude, heuristic suffix-chopping process."
  - q: "What are stop words and why are they removed in NLP pipelines?"
    a: "High-frequency function words (e.g., 'the', 'and', 'is') that carry little meaning. Removed to reduce data dimensionality and focus models on content-bearing terms."
  - q: "What is the difference between inflectional and derivational morphology?"
    a: "Inflectional morphemes change word form but not grammatical category (e.g., run→runs, both verbs). Derivational morphemes often change POS (e.g., 'democratic' adjective → 'democracy' noun)."
  - q: "Why are regular expressions described as 'greedy'?"
    a: "By default, quantifiers (*, +) match as much text as possible. Use *? or +? for non-greedy (lazy) matching that stops at the first valid match."
  - q: "Are these two regex patterns equivalent: ^[a-zA-Z][a-zA-Z][a-zA-Z]$ and ^[a-zA-Z]{3}$?"
    a: "Yes, they are functionally identical — both match exactly 3 alphabetic characters. Example: 'Abc' matches both; 'Ab1' matches neither."
  - q: "What is compounding in morphology? Give an example using the root 'rain'."
    a: "Combining two or more words to form a new word: e.g., 'raincoat', 'rainbow', 'rainforest'."
  - q: "What is derivation in morphology? Give an example using the root 'rain'."
    a: "Adding affixes to create a new word, often changing the POS: e.g., 'rainy' (noun→adjective), 'rainfall'."
  - q: "What is inflection in morphology? Give an example using the root 'rain'."
    a: "Changing a word's form within the same grammatical category: e.g., 'rains', 'raining', 'rained' (all verbs)."
  - q: "In what order should these NLP preprocessing steps typically be applied: stemming, POS tagging, word tokenisation, sentence tokenisation, lemmatising, stop word removal?"
    a: "Sentence tokenisation → word tokenisation → POS tagging → lemmatising → stop word removal → stemming. POS tagging before lemmatisation ensures context-sensitive root resolution."
  - q: "What challenge does the sentence 'Prof. Russell-Rose uses TF.IDF when parsing data from Which? reports' pose for sentence tokenisation?"
    a: "Periods in 'Prof.' and 'TF.IDF' are not sentence boundaries; '?' in 'Which?' is a brand name, not a question. These abbreviations and embedded punctuation cause false sentence splits."
  - q: "What regex matches any non-word characters at the end of a string?"
    a: "\\W$ — \\W matches non-word characters, $ anchors to the end of the string."

---

Here is everything you need to know from the **Topic 2: Basic Text Processing** course page, organized by section, followed by past exam questions grouped by topic.

---

## Topic Overview

The topic is split into two parts and covers three learning objectives:
1. **Understand text processing fundamentals**
2. **Apply text processing techniques**
3. **Manipulate unstructured data**

The tool used throughout is **NLTK (Natural Language Toolkit)**, an open-source Python library for NLP.

---

## 2.1 — Introduction to Text Processing

### Why Does Unstructured Data Matter?

The vast majority of the world's data is **unstructured**, meaning it's not organized in tables or spreadsheets. Key sources include documents and paper, emails, social media, customer feedback, open-ended survey responses, web pages, and audio/video (which is first transcribed into text). Because most of this data exists as free-form text, processing it is a foundational NLP challenge.

### Why Is Text Hard to Process?

Even though humans communicate effortlessly every day, text presents many computational challenges:

- **Polysemy** — one word maps to many concepts (e.g., "bat" = animal or sports equipment)
- **Synonymy** — one concept maps to many words (e.g., "smart", "bright", "clever" all mean intelligence)
- **Word order** — "man bites dog" vs "dog bites man" have the same words but very different meanings. In English, word order defines subject/verb/object. Some inflectional languages use word endings instead.
- **Language is generative** — the same idea can be expressed in countless ways
- **Techniques used to describe an idea/words** — paraphrase, metaphor, idiom, sarcasm, and irony
- **Language change** — meanings evolve (e.g., "I want to buy a mobile" meant something entirely different 30 years ago); also culturally variable ("mobile" in the UK = "cellphone" in the US)
- **Noise and typos** — real-world text is full of errors and disfluencies
- **Negation and coordination** — searching for "neuro linguistic programming" returns a document that explicitly says it's *not* about that topic
- **Multilinguality** — a single sentence may span multiple languages
- **Sarcasm/irony/jargon** — the intended meaning can be the opposite of the literal words

---

## 2.1 — Text Processing Fundamentals (Part 1)

### Levels of Ambiguity

Ambiguity occurs at multiple linguistic levels, from word-level up to sentence-level and beyond:

**Lexical level (words/tokens)**
The most basic challenge: separating tokens from each other. In English, whitespace helps, but it's not always sufficient. "I can't stand the rain" — should "can't" be 1 or 2 tokens? This depends on your **tokenization policy**.

**Function Words & Stop Words**
Many words (e.g., "and", "of", "the", "with") act as grammatical "glue" rather than carrying meaning. These are **function words** or **stop words**. In indexing and search engines, removing them reduces index size and improves efficiency — but there is no definitive, universal stop word list. The famous failure case: searching for Shakespeare's "to be or not to be" returned zero results because all the words were stop words.

**Stemming**
A crude technique that **chops the endings off words** to reduce them to a common root:
- "fishing", "fished", "fisher" → "fish"
- Problem: "argue" → might produce "argu" (not a real word)
- Benefit: efficiency and index size reduction
- Drawback: stems may not be valid words

**Lemmatization**
A more linguistically principled approach to the same problem — resolves words to their **linguistic root (lemma)**:
- "were" → "be" (past tense)
- "passing" → "pass"
- It is sensitive to **syntactic category** (noun, verb, adjective, etc.)
- Example: "meeting" lemmatized as a noun stays "meeting"; as a verb it becomes "meet"
- More accurate than stemming but requires access to a lexical database (e.g., WordNet)

**Morphology**
The study of the shape/structure of words. In English, morphology is relatively simple. In German, compound nouns like *Gebäudereinigungsunternehmensmitarbeiter* (building-cleaning-company-employee) must be decomposed to be understood — a major NLP challenge for many languages.

---

## 2.1 — Text Processing Fundamentals (Part 2)

### Higher-Level Ambiguity

**Syntax (Part-of-Speech)**
Words play syntactic roles: nouns, pronouns, adjectives, determiners, verbs, adverbs, prepositions, conjunctions, interjections. The word "book" can be a noun ("I read the book") or a verb ("I booked a flight"). This is called **Part-of-Speech (POS) tagging**.

Classic example: "Time flies like an arrow" vs "Fruit flies like a banana" — syntactically similar on the surface, but require completely different parsing. "Fruit flies" = insects (noun), "like" = a verb.

**Syntactic Parsing**
Parsing creates a **tree structure** (parse tree) showing how parts of a sentence combine to form meaning. This uses rules of **grammar**. Problem example: "I saw the man on the hill with a telescope" — you cannot determine syntactically who is holding the telescope. This is called **prepositional phrase attachment** ambiguity, and requires **contextual information** to resolve.

**Sentence Boundary Detection**
Identifying where one sentence ends and another begins. Simple rules (e.g., look for a period or exclamation mark) fail due to exceptions. This is one reason **statistical techniques** are often more robust than purely rule-based ones.

---

## 2.2 — Practical Text Processing Techniques

### Sentence Segmentation (using NLTK)

Sentence segmentation is a form of **tokenization** — finding where sentences begin and end. NLTK provides a pre-trained **sentence tokenizer** (`sent_tokenize`). It handles challenges like:
- Punctuation not at the end of sentences
- Sentences spanning multiple lines
- Sentences beginning with lowercase letters

Example: given a multi-sentence passage, `sent_tokenize` returns a list of sentence strings. It correctly identifies exclamation marks and periods as sentence boundaries and treats a run-on multi-line block as one sentence when appropriate.

---

### Word Tokenization (using NLTK)

Word tokenization divides a string into its individual words/tokens. Whitespace works most of the time in English, but exceptions arise:

- **Email addresses**: `fred@gmail.com` — split on `@` gives 2 tokens, or kept as one; the right choice **depends on your application's purpose**
- **Dates**: often kept together (`23/01/2021`)
- **Apostrophes**: possessive `students'` → split separately; contractions like `aren't` → `are` + `n't`
- **Hyphenated words**: usually kept together
- **URLs**: typically split on the colon character
- **Company names and proper nouns**: kept together

NLTK's `word_tokenize` function handles these edge cases reasonably well out of the box for English.

---

### Text Normalisation (using NLTK)

Normalisation reduces linguistic variation to manageable forms. Two main techniques:

**Inflectional vs. Derivational Morphology:**
- *Inflectional*: different forms within the same grammatical category (run, runs, running → all verbs)
- *Derivational*: forms across different categories ("democratic" = adjective; "democracy" = noun)

**Stemming (Porter Stemmer):**
- Crude, heuristic process — chops suffixes
- "meeting" → "meet" (stem), but can produce non-words
- "dogs" → "dog" ✓, but irregular forms may not stem correctly

**Lemmatization (WordNet Lemmatizer):**
- Linguistically principled — uses a lexical database (WordNet)
- Context-sensitive: the same word is resolved differently depending on whether it's treated as a noun or verb
- "dogs" → "dog", "churches" → "church", "abaci" → "abacus"
- "meeting" (as noun) → "meeting"; (as verb) → "meet"

Both are forms of **text normalisation**. The key difference: stemming is a crude, heuristic process; lemmatisation is informed by linguistic context and requires a lexical database.

---

## 2.3 — Regular Expressions

Regular expressions (regex) are a **formal language for defining patterns** in character sequences. They allow matching, extracting, replacing, and cleaning text. Python's `re` library is used. Five core concepts are covered:

### 1. Disjunction `[ ]` and `|`
- `[Tt]he` — matches "the" or "The" (uppercase or lowercase)
- `[0-9]` — matches any digit
- `[A-Z]` — matches any uppercase letter
- `off|the|away` (pipe) — matches any of those words

### 2. Negation `[^ ]`
The **caret `^` inside square brackets** negates the range:
- `[^0-9]` — matches anything that is *not* a digit
- Combined with substituting for empty string → extracts only digits from text

### 3. Optionality `.` `?` `*` `+`
- `.` (dot) — matches **any single character** (wildcard); e.g., `beg.n` matches "begin", "began", "begun"
- `?` — the **previous character is optional**; e.g., `colou?r` matches "colour" and "color"
- `*` (Kleene star) — **0 or more** of the previous character; matches are **greedy by default** (consume as much as possible); use `*?` for **non-greedy** matching
- `+` (Kleene plus) — **1 or more** of the previous character; e.g., `fooo+` matches "fooo", "foooo", but not "foo"

### 4. Aliases (shortcuts)
- `\w` — match any **word character** (letter/digit/underscore)
- `\W` — match any **non-word character**
- `\d` — match any **digit**
- `\D` — match any **non-digit**
- `\s` — match any **whitespace**
- `\S` — match any **non-whitespace**

### 5. Anchors `^` and `$`
- `^` at the **start of a pattern** (outside brackets) — anchors to the **start of a string**
- `$` at the end of a pattern — anchors to the **end of a string**
- `re.MULTILINE` flag — treats each line as a separate string, so `^` and `$` apply per line

The main `re` method used is `re.sub(pattern, replacement, text)` — substitutes all matches of the pattern with the replacement string.

**Practical regex lab tasks include:** matching URLs, email addresses (rejecting malformed ones like `bob @ aol.com`), and dates in various formats.

---

### Stop Words

Stop words are **high-frequency function words** (e.g., "and", "the", "of", "in") that appear across all document types and add little meaning-differentiating content. They tend to add noise in machine learning tasks like document classification.

Key points:

- NLTK provides a built-in stop word list for many languages (English, German, French, etc.)
- **There is no universal list** — the appropriate stop word list depends entirely on your application
- Classic failure: Shakespeare's "to be or not to be" would return an empty list after stop word removal because every word is a stop word
- Stop word lists are language-specific
- **Use with caution** — being too aggressive can remove important terms

Implementation: tokenize text with `word_tokenize`, cast the stop word list to a `set` (faster lookup), then filter with a list comprehension keeping only words not in the stop word set.

---

## 2.4 — Text Corpora

A **corpus** (plural: *corpora*) is a large, structured collection of text used for linguistic analysis.

### Four Types of Text Corpus (all accessible via NLTK)

**1. Isolated Corpus — Gutenberg Corpus**
A collection of freely available electronic books (Jane Austen, Shakespeare, Melville, etc.). You can extract words, sentences, and raw text. Good for literary analysis.

**2. Categorized Corpus — Brown Corpus**
One of the first formally gathered, categorized corpora. Contains text from hundreds of sources organized by **genre** (news, science fiction, romance, mystery, reviews, etc.). Enables **stylistic analysis** — e.g., looking at how **modal verb** usage (can, could, may, might, must, will) differs across genres. Finding: "will" is most common in news (language of the future), "can" in hobbies (language of possibility), "could" in romance.

The study of systematic differences between language genres is called **Stylistics**.

**3. Overlapping Corpus — Reuters Corpus**
Contains 10,788 news documents **tagged with topics/industries**. Unlike Brown, a single document can belong to **multiple categories** simultaneously (overlapping tags). Useful for multi-label classification tasks.

**4. Temporal Corpus — Inaugural Address Corpus**
Contains 55 presidential inauguration speeches from 1789 (George Washington) to 2017 (Donald Trump). Enables **temporal analysis** — e.g., tracking the frequency of words like "America" and "citizen" over time reveals interesting historical patterns (e.g., "America" spikes dramatically in recent decades).

---

## 2.5 — Summary

The topic recaps the full pipeline:

1. **Lexical analysis / Tokenization** — separating text into tokens (whitespace helps but isn't sufficient)
2. **Stemming** — crude suffix-chopping to find common roots
3. **Lemmatization** — linguistically principled root-finding, context-sensitive
4. **Morphology** — word shape analysis (important in compounding languages like German)
5. **Syntax & POS Tagging** — assigning grammatical roles to words in sentences
6. **Syntactic Parsing** — building parse trees; some ambiguities (e.g., prepositional phrase attachment) cannot be resolved by syntax alone
7. **Sentence Boundary Detection** — needs more than just punctuation rules; statistical approaches are more robust
8. **Regular Expressions** — flexible, efficient tool for pattern matching and text transformation
9. **Stop Word Removal** — filter high-frequency low-information words; no universal list; use cautiously
10. **Text Corpora** — large text collections enabling stylistic, temporal, and categorical analyses (isolated, categorized, overlapping, temporal)

---

## Key Textbooks Referenced

- Provost & Fawcett, *Data Science for Business* (pp. 251–277) — representing text
- Schütze, Manning & Raghavan, *Introduction to Information Retrieval* (Ch. 2, pp. 21–22) — tokenization
- Jurafsky & Martin, *Speech and Language Processing* (3rd ed., Ch. 2) — regular expressions
- Bird, Klein & Loper, *NLP with Python* (Sec. 2.1, pp. 39–51) — accessing text corpora
