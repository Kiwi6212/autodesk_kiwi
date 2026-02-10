# Grades Import Guide

## Overview

AutoDesk Kiwi supports manual grade import for the Hyperplanning section.

## Format

Grades must be provided as a JSON array. Each entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `subject` | string | Subject name (max 200 chars) |
| `date` | string | Grade date (max 50 chars) |
| `value` | number | Grade value (0-20) |

**Example:**

```json
[
  {"subject": "Admin & sec infra reseau", "date": "18 dec.", "value": 18.39},
  {"subject": "Anglais", "date": "13 dec.", "value": 15.50},
  {"subject": "Supervision des infras", "date": "12 dec.", "value": 10.00}
]
```

## Import Steps

1. Open the Hyperplanning tab
2. In the grades section, click "Import"
3. Paste the JSON content
4. Confirm the import

Grades are saved to the SQLite database and persist across restarts.

## API Endpoints

### GET `/hyperplanning/grades`

Returns all grades sorted by creation date (descending).

### POST `/hyperplanning/grades/import`

Replaces all existing grades with the provided data.

**Request body:**

```json
{
  "grades": [
    {"subject": "Subject", "date": "13 dec.", "value": 15.5}
  ]
}
```

### DELETE `/hyperplanning/grades/clear`

Deletes all grades.

## Validation

- `subject`: required, max 200 characters
- `date`: required, max 50 characters
- `value`: required, must be between 0 and 20

## Troubleshooting

| Error | Cause |
|-------|-------|
| Invalid JSON format | Check syntax (commas, quotes, brackets) |
| JSON must be an array | Content must start with `[` and end with `]` |
| Value must be between 0 and 20 | Use decimal notation if needed (e.g., 15.5) |
