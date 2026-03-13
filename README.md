# Application Backend

This repo contains a server side part of application written in Django.

## Privacy and sharing (NDA)

Project name and domain terms are neutralized. Clone with a neutral folder name, e.g. `git clone <url> project-x`. This repository is prepared for sharing under NDA/compliance: all committed env files (`.envs/*`) and examples use **placeholder values only**. Do not commit real secrets, API keys, or client-specific data. Use `.env.example` as reference; set real values locally or via your CI/CD secrets. Replace generic CI names (e.g. `your-org`, `project-*`) in `.circleci/config.yml` with your own.

## Development

In the project directory, you can run:

#### `docker compose up`

Build and run application at the development mode. \
Open [http://localhost:8000](http://localhost:8000) to view it in the browser.

## Expert in the loop feature

To allow experts to review generated results, you must first create a group in the administrative panel in Django. After that we need to create users, who will be responsible for results review. Members of this group must have the following permissions:

<ul>
    <li>admin | log entry | Can view log entry</li>
    <li>algorithm | result | Can view result</li>
    <li>algorithm | result batch | Can view result batch</li>
    <li>core | questionnaire | Can view questionnaire</li>
    <li>expert | expert batch review | Can change expert batch review</li>
    <li>expert | expert batch review | Can view expert batch review</li>
    <li>expert | result review | Can add result review</li>
    <li>expert | result review | Can change result review</li>
    <li>expert | result review | Can delete result review</li>
    <li>expert | result review | Can view result review</li>
</ul>

## Application directory structure

Inside the application, the file directory has a standard structure for Django applications.

### App

Django project directory, that contains configurational files and directories of Django apps inside.

### Algorithm

Contains all functionality for generating and managing the results of the questionnaire.

### Core

Directory that manages users, questionnaires, gift-cards and other instances.

### Expert

To enable expert in the loop feature. Expert can make review to generated results and provide it to the customers.

### Tracker

Contains functionality to keep track of events connected to the questionnaire creation.
