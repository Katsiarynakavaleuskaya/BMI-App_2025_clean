# TODO Update Process

This document describes the process for keeping the project TODO files up to date.

## Files to Update

1. [PROJECT_TODO.md](PROJECT_TODO.md) - Main project tracking in English
2. [TODO.md](TODO.md) - Additional tasks and issues in Russian

## When to Update

- When starting work on a new task
- When completing a task
- When discovering new issues or problems
- During weekly project reviews
- Before team meetings

## How to Update

### Marking Tasks as Complete

1. Move the task from "In Progress" or "Pending Tasks" to "Completed Tasks"
2. Change the checkbox from `[ ]` to `[x]`
3. Add any relevant notes about the completion if necessary

### Adding New Tasks

1. Add the task to the appropriate section:
   - "In Progress" for tasks currently being worked on
   - "Pending Tasks" for tasks planned for the future
   - "Current Issues and Problems" for newly discovered issues
2. Use the appropriate checkbox format: `[ ]`
3. Prioritize tasks by adding them to the correct priority section if applicable

### Updating Task Status

1. Move tasks between sections as their status changes
2. Update checkboxes to reflect current status
3. Add dates or notes if relevant

## Review Process

1. All team members should review the TODO files at the beginning of each workday
2. During weekly team meetings, review and update the TODO files together
3. Before making commits, check if any TODO items were affected by the changes

## Current Issues Tracking

The "Current Issues and Problems" section should be updated with any newly discovered issues, including:
- Performance problems
- Integration issues
- Bug reports
- Technical debt items
- Deployment issues

## Communication

When working on a task:
1. Immediately mark it as in progress in the TODO files
2. Comment on the specific task line with your GitHub username or initials
3. Update the status when you complete the task or encounter blockers

## Example Updates

### Before:

```markdown
### Database Expansion and Integration
- [ ] Research FooDB API/data format and create adapter to enhance phytonutrient data
```

### After starting work:

```markdown
### Database Expansion and Integration
- [ ] Research FooDB API/data format and create adapter to enhance phytonutrient data (@john)
```

### After completion:

```markdown
## Completed Tasks

### Database Expansion and Integration
- [x] Research FooDB API/data format and create adapter to enhance phytonutrient data
```
