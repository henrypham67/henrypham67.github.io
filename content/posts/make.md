---
title: 'Make'
date: 2024-12-24T13:16:44+07:00
draft: true
---

## What are main syntax?

```makefile
target: dependencies
  commands
```

## why path to main.go is defined as a dependency?

```make
$(BIN_DIR)/$(APP_NAME_1): $(SRC_DIR)/$(APP_NAME_1)/main.go
  mkdir -p $(BIN_DIR)
  go build $(GO_FLAGS) -o $@ $(SRC_DIR)/$(APP_NAME_1)
```

## Why there is `@` in front of some cmd?

## What is `.PHONY` used for?

By default, Makefile targets are "file targets" - they are used to build files from other files. Make assumes its target is a file, and this makes writing Makefiles relatively easy:

foo: bar
  create_one_from_the_other foo bar
However, sometimes, you want your Makefile to run commands that do not represent physical files in the file system. Good examples of this are the common targets "clean" and "all". Chances are this isn't the case, but you may potentially have a file named clean in your main directory. In such a case Make will be confused because by default the clean target would be associated with this file and Make will only run it when the file doesn't appear to be up-to-date with regards to its dependencies.

These special targets are called phony and you can explicitly tell Make they're not associated with files, e.g.:

.PHONY: clean
clean:
  rm -rf *.o
Now make clean will run as expected even if you do have a file named clean.

In terms of Make, a phony target is simply a target that is always out-of-date, so whenever you ask make <phony_target>, it will run, independent from the state of the file system. Some common make targets that are often phony are: all, install, clean, distclean, TAGS, info, check.