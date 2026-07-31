You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig/Renderers/TextRendererBase.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Renderers/TextRendererBase.cs b/src/Markdig/Renderers/TextRendererBase.cs
index ef4dd525..cb2b0da1 100644
--- a/src/Markdig/Renderers/TextRendererBase.cs
+++ b/src/Markdig/Renderers/TextRendererBase.cs
@@ -176,6 +176,8 @@ public void PopIndent()
     {
         if (this.indents.Count > 0)
             indents.RemoveAt(indents.Count - 1);
+        else
+            throw new InvalidOperationException("No indent to pop");
     }
 
     public void ClearIndent() => indents.Clear();
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Skipped ListUnorderedLooseTop [< 1 ms]

Passed!  - Failed:     0, Passed:  3444, Skipped:     1, Total:  3445, Duration: 1 s - Markdig.Tests.dll (net9.0)
</test_output>

<production_snippet path="src/Markdig/Renderers/TextRendererBase.cs" lines="154-205">
            Writer.WriteLine();
        }
        return (T)this;
    }

    public void PushIndent(string indent)
    {
        if (indent is null) ThrowHelper.ArgumentNullException(nameof(indent));
        indents.Add(new Indent(indent));
    }

    public void PushIndent(string[] lineSpecific)
    {
        if (indents is null) ThrowHelper.ArgumentNullException(nameof(indents));
        indents.Add(new Indent(lineSpecific));

        // ensure that indents are written to the output stream
        // this assumes that calls after PushIndent wil write children content
        previousWasLine = true;
    }

    public void PopIndent()
    {
        if (this.indents.Count > 0)
            indents.RemoveAt(indents.Count - 1);
        else
            throw new InvalidOperationException("No indent to pop");
    }

    public void ClearIndent() => indents.Clear();

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private protected void WriteIndent()
    {
        if (previousWasLine)
        {
            WriteIndentCore();
        }
    }

    private void WriteIndentCore()
    {
        previousWasLine = false;
        for (int i = 0; i < indents.Count; i++)
        {
            var indent = indents[i];
            var indentText = indent.Next();
            Writer.Write(indentText);
        }
    }

    /// <summary>
</production_snippet>
