You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs, src/Markdig/Renderers/Roundtrip/ListRenderer.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs b/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs
index f35a2e8b..a65c3e71 100644
--- a/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs
+++ b/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs
@@ -25,6 +25,7 @@ public class TestUnorderedList
     [TestCase("-\ti1")]
     [TestCase("-\ti1\n-\ti2")]
     [TestCase("-\ti1\n-  i2\n-\ti3")]
+    [TestCase("- 1.\n- 2.")]
     public void Test(string value)
     {
         RoundTrip(value);
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed Test("- 1.\n- 2.") [13 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 9 but was 6. Strings differ at index 1.
  Expected: "- 1.\n- 2."
  But was:  "-\n- 2."
  ------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestRoundtrip.RoundTrip(String markdown, String context) in <worktree>/src/Markdig.Tests/TestRoundtrip.cs:line 27
   at Markdig.Tests.RoundtripSpecs.TestUnorderedList.Test(String value) in <worktree>/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs:line 31
   at InvokeStub_TestUnorderedList.Test(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestRoundtrip.RoundTrip(String markdown, String context) in <worktree>/src/Markdig.Tests/TestRoundtrip.cs:line 27
   at Markdig.Tests.RoundtripSpecs.TestUnorderedList.Test(String value) in <worktree>/src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs:line 31
   at InvokeStub_TestUnorderedList.Test(Object, Span`1)


  Standard Output Messages:
 ```````````````````Source

 ```````````````````Result
 -
 -·2.
 ```````````````````Expected
 -·1.
 -·2.
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 1      32   \u20;   10   \n
 *** 2      49   1     45   -
 *** 3      46   .     32   \u20;
 *** 4      10   \n    50   2
 *** 5      45   -     46   .
 *** 6      32   \u20;
 *** 7      50   2
 *** 8      46   .



Failed!  - Failed:     1, Passed:   124, Skipped:     0, Total:   125, Duration: 50 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/RoundtripSpecs/TestUnorderedList.cs" lines="3-53">
namespace Markdig.Tests.RoundtripSpecs;

[TestFixture]
public class TestUnorderedList
{
    // i = item
    [TestCase("- i1")]
    [TestCase("- i1 ")]
    [TestCase("- i1\n")]
    [TestCase("- i1\n\n")]
    [TestCase("- i1\n- i2")]
    [TestCase("- i1\n    - i2")]
    [TestCase("- i1\n    - i1.1\n    - i1.2")]
    [TestCase("- i1 \n- i2 \n")]
    [TestCase("- i1  \n- i2  \n")]
    [TestCase(" - i1")]
    [TestCase("  - i1")]
    [TestCase("   - i1")]
    [TestCase("- i1\n\n- i1")]
    [TestCase("- i1\n\n\n- i1")]
    [TestCase("- i1\n    - i1.1\n        - i1.1.1\n")]

    [TestCase("-\ti1")]
    [TestCase("-\ti1\n-\ti2")]
    [TestCase("-\ti1\n-  i2\n-\ti3")]
    [TestCase("- 1.\n- 2.")]
    public void Test(string value)
    {
        RoundTrip(value);
    }

    [TestCase("- > q")]
    [TestCase(" - > q")]
    [TestCase("  - > q")]
    [TestCase("   - > q")]
    [TestCase("-  > q")]
    [TestCase(" -  > q")]
    [TestCase("  -  > q")]
    [TestCase("   -  > q")]
    [TestCase("-   > q")]
    [TestCase(" -   > q")]
    [TestCase("  -   > q")]
    [TestCase("   -   > q")]
    [TestCase("-    > q")]
    [TestCase(" -    > q")]
    [TestCase("  -    > q")]
    [TestCase("   -    > q")]
    [TestCase("   -    > q1\n   -    > q2")]
    public void TestBlockQuote(string value)
    {
        RoundTrip(value);
</test_snippet>

<production_snippet path="src/Markdig/Renderers/Roundtrip/ListRenderer.cs" lines="1-56">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using Markdig.Helpers;
using Markdig.Syntax;

namespace Markdig.Renderers.Roundtrip;

/// <summary>
/// A Roundtrip renderer for a <see cref="ListBlock"/>.
/// </summary>
/// <seealso cref="RoundtripObjectRenderer{ListBlock}" />
public class ListRenderer : RoundtripObjectRenderer<ListBlock>
{
    protected override void Write(RoundtripRenderer renderer, ListBlock listBlock)
    {
        renderer.RenderLinesBefore(listBlock);
        if (listBlock.IsOrdered)
        {
            for (var i = 0; i < listBlock.Count; i++)
            {
                var item = listBlock[i];
                var listItem = (ListItemBlock) item;
                renderer.RenderLinesBefore(listItem);

                var bws = listItem.TriviaBefore.ToString();
                var bullet = listItem.SourceBullet.ToString();
                var delimiter = listBlock.OrderedDelimiter;
                renderer.PushIndent(new string[] { $"{bws}{bullet}{delimiter}" });
                renderer.WriteChildren(listItem);
                renderer.RenderLinesAfter(listItem);
            }
        }
        else
        {
            for (var i = 0; i < listBlock.Count; i++)
            {
                var item = listBlock[i];
                var listItem = (ListItemBlock) item;
                renderer.RenderLinesBefore(listItem);

                StringSlice bws = listItem.TriviaBefore;
                char bullet = listBlock.BulletType;
                StringSlice aws = listItem.TriviaAfter;

                renderer.PushIndent(new string[] { $"{bws}{bullet}{aws}" });
                if (listItem.Count == 0)
                {
                    renderer.Write(""); // trigger writing of indent
                }
                else
                {
                    renderer.WriteChildren(listItem);
                }
                renderer.PopIndent();
</production_snippet>
