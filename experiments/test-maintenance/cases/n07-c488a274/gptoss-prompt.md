You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Parsers/BlockState.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Parsers/BlockState.cs b/src/Markdig/Parsers/BlockState.cs
index bd1fbc7f..1172f629 100644
--- a/src/Markdig/Parsers/BlockState.cs
+++ b/src/Markdig/Parsers/BlockState.cs
@@ -10,32 +10,34 @@ namespace Markdig.Parsers;
 public enum BlockState
 {
     /// <summary>
-    /// A line is not accepted by this parser.
+    /// The parser does not accept the line for this block.
+    /// No line content is consumed by this result.
     /// </summary>
     None,
 
     /// <summary>
-    /// The parser is skipped.
+    /// Skips this parser for the current line and continues with the next parser/candidate block.
     /// </summary>
     Skip,
 
     /// <summary>
-    /// The parser accepts a line and instruct to continue.
+    /// The parser accepts the line and keeps the block open.
+    /// For leaf blocks, the current line is appended to the block.
     /// </summary>
     Continue,
 
     /// <summary>
-    /// The parser accepts a line, instruct to continue but discard the line (not stored on the block)
+    /// The parser accepts the line and keeps the block open, but the line is consumed and not appended.
     /// </summary>
     ContinueDiscard,
 
     /// <summary>
-    /// The parser is ending a block, instruct to stop and keep the line being processed.
+    /// The parser ends the block and keeps the current line available for further parsing.
     /// </summary>
     Break,
 
     /// <summary>
-    /// The parser is ending a block, instruct to stop and discard the line being processed.
+    /// The parser ends the block and consumes the current line.
     /// </summary>
     BreakDiscard
-}
\ No newline at end of file
+}
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3606, Skipped:     1, Total:  3607, Duration: 952 ms - Markdig.Tests.dll (net10.0)
</test_output>

<production_snippet path="src/Markdig/Parsers/BlockState.cs" lines="1-43">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

namespace Markdig.Parsers;

/// <summary>
/// Defines the result of parsing a line for a <see cref="BlockParser"/>.
/// </summary>
public enum BlockState
{
    /// <summary>
    /// The parser does not accept the line for this block.
    /// No line content is consumed by this result.
    /// </summary>
    None,

    /// <summary>
    /// Skips this parser for the current line and continues with the next parser/candidate block.
    /// </summary>
    Skip,

    /// <summary>
    /// The parser accepts the line and keeps the block open.
    /// For leaf blocks, the current line is appended to the block.
    /// </summary>
    Continue,

    /// <summary>
    /// The parser accepts the line and keeps the block open, but the line is consumed and not appended.
    /// </summary>
    ContinueDiscard,

    /// <summary>
    /// The parser ends the block and keeps the current line available for further parsing.
    /// </summary>
    Break,

    /// <summary>
    /// The parser ends the block and consumes the current line.
    /// </summary>
    BreakDiscard
}
</production_snippet>
