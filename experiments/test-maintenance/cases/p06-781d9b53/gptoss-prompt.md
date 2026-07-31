You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/Specs/GenericAttributesSpecs.md, src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/Specs/GenericAttributesSpecs.md b/src/Markdig.Tests/Specs/GenericAttributesSpecs.md
index a0c46e40..3fee4340 100644
--- a/src/Markdig.Tests/Specs/GenericAttributesSpecs.md
+++ b/src/Markdig.Tests/Specs/GenericAttributesSpecs.md
@@ -61,3 +61,12 @@ Attribute values can be one character long
 <p><a href="url" data-x="1">Foo</a></p>
 <p><a href="url" data-x="11">Foo</a></p>
 ````````````````````````````````
+
+Attributes that occur immediately before a block element, on a line by themselves, affect that element
+
+```````````````````````````````` example
+{.center}
+A paragraph
+.
+<p class="center">A paragraph</p>
+````````````````````````````````
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed ExtensionsGenericAttributes_Example004 [13 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 33 but was 34. Strings differ at index 18.
  Expected: "<p class="center">A paragraph</p>"
  But was:  "<p class="center">\nA paragraph</p>"
  -----------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.Specs.GenericAttributes.TestExtensionsGenericAttributes.ExtensionsGenericAttributes_Example004() in <worktree>/src/Markdig.Tests/Specs/GenericAttributesSpecs.generated.cs:line 116

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.Specs.GenericAttributes.TestExtensionsGenericAttributes.ExtensionsGenericAttributes_Example004() in <worktree>/src/Markdig.Tests/Specs/GenericAttributesSpecs.generated.cs:line 116


  Standard Output Messages:
 Example 4
 Section Extensions / Generic Attributes

 Pipeline configured with extensions: attributes
 ```````````````````Source
 {.center}
 A·paragraph
 ```````````````````Result
 <p·class="center">
 A·paragraph</p>
 ```````````````````Expected
 <p·class="center">A·paragraph</p>
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 18     65   A     10   \n
 *** 19     32   \u20;   65   A
 *** 20     112  p     32   \u20;
 *** 21     97   a     112  p
 *** 22     114  r     97   a
 *** 23     97   a     114  r
 *** 24     103  g     97   a
 *** 25     114  r     103  g
 *** 26     97   a     114  r
 *** 27     112  p     97   a



Failed!  - Failed:     1, Passed:     3, Skipped:     0, Total:     4, Duration: 55 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/Specs/GenericAttributesSpecs.md" lines="39-72">
The following shows that attributes can be attached to the next block if they are used inside a single line just preceding the block (and preceded by a blank line or beginning of a block container):

```````````````````````````````` example
{#fenced-id .fenced-class}
~~~
This is a fenced with attached attributes
~~~ 
.
<pre><code id="fenced-id" class="fenced-class">This is a fenced with attached attributes
</code></pre>
````````````````````````````````

Attribute values can be one character long

```````````````````````````````` example
[Foo](url){data-x=1}

[Foo](url){data-x='1'}

[Foo](url){data-x=11}
.
<p><a href="url" data-x="1">Foo</a></p>
<p><a href="url" data-x="1">Foo</a></p>
<p><a href="url" data-x="11">Foo</a></p>
````````````````````````````````

Attributes that occur immediately before a block element, on a line by themselves, affect that element

```````````````````````````````` example
{.center}
A paragraph
.
<p class="center">A paragraph</p>
````````````````````````````````
</test_snippet>

<production_snippet path="src/Markdig/Extensions/GenericAttributes/GenericAttributesParser.cs" lines="86-136">
    /// </summary>
    /// <param name="slice">The slice to parse.</param>
    /// <param name="attributes">The output attributes or null if not found or invalid</param>
    /// <returns><c>true</c> if parsing the HTML attributes was successful</returns>
    public static bool TryParse(ref StringSlice slice, [NotNullWhen(true)] out HtmlAttributes? attributes)
    {
        attributes = null;
        if (slice.PeekCharExtra(-1) == '{')
        {
            return false;
        }

        var line = slice;

        string? id = null;
        List<string>? classes = null;
        List<KeyValuePair<string, string?>>? properties = null;

        bool isValid = false;
        var c = line.NextChar();
        while (true)
        {
            if (c == '}')
            {
                isValid = true;
                line.SkipChar(); // skip }
                break;
            }

            if (c == '\0')
            {
                break;
            }

            bool isClass = c == '.';
            if (c == '#' || isClass)
            {
                c = line.NextChar(); // Skip #
                var start = line.Start;
                // Get all non-whitespace characters following a #
                // But stop if we found a } or \0
                while (c != '}' && !c.IsWhiteSpaceOrZero())
                {
                    c = line.NextChar();
                }
                var end = line.Start - 1;
                if (end == start)
                {
                    break;
                }
                var text = slice.Text.Substring(start, end - start + 1);
</production_snippet>
