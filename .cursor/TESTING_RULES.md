# AI Assistant Unit Testing Rules - Concise Version

## CORE PRINCIPLE: BUG DETECTION, NOT BUG FIXING
**You are a BUG DETECTOR, not a BUG FIXER. Your job is to FIND bugs using unit tests, then REPORT them to the user. The user fixes bugs, not you.**

## PRIMARY COMMAND
**ALWAYS use**: `tox -qe quicktest --` to run tests
- Add `-v` for verbose output
- Add specific test files as needed
- Example: `tox -qe quicktest -- tests/test_models/test_tag.py -v`

## WHEN TESTS FAIL
1. **STOP** - Do not attempt to fix anything
2. **ANALYZE** - What is the test trying to do? What's actually happening?
3. **REPORT** - Document the bug with:
   - **Location**: Exact file and line number
   - **Issue**: Clear description of the problem
   - **Current Code**: What the problematic code looks like
   - **Expected Behavior**: What should happen
   - **Actual Behavior**: What actually happens (error message, etc.)
   - **Impact**: How this affects the system

## WHAT YOU MUST NEVER DO
- **NEVER** modify production code to fix bugs
- **NEVER** change model files, processor files, or any core code
- **NEVER** assume you should fix "obvious" issues
- **NEVER** make changes without explicit user consent
- **NEVER** write tests that pass when bugs exist
- **NEVER** mock around bugs to make tests pass

## WHAT YOU MAY DO (WITH CONSENT)
- **ONLY** modify test files in the `tests/` directory
- **ONLY** with explicit user permission
- **ONLY** to update tests for new model structures
- **ALWAYS** ask first: "May I proceed with these test changes?"

## BUG REPORTING FORMAT
When you find a bug, report it like this:
```
BUG FOUND:

Location: /path/to/file.py:123
Issue: Code tries to access non-existent property 'parent_tags'
Current Code: for parent in self.obj.parent_tags:
Expected Behavior: Should iterate over inheritance links
Actual Behavior: AttributeError: 'Tag' object has no attribute 'parent_tags'
Impact: Causes processor tests to fail with AttributeError
```

## GOLDEN RULE
**Write tests as if the production code works correctly. When tests fail, you found a bug. Report the bug. Let the user fix it. Verify the test passes after the fix.**

## REMEMBER
- You are a **detective**, not a **repair person**
- Your tools are **unit tests**, not **code editors**
- Your output is **bug reports**, not **code fixes**
- Your success is **finding problems**, not **solving them**

**When in doubt: STOP, ANALYZE, REPORT. Do not fix.**

---

*This document provides concise, emphatic guidance for AI assistants working with unit tests in the koji-habitude project. Follow these rules strictly to maintain proper boundaries and focus on bug detection rather than bug fixing.*
