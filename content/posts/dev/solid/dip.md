---
title: 'Dependencies Inversion Principle (DIP)'
date: 2025-11-07T14:40:27+07:00
draft: false
---

```text
High-level modules should not depend on low-level modules. Both should depend on abstractions.
```

At first, I need a tool to call Gitlab API and return processed response data. When the requirement extends I can not add another remote repository (e.g. GitHub)

High-level modules: business logic (return processed data)

Low-level modules: data access (call GitLab API)

Bad implementation:

```text
  ┌────────────────────────┐
  │   graph.go             │
  │ BuildDependencyGraph() │
  │                        │
  │ Receives & uses:       │
  │ - *gitlab.File         │
  │ - *gitlab.Project      │
  └────────────────────────┘
           ▲               │
           │               │
           │               │ DEPENDS ON
           │               │ (transitive)
  ┌────────┴──────────┐    │
  │   manifest.go     │    │
  │ GetDependencies() │    │
  │                   │    │
  │ Returns:          │    │
  │ - *gitlab.File    │    │
  │ - *gitlab.Project │    │
  └───────────────────┘    │
           ▲               │
           │               │
           │ imports       │
           │               ▼
  ┌────────┴────────────────────────┐
  │   EXTERNAL LIBRARY              │
  │   (GitLab SDK)                  │
  │                                 │
  │ - gitlab.Client                 │
  │ - gitlab.File                   │
  │ - gitlab.Project                │
  └─────────────────────────────────┘

Problem: graph.go is TIGHTLY COUPLED to GitLab SDK types,
even though it never directly imports the library!
```

Good implementation:

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                    YOUR ABSTRACTIONS                        │
  │              (interfaces.go + types.go)                     │
  │                                                             │
  │  - RepositoryClient interface                               │
  │  - ProjectDTO struct                                        │
  │  - FileDTO struct                                           │
  │  - ManifestFile struct                                      │
  └─────────────────────────────────────────────────────────────┘
                ▲                          ▲
                │                          │
                │ depends on               │ depends on
                │                          │
      ┌─────────┴─────────┐       ┌────────┴──────────┐
      │   HIGH-LEVEL      │       │   LOW-LEVEL       │
      │   (graph.go)      │       │  (manifest.go)    │
      │                   │       │                   │
      │ BuildReverseGraph │       │ Client struct     │
      │                   │       │ GetProjects()     │
      │ Takes:            │       │ GetProject()      │
      │ []*ManifestFile   │       │ GetDependency...()│
      │                   │       │                   │
      │ Uses:             │       │ Returns:          │
      │ - FileDTO.Path    │       │ - []*ProjectDTO   │
      │ - FileDTO.Content │       │ - *ProjectDTO     │
      │ - ProjectDTO.*    │       │ - *FileDTO        │
      └───────────────────┘       └───────────────────┘
                                           │
                                           │ uses internally
                                           ▼
                                  ┌─────────────────┐
                                  │  EXTERNAL LIB   │
                                  │  (GitLab SDK)   │
                                  │                 │
                                  │ gitlab.Client   │
                                  │ gitlab.Project  │
                                  │ gitlab.File     │
                                  └─────────────────┘

```

## Why this matters

In the bad implementation, your business logic is tightly coupled to GitLab's SDK. If you need to support GitHub, Bitbucket, or switch to a different GitLab SDK version, you'll need to modify your high-level business logic code. This violates the principle that stable, high-level policies should not depend on volatile, low-level details.

## Code example: the bad way

Here's what the problematic code looks like:

```go
// graph.go - High-level business logic
package graph

import (
    "gitlab.com/gitlab-org/api/client-go"
)

func BuildDependencyGraph(client *gitlab.Client, projectID int) (map[string][]string, error) {
    // Directly using GitLab-specific types
    project, _, err := client.Projects.GetProject(projectID, nil)
    if err != nil {
        return nil, err
    }

    file, _, err := client.RepositoryFiles.GetFile(
        projectID,
        "manifest.json",
        &gitlab.GetFileOptions{Ref: gitlab.String("main")},
    )
    if err != nil {
        return nil, err
    }

    // Business logic mixed with GitLab-specific details
    return buildGraph(project.Name, file.Content), nil
}
```

The problem: `BuildDependencyGraph` cannot work with GitHub, local files, or mock data for testing without changing the function signature and implementation.

## Code example: the good way

Now let's apply DIP by introducing abstractions:

```go
// types.go - Your domain types
package repository

type ProjectDTO struct {
    ID   int
    Name string
    URL  string
}

type FileDTO struct {
    Path    string
    Content string
}

// interfaces.go - Your abstraction
type RepositoryClient interface {
    GetProject(id int) (*ProjectDTO, error)
    GetFile(projectID int, path string, ref string) (*FileDTO, error)
}
```

```go
// graph.go - High-level business logic
package graph

import "your-module/repository"

func BuildDependencyGraph(client repository.RepositoryClient, projectID int) (map[string][]string, error) {
    // Works with ANY implementation of RepositoryClient
    project, err := client.GetProject(projectID)
    if err != nil {
        return nil, err
    }

    file, err := client.GetFile(projectID, "manifest.json", "main")
    if err != nil {
        return nil, err
    }

    // Pure business logic - no external library dependencies
    return buildGraph(project.Name, file.Content), nil
}
```

```go
// gitlab_client.go - Low-level implementation
package repository

