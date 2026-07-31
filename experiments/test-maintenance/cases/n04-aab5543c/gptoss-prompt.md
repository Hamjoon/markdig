You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Parsers/BlockProcessor.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Parsers/BlockProcessor.cs b/src/Markdig/Parsers/BlockProcessor.cs
index 236bac7a..39f03d3f 100644
--- a/src/Markdig/Parsers/BlockProcessor.cs
+++ b/src/Markdig/Parsers/BlockProcessor.cs
@@ -485,15 +485,11 @@ public void Discard(Block block)
     /// Processes a new line.
     /// </summary>
     /// <param name="newLine">The new line.</param>
-    /// <param name="column">The offset.</param>
-    public void ProcessLine(StringSlice newLine, int column = 0)
+    public void ProcessLine(StringSlice newLine)
     {
         CurrentLineStartPosition = newLine.Start;
 
-        if (column == 0)
-        {
-            Document.LineStartIndexes?.Add(CurrentLineStartPosition);
-        }
+        Document.LineStartIndexes?.Add(CurrentLineStartPosition);
 
         ContinueProcessingLine = true;
 
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3541, Skipped:     1, Total:  3542, Duration: 931 ms - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Parsers/BlockProcessor.cs" lines="463-517">
            }
        }
    }

    /// <summary>
    /// Discards the specified block from the stack, remove from its parent.
    /// </summary>
    /// <param name="block">The block.</param>
    public void Discard(Block block)
    {
        for (int i = OpenedBlocks.Count - 1; i >= 1; i--)
        {
            if (ReferenceEquals(OpenedBlocks[i].Block, block))
            {
                block.Parent!.Remove(block);
                OpenedBlocks.RemoveAt(i);
                break;
            }
        }
    }

    /// <summary>
    /// Processes a new line.
    /// </summary>
    /// <param name="newLine">The new line.</param>
    public void ProcessLine(StringSlice newLine)
    {
        CurrentLineStartPosition = newLine.Start;

        Document.LineStartIndexes?.Add(CurrentLineStartPosition);

        ContinueProcessingLine = true;

        ResetLine(newLine, 0);

        Process();

        LineIndex++;
    }

    /// <summary>
    /// Processes part of a line.
    /// </summary>
    /// <param name="line">The line.</param>
    /// <param name="column">The column.</param>
    public void ProcessLinePart(StringSlice line, int column)
    {
        CurrentLineStartPosition = line.Start - column;

        ContinueProcessingLine = true;

        ResetLine(line, column);

        Process();
    }
</production_snippet>
