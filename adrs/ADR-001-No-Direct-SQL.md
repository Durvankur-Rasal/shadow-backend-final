# ADR-001: No Direct SQL in Controllers

## Context
We are seeing SQL injection vulnerabilities and tight coupling in our API controllers.

## Decision
All database interaction must go through the `Repository` pattern. 
Direct usage of `SELECT *` or raw SQL strings inside `src/controllers/` is strictly forbidden.
Use the `QueryBuilder` class instead.

## Consequences
Code that imports `database.execute` directly in a controller will be rejected.