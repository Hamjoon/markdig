You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Parsers/ListBlockParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Parsers/ListBlockParser.cs b/src/Markdig/Parsers/ListBlockParser.cs
index a17a48c7..e9dcf323 100644
--- a/src/Markdig/Parsers/ListBlockParser.cs
+++ b/src/Markdig/Parsers/ListBlockParser.cs
@@ -145,6 +145,7 @@ private BlockState TryContinueListItem(BlockProcessor state, ListItemBlock listI
             if (list.CountBlankLinesReset == 1 && listItem.ColumnWidth < 0)
             {
                 state.Close(listItem);
+                list.CountBlankLinesReset = 0;
 
                 // Leave the list open
                 list.IsOpen = true;
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3543, Skipped:     1, Total:  3544, Duration: 912 ms - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Parsers/ListBlockParser.cs" lines="123-173">
    private BlockState TryContinueListItem(BlockProcessor state, ListItemBlock listItem)
    {
        var list = (ListBlock)listItem.Parent!;

        // Allow all blanks lines if the last block is a fenced code block
        // Allow 1 blank line inside a list
        // If > 1 blank line, terminate this list
        if (state.IsBlankLine)
        {
            if (state.CurrentBlock != null && state.CurrentBlock.IsBreakable)
            {
                if (!(state.NextContinue is ListBlock))
                {
                    list.CountAllBlankLines++;
                    if (!state.TrackTrivia)
                    {
                        listItem.Add(new BlankLineBlock());
                    }
                }
                list.CountBlankLinesReset++;
            }

            if (list.CountBlankLinesReset == 1 && listItem.ColumnWidth < 0)
            {
                state.Close(listItem);
                list.CountBlankLinesReset = 0;

                // Leave the list open
                list.IsOpen = true;
                return BlockState.Continue;
            }

            // Update list-item source end position
            listItem.UpdateSpanEnd(state.Line.End);

            return BlockState.Continue;
        }

        list.CountBlankLinesReset = 0;

        int columnWidth = listItem.ColumnWidth;
        if (columnWidth < 0)
        {
            columnWidth = -columnWidth;
        }

        if (state.Indent >= columnWidth)
        {
            if (state.Indent > columnWidth && state.IsCodeIndent)
            {
                state.GoToColumn(state.ColumnBeforeIndent + columnWidth);
</production_snippet>
