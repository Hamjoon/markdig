You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestCodeInline.cs, src/Markdig/Parsers/Inlines/CodeInlineParser.cs, src/Markdig/Polyfills/SpanExtensions.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/TestCodeInline.cs b/src/Markdig.Tests/TestCodeInline.cs
new file mode 100644
index 00000000..b5427647
--- /dev/null
+++ b/src/Markdig.Tests/TestCodeInline.cs
@@ -0,0 +1,10 @@
+namespace Markdig.Tests;
+
+public class TestCodeInline
+{
+    [Test]
+    public void UnpairedCodeInlineWithTrailingChars()
+    {
+        TestParser.TestSpec("*`\n\f", "<p>*`</p>");
+    }
+}
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed UnpairedCodeInlineWithTrailingChars [8 ms]
  Error Message:
   System.IndexOutOfRangeException : Index was outside the bounds of the array.
  Stack Trace:
     at Markdig.Parsers.Inlines.CodeInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/CodeInlineParser.cs:line 30
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 273
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 172
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 75
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 101
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 93
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.TestCodeInline.UnpairedCodeInlineWithTrailingChars() in <worktree>/src/Markdig.Tests/TestCodeInline.cs:line 8
   at System.RuntimeMethodHandle.InvokeMethod(Object target, Void** arguments, Signature sig, Boolean isConstructor)
   at System.Reflection.MethodBaseInvoker.InvokeWithNoArgs(Object obj, BindingFlags invokeAttr)


Failed!  - Failed:     1, Passed:    45, Skipped:     0, Total:    46, Duration: 34 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestCodeInline.cs" lines="1-10">
namespace Markdig.Tests;

public class TestCodeInline
{
    [Test]
    public void UnpairedCodeInlineWithTrailingChars()
    {
        TestParser.TestSpec("*`\n\f", "<p>*`</p>");
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Parsers/Inlines/CodeInlineParser.cs" lines="58-113">
            int i = span.IndexOfAny('\r', '\n', match);

            if ((uint)i >= (uint)span.Length)
            {
                // We got to the end of the input before seeing the match character. CodeInline can't match here.
                return false;
            }

            int closeSticks = 0;

            while ((uint)i < (uint)span.Length && span[i] == match)
            {
                closeSticks++;
                i++;
            }

            span = span.Slice(i);

            if (openSticks == closeSticks)
            {
                break;
            }

            if (closeSticks == 0)
            {
                ReadOnlySpan<char> lookAhead = span.Length > 1 ? span.Slice(1) : ReadOnlySpan<char>.Empty;
                while (!lookAhead.IsEmpty && (lookAhead[0] == '\r' || lookAhead[0] == '\n'))
                {
                    lookAhead = lookAhead.Slice(1);
                }
                if (lookAhead[0] == '|')
                {
                    // We saw the start of a code inline, but the close sticks are not present on the same line.
                    // If the next line starts with a pipe character, this is likely an incomplete CodeInline within a table.
                    // Treat it as regular text to avoid breaking the overall table shape.
                    if (processor.Inline != null && processor.Inline.ContainsParentOfType<PipeTableDelimiterInline>())
                    {
                        slice.Start = openingStart;
                        return false;
                    }
                }

                containsNewLines = true;
                span = span.Slice(1);
            }
        }

        ReadOnlySpan<char> rawContent = slice.AsSpan().Slice(0, slice.Length - span.Length - openSticks);

        var content = containsNewLines
            ? new LazySubstring(ReplaceNewLines(rawContent)) // Should be the rare path.
            : new LazySubstring(slice.Text, slice.Start, rawContent.Length);

        // Remove one space from front and back if the string is not all spaces
        if (rawContent.Length > 2 &&
            rawContent[0] is ' ' or '\n' &&
</production_snippet>

<production_snippet path="src/Markdig/Polyfills/SpanExtensions.cs" lines="1-23">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license.
// See the license.txt file in the project root for more information.

#if NET462 || NETSTANDARD2_0

using System.Diagnostics;

namespace System;

internal static class SpanExtensions
{
    public static bool StartsWith(this ReadOnlySpan<char> span, string prefix, StringComparison comparisonType)
    {
        Debug.Assert(comparisonType is StringComparison.Ordinal or StringComparison.OrdinalIgnoreCase);

        return
            span.Length >= prefix.Length &&
            span.Slice(0, prefix.Length).Equals(prefix.AsSpan(), comparisonType);
    }
}

#endif
</production_snippet>