import "github.com/xanzy/go-gitlab"

type GitLabClient struct {
    client *gitlab.Client
}

func (g *GitLabClient) GetProject(id int) (*ProjectDTO, error) {
    project, _, err := g.client.Projects.GetProject(id, nil)
    if err != nil {
        return nil, err
    }

    // Convert GitLab type to your domain type
    return &ProjectDTO{
        ID:   project.ID,
        Name: project.Name,
        URL:  project.WebURL,
    }, nil
}

func (g *GitLabClient) GetFile(projectID int, path string, ref string) (*FileDTO, error) {
    file, _, err := g.client.RepositoryFiles.GetFile(
        projectID,
        path,
        &gitlab.GetFileOptions{Ref: gitlab.String(ref)},
    )
    if err != nil {
        return nil, err
    }

    return &FileDTO{
        Path:    file.FileName,
        Content: file.Content,
    }, nil
}
```

Now you can easily add GitHub support without touching your business logic:

```go
// github_client.go - Another implementation
package repository

import "github.com/google/go-github/v57/github"

type GitHubClient struct {
    client *github.Client
}

func (g *GitHubClient) GetProject(id int) (*ProjectDTO, error) {
    // Implement using GitHub SDK
    // ...
}

func (g *GitHubClient) GetFile(projectID int, path string, ref string) (*FileDTO, error) {
    // Implement using GitHub SDK
    // ...
}
```

## Benefits you get

### 1. Testability without infrastructure

Mock the `RepositoryClient` interface for fast unit tests:

```go
type MockClient struct {
    projects map[int]*ProjectDTO
    files    map[string]*FileDTO
}

func (m *MockClient) GetProject(id int) (*ProjectDTO, error) {
    return m.projects[id], nil
}

func TestBuildDependencyGraph(t *testing.T) {
    mock := &MockClient{
        projects: map[int]*ProjectDTO{
            1: {ID: 1, Name: "my-project"},
        },
        files: map[string]*FileDTO{
            "manifest.json": {Content: `{"deps": ["dep1"]}`},
        },
    }

    // Test without GitLab/GitHub running!
    graph, err := BuildDependencyGraph(mock, 1)
    // assertions...
}
```

No Docker containers, no API tokens, no network calls. Tests run in milliseconds.

### 2. Flexibility to switch providers

Already shown above with GitHubClient, but the real power is you can support **multiple providers simultaneously**:

```go
func main() {
    var client repository.RepositoryClient

    switch os.Getenv("REPO_PROVIDER") {
    case "gitlab":
        client = &repository.GitLabClient{...}
    case "github":
        client = &repository.GitHubClient{...}
    case "local":
        client = &repository.LocalFileClient{...}
    }

    // Same code works for all providers
    graph, _ := graph.BuildDependencyGraph(client, projectID)
}
```

### 3. Stability against breaking changes

When GitLab SDK v5.0 drops support for `GetProject` in favor of `FetchProject`:

**With DIP**: Change one file (`gitlab_client.go`)
```go
func (g *GitLabClient) GetProject(id int) (*ProjectDTO, error) {
    // Old: project, _, err := g.client.Projects.GetProject(id, nil)
    project, _, err := g.client.Projects.FetchProject(id, nil) // Updated
    // rest stays the same
}
```

**Without DIP**: Update every file that calls GitLab SDK (10+ files? 50+ files?)

### 4. Parallel development

Frontend and backend teams can work simultaneously:

- Backend team: Implements `GitLabClient`
- Frontend/Business logic team: Works with `RepositoryClient` interface using mocks
- No blocking dependencies between teams

### 5. Local development without external services

```go
type LocalFileClient struct {
    basePath string
}

func (l *LocalFileClient) GetProject(id int) (*ProjectDTO, error) {
    // Read from local JSON file
    data, _ := os.ReadFile(filepath.Join(l.basePath, "project.json"))
    var project ProjectDTO
    json.Unmarshal(data, &project)
    return &project, nil
}
```

Develop on airplanes, trains, or anywhere without internet. No VPN required.

### 6. Easier debugging and performance profiling

Suspect the GitLab API is slow? Swap in a caching implementation:

```go
type CachedClient struct {
    underlying RepositoryClient
    cache      map[int]*ProjectDTO
}

func (c *CachedClient) GetProject(id int) (*ProjectDTO, error) {
    if cached, ok := c.cache[id]; ok {
        return cached, nil
    }
    project, err := c.underlying.GetProject(id)
    c.cache[id] = project
    return project, err
}
```

No changes to business logic. Just wrap the client.

### 7. Migration path for gradual changes

Migrating from GitLab to GitHub? Run both simultaneously:

```go
type DualClient struct {
    primary   RepositoryClient // GitLab
    secondary RepositoryClient // GitHub
}

func (d *DualClient) GetProject(id int) (*ProjectDTO, error) {
    project, err := d.primary.GetProject(id)
    if err != nil {
        log.Warn("Primary failed, trying secondary")
        return d.secondary.GetProject(id)
    }
    return project, err
}
```

Zero-downtime migration with fallback support.

## The key insight

The abstraction layer isn't just a technical detail—it's where you define **what your application needs** rather than **what external libraries happen to provide**. This inverts the traditional dependency direction: instead of your code depending on external libraries, external libraries are adapted to match your interfaces.

Your business logic owns the abstraction. External libraries are implementation details.
