1. Write the blog post first (deep processing)

When you learn something (e.g., systemd, Kubernetes networking), write it
up as a blog post. This forces you to:
- Organize the concept clearly
- Fill knowledge gaps (you'll notice what you don't understand)
- Create your own examples

2. Extract Anki cards from your post

After publishing, create Anki cards from the key points. Rules of thumb:

- One fact per card — don't cram a whole section into one card
- Use cloze deletions for definitions and commands
- Ask "why" and "how" questions, not just "what"

Example from a systemd post:
Card Type: Basic
Front: What command reloads all unit files after editing?
Back: systemctl daemon-reload
────────────────────────────────────────
Card Type: Cloze
Front: The directive {{c1::Restart=on-failure}} tells systemd to restart
the
    service only when it exits with a non-zero code
Back: —
────────────────────────────────────────
Card Type: Why
Front: Why use WantedBy=multi-user.target instead of graphical.target?
Back: For servers/headless systems that don't run a GUI
3. Link them together

In your Anki cards, add a "Source" field with the link back to your blog
post (e.g., https://henrypham67.github.io/posts/linux/systemd/). When a
card is hard to recall, you can revisit the full context.

4. Use the Feynman technique as a bridge

Learn → Blog about it (explain simply) → Extract Anki cards → Review →
  ↑                                                                  |
  └──── If card is hard, re-read/rewrite the blog section ←─────────┘

Practical tips

- Tag Anki cards by blog post category (k8s, linux, databases) — mirrors
your Hugo content structure
- Keep cards atomic — 20 small cards beat 5 overloaded ones
- Add cards incrementally — don't try to card-ify an entire post at once;
add 5-10 cards per post
- Review cards daily (even 10 min), write blog posts weekly
- Use images in Anki — screenshot your own diagrams from blog posts (you
already have .wsd files)

Tools to streamline this

- Obsidian + Anki plugin — if you draft in Obsidian before Hugo, you can
auto-generate cards from markdown
- AnkiConnect API — you could script card creation from your Hugo
frontmatter/content
- Anki tags matching Hugo categories — k8s::networking, linux::systemd,
databases::acid

The key insight: writing the blog is the encoding phase, Anki is the
retrieval phase. You need both. Most people only do one — they either write
  notes they never review, or make Anki cards without deeply understanding
the material first.