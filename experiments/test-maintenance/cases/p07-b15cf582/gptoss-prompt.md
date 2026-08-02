You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestHtmlCodeBlocks.cs, src/Markdig/Parsers/HtmlBlockParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/TestHtmlCodeBlocks.cs b/src/Markdig.Tests/TestHtmlCodeBlocks.cs
new file mode 100644
index 00000000..5935d6ef
--- /dev/null
+++ b/src/Markdig.Tests/TestHtmlCodeBlocks.cs
@@ -0,0 +1,35 @@
+using Markdig.Syntax;
+
+namespace Markdig.Tests;
+
+public class TestHtmlCodeBlocks
+{
+    // Start condition: line begins with the string < or </ followed by one of the strings (case-insensitive)
+    // {list of all tags}, followed by a space, a tab, the end of the line, the string >, or the string />.
+    public static string[] KnownSimpleHtmlTags =>
+    [
+        "address", "article", "aside", "base", "basefont", "blockquote", "body", "caption", "center", "col", "colgroup", "dd", "details",
+        "dialog", "dir", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "frame", "frameset",
+        "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hr", "html", "iframe", "legend", "li", "link",
+        "main", "menu", "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
+        "search", "section", "summary", "table", "tbody", "td", "tfoot", "th", "thead", "title", "tr", "track", "ul",
+    ];
+
+    [Theory]
+    [TestCaseSource(nameof(KnownSimpleHtmlTags))]
+    public void TestKnownTags(string tag)
+    {
+        MarkdownDocument document = Markdown.Parse(
+            $"""
+            Hello
+             <{tag} />
+            World
+            """.ReplaceLineEndings("\n"));
+
+        HtmlBlock[] htmlBlocks = document.Descendants<HtmlBlock>().ToArray();
+
+        Assert.AreEqual(1, htmlBlocks.Length);
+        Assert.AreEqual(7, htmlBlocks[0].Span.Start);
+        Assert.AreEqual(10 + tag.Length, htmlBlocks[0].Span.Length);
+    }
+}
\ No newline at end of file
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed TestKnownTags("search") [14 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected: 1
  But was:  0

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestHtmlCodeBlocks.TestKnownTags(String tag) in <worktree>/src/Markdig.Tests/TestHtmlCodeBlocks.cs:line 31
   at InvokeStub_TestHtmlCodeBlocks.TestKnownTags(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestHtmlCodeBlocks.TestKnownTags(String tag) in <worktree>/src/Markdig.Tests/TestHtmlCodeBlocks.cs:line 31
   at InvokeStub_TestHtmlCodeBlocks.TestKnownTags(Object, Span`1)



Failed!  - Failed:     1, Passed:    61, Skipped:     0, Total:    62, Duration: 34 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestHtmlCodeBlocks.cs" lines="1-35">
using Markdig.Syntax;

namespace Markdig.Tests;

public class TestHtmlCodeBlocks
{
    // Start condition: line begins with the string < or </ followed by one of the strings (case-insensitive)
    // {list of all tags}, followed by a space, a tab, the end of the line, the string >, or the string />.
    public static string[] KnownSimpleHtmlTags =>
    [
        "address", "article", "aside", "base", "basefont", "blockquote", "body", "caption", "center", "col", "colgroup", "dd", "details",
        "dialog", "dir", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "frame", "frameset",
        "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hr", "html", "iframe", "legend", "li", "link",
        "main", "menu", "menuitem", "nav", "noframes", "ol", "optgroup", "option", "p", "param",
        "search", "section", "summary", "table", "tbody", "td", "tfoot", "th", "thead", "title", "tr", "track", "ul",
    ];

    [Theory]
    [TestCaseSource(nameof(KnownSimpleHtmlTags))]
    public void TestKnownTags(string tag)
    {
        MarkdownDocument document = Markdown.Parse(
            $"""
            Hello
             <{tag} />
            World
            """.ReplaceLineEndings("\n"));

        HtmlBlock[] htmlBlocks = document.Descendants<HtmlBlock>().ToArray();

        Assert.AreEqual(1, htmlBlocks.Length);
        Assert.AreEqual(7, htmlBlocks[0].Span.Start);
        Assert.AreEqual(10 + tag.Length, htmlBlocks[0].Span.Length);
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Parsers/HtmlBlockParser.cs" lines="273-323">

        return result;
    }

    private BlockState CreateHtmlBlock(BlockProcessor state, HtmlBlockType type, int startColumn, int startPosition)
    {
        var htmlBlock = new HtmlBlock(this)
        {
            Column = startColumn,
            Type = type,
            // By default, setup to the end of line
            Span = new SourceSpan(startPosition, startPosition + state.Line.End),
            //BeforeWhitespace = state.PopBeforeWhitespace(startPosition - 1),
        };

        if (state.TrackTrivia)
        {
            htmlBlock.LinesBefore = state.UseLinesBefore();
            htmlBlock.NewLine = state.Line.NewLine;
        }

        state.NewBlocks.Push(htmlBlock);
        return BlockState.Continue;
    }

    private static readonly CompactPrefixTree<int> HtmlTags = new(66, 94, 83)
    {
        { "address", 0 },
        { "article", 1 },
        { "aside", 2 },
        { "base", 3 },
        { "basefont", 4 },
        { "blockquote", 5 },
        { "body", 6 },
        { "caption", 7 },
        { "center", 8 },
        { "col", 9 },
        { "colgroup", 10 },
        { "dd", 11 },
        { "details", 12 },
        { "dialog", 13 },
        { "dir", 14 },
        { "div", 15 },
        { "dl", 16 },
        { "dt", 17 },
        { "fieldset", 18 },
        { "figcaption", 19 },
        { "figure", 20 },
        { "footer", 21 },
        { "form", 22 },
        { "frame", 23 },
</production_snippet>

<production_snippet path="src/Markdig/Parsers/HtmlBlockParser.cs" lines="340-367">
        { "menu", 40 },
        { "menuitem", 41 },
        { "nav", 42 },
        { "noframes", 43 },
        { "ol", 44 },
        { "optgroup", 45 },
        { "option", 46 },
        { "p", 47 },
        { "param", 48 },
        { "pre", 49 },      // <=== special group 1
        { "script", 50 },   // <=== special group 1
        { "section", 51 },
        { "source", 52 },
        { "style", 53 },    // <=== special group 1
        { "summary", 54 },
        { "table", 55 },
        { "textarea", 56 }, // <=== special group 1
        { "tbody", 57 },
        { "td", 58 },
        { "tfoot", 59 },
        { "th", 60 },
        { "thead", 61 },
        { "title", 62 },
        { "tr", 63 },
        { "track", 64 },
        { "ul", 65 }
    };
}
</production_snippet>
