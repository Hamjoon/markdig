You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs, src/Markdig/Renderers/Roundtrip/Inlines/LinkInlineRenderer.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs b/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs
index b5b67b79..5e5eb143 100644
--- a/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs
+++ b/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs
@@ -1,3 +1,6 @@
+using System.IO;
+using Markdig.Renderers.Roundtrip;
+using Markdig.Syntax;
 using NUnit.Framework;
 using static Markdig.Tests.TestRoundtrip;
 
@@ -19,5 +22,24 @@ public void Test(string value)
         {
             RoundTrip(value);
         }
+
+        [TestCase("http://example.com/", "[http://example.com/](http://example.com/)")]
+        [TestCase("www.example.com", "[www.example.com](http://www.example.com)")]
+        [TestCase("mailto:user@example.com", "[user@example.com](mailto:user@example.com)")]
+        public void AutoLinksKeepUrlWhenRoundTripped(string markdown, string expected)
+        {
+            var pipeline = new MarkdownPipelineBuilder()
+                .DisableHtml()
+                .UseAutoLinks()
+                .EnableTrackTrivia()
+                .Build();
+            MarkdownDocument markdownDocument = Markdown.Parse(markdown, pipeline);
+            var sw = new StringWriter();
+            var rr = new RoundtripRenderer(sw);
+
+            rr.Write(markdownDocument);
+
+            Assert.AreEqual(expected, sw.ToString());
+        }
     }
 }
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Failed AutoLinksKeepUrlWhenRoundTripped("http://example.com/","[http://example.com/](http://example.com/)") [30 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 42 but was 23. Strings differ at index 22.
  Expected: "[http://example.com/](http://example.com/)"
  But was:  "[http://example.com/]()"
  ---------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42


  Failed AutoLinksKeepUrlWhenRoundTripped("www.example.com","[www.example.com](http://www.example.com)") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 41 but was 19. Strings differ at index 18.
  Expected: "[www.example.com](http://www.example.com)"
  But was:  "[www.example.com]()"
  -----------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42
   at InvokeStub_TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42
   at InvokeStub_TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(Object, Span`1)


  Failed AutoLinksKeepUrlWhenRoundTripped("mailto:user@example.com","[user@example.com](mailto:user@example.com)") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 43 but was 20. Strings differ at index 19.
  Expected: "[user@example.com](mailto:user@example.com)"
  But was:  "[user@example.com]()"
  ------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42
   at InvokeStub_TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.RoundtripSpecs.Inlines.TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(String markdown, String expected) in <worktree>/src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs:line 42
   at InvokeStub_TestAutoLinkInline.AutoLinksKeepUrlWhenRoundTripped(Object, Span`1)



Failed!  - Failed:     3, Passed:     9, Skipped:     0, Total:    12, Duration: 41 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/RoundtripSpecs/Inlines/TestAutoLinkInline.cs" lines="1-45">
using System.IO;
using Markdig.Renderers.Roundtrip;
using Markdig.Syntax;
using NUnit.Framework;
using static Markdig.Tests.TestRoundtrip;

namespace Markdig.Tests.RoundtripSpecs.Inlines
{
    [TestFixture]
    public class TestAutoLinkInline
    {
        [TestCase("<http://a>")]
        [TestCase(" <http://a>")]
        [TestCase("<http://a> ")]
        [TestCase(" <http://a> ")]
        [TestCase("<example@example.com>")]
        [TestCase(" <example@example.com>")]
        [TestCase("<example@example.com> ")]
        [TestCase(" <example@example.com> ")]
        [TestCase("p http://a p")]
        public void Test(string value)
        {
            RoundTrip(value);
        }

        [TestCase("http://example.com/", "[http://example.com/](http://example.com/)")]
        [TestCase("www.example.com", "[www.example.com](http://www.example.com)")]
        [TestCase("mailto:user@example.com", "[user@example.com](mailto:user@example.com)")]
        public void AutoLinksKeepUrlWhenRoundTripped(string markdown, string expected)
        {
            var pipeline = new MarkdownPipelineBuilder()
                .DisableHtml()
                .UseAutoLinks()
                .EnableTrackTrivia()
                .Build();
            MarkdownDocument markdownDocument = Markdown.Parse(markdown, pipeline);
            var sw = new StringWriter();
            var rr = new RoundtripRenderer(sw);

            rr.Write(markdownDocument);

            Assert.AreEqual(expected, sw.ToString());
        }
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Renderers/Roundtrip/Inlines/LinkInlineRenderer.cs" lines="26-76">
        renderer.WriteChildren(link);
        renderer.Write(']');

        if (link.Label != null)
        {
            if (link.LocalLabel == LocalLabel.Local || link.LocalLabel == LocalLabel.Empty)
            {
                renderer.Write('[');
                if (link.LocalLabel == LocalLabel.Local)
                {
                    renderer.Write(link.LabelWithTrivia);
                }
                renderer.Write(']');
            }
        }
        else
        {
            if (link.Url != null)
            {
                renderer.Write('(');
                renderer.Write(link.TriviaBeforeUrl);
                if (link.UrlHasPointyBrackets)
                {
                    renderer.Write('<');
                }
                renderer.Write(link.UnescapedUrl);
                if (link.UrlHasPointyBrackets)
                {
                    renderer.Write('>');
                }
                renderer.Write(link.TriviaAfterUrl);

                if (!string.IsNullOrEmpty(link.Title))
                {
                    var open = link.TitleEnclosingCharacter;
                    var close = link.TitleEnclosingCharacter;
                    if (link.TitleEnclosingCharacter == '(')
                    {
                        close = ')';
                    }
                    renderer.Write(open);
                    renderer.Write(link.UnescapedTitle);
                    renderer.Write(close);
                    renderer.Write(link.TriviaAfterTitle);
                }

                renderer.Write(')');
            }
        }
    }
}
</production_snippet>
