# BOMWatcher

**Know every dependency and AI model your code ships with.**

BOMWatcher connects to your GitHub account and produces an **AI Bill of Materials**
for each repository you choose: a complete inventory of the libraries it depends on
and the AI models and AI services it uses. Results are in the open
[CycloneDX](https://cyclonedx.org/) format, so any tool that reads it can use them.

The scan runs on **your own GitHub Actions minutes**. Your source code never leaves
GitHub, and BOMWatcher only ever receives the finished report.

🔗 **Live:** [bomwatcher.vercel.app](https://bomwatcher.vercel.app)

## Why this exists

AI features are being added to codebases faster than anyone is tracking them. Teams
often can't answer simple questions: which models do we call, from which providers,
in which repos, and under what licenses?

This project grew out of real production work on CI/CD pipelines, where a security
and dependency scan gates a release before it ships. BOMWatcher applies the same
idea (scan as a pipeline stage, not an afterthought) to a self-serve product
anyone can connect their GitHub account to.

## How it works

1. **Sign up** and connect your GitHub account by installing the BOMWatcher GitHub App.
2. **Pick repos** to scan: some, or all.
3. **Review one pull request.** BOMWatcher opens a PR adding a small workflow file.
   Nothing runs until you merge it.
4. **The scan runs on GitHub's runners** on every push to your default branch.
5. **See the results** in your dashboard: libraries, AI models, AI services and
   license flags. Download the full BOM any time.

## What you get

- **Dependency inventory:** every library, with version, ecosystem and license.
- **AI model usage:** hosted models (Anthropic, OpenAI, Google, Mistral, Cohere) and
  open-weight models loaded from Hugging Face.
- **AI services:** the external AI APIs your code calls.
- **License review flags:** copyleft and non-commercial licenses highlighted before release.

## Privacy by design

- Your code is never cloned or uploaded anywhere.
- The workflow is added through a PR you review, and runs with read-only access.
- You can stop at any time by deleting the workflow file or uninstalling the app.

## Built with

React · FastAPI · PostgreSQL · GitHub Apps · GitHub Actions · CycloneDX

## Pricing

Free trial: up to 3 repositories per account.

## About the developer

Built by **Rao Rizwan**, a backend engineer working primarily in Python
(Django, FastAPI, Flask). Background includes Django REST APIs serving
100,000+ requests a day, Celery/RabbitMQ pipelines to keep slow work off the
request path, and CI/CD security scanning that gates releases before they ship.

- GitHub: [github.com/devRaoRizwan](https://github.com/devRaoRizwan)
- LinkedIn: [linkedin.com/in/raorixwan](https://linkedin.com/in/raorixwan)
- Portfolio: [devraorizwan.online](https://devraorizwan.online)
- Email: dev.raorizwan@gmail.com

Currently open to backend roles, remote or based in Lahore.
