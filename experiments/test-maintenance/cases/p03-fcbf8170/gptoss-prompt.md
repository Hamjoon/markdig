You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestCjkFriendlyEmphasis.cs, src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs b/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs
index b0f55b65..38178a9d 100644
--- a/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs
+++ b/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs
@@ -106,6 +106,21 @@ public void TestCjkFriendlyPseudoEmoji(string source, string expected)
             Assert.AreEqual(expected, actual);
         }
 
+        [Test]
+        [TestCase("**Start**", "<p><strong>Start</strong></p>\n")]
+        [TestCase("\n**Newline**", "<p><strong>Newline</strong></p>\n")]
+        [TestCase("&#10;**Entity**", "<p>\n<strong>Entity</strong></p>\n")]
+        [TestCase("**First**\n**Second**", "<p><strong>First</strong>\n<strong>Second</strong></p>\n")]
+        [TestCase("**First**&#10;**Second**", "<p><strong>First</strong>\n<strong>Second</strong></p>\n")]
+        [TestCase("&#13;**CarriageReturn**", "<p>\r<strong>CarriageReturn</strong></p>\n")]
+        [TestCase("𠮷**SurrogatePair**", "<p>𠮷<strong>SurrogatePair</strong></p>\n")]
+        public void TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(string source, string expected)
+        {
+            var pipeline = GetPipeline();
+            var actual = Markdown.ToHtml(source, pipeline);
+            Assert.AreEqual(expected, actual);
+        }
+
 #if !NET || !MARKDIG_NO_RUNE_TESTS
         // delimiter: '*', '_' = each character, '?' = either
         // can open/close = whether the places can be in the range of emphasis
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Failed TestCjkFriendlyEmphasisAfterLineBreaksAndEntities("&#10;**Entity**","<p>\n<strong>Entity</strong></p>\n") [4 ms]
  Error Message:
   System.IndexOutOfRangeException : Index was outside the bounds of the array.
  Stack Trace:
     at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)
1)    at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)

  Failed TestCjkFriendlyEmphasisAfterLineBreaksAndEntities("**First**&#10;**Second**","<p><strong>First</strong>\n<strong>Second</strong></p>\n") [< 1 ms]
  Error Message:
   System.IndexOutOfRangeException : Index was outside the bounds of the array.
  Stack Trace:
     at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)
1)    at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)

  Failed TestCjkFriendlyEmphasisAfterLineBreaksAndEntities("&#13;**CarriageReturn**","<p>\r<strong>CarriageReturn</strong></p>\n") [< 1 ms]
  Error Message:
   System.IndexOutOfRangeException : Index was outside the bounds of the array.
  Stack Trace:
     at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)
1)    at Markdig.Helpers.StringSlice.RuneAt(Int32 index) in <worktree>/src/Markdig/Helpers/StringSlice.cs:line 194
   at Markdig.Parsers.Inlines.EmphasisInlineParser.Match(InlineProcessor processor, StringSlice& slice) in <worktree>/src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs:line 180
   at Markdig.Parsers.InlineProcessor.ProcessInlineLeaf(LeafBlock leafBlock) in <worktree>/src/Markdig/Parsers/InlineProcessor.cs:line 285
   at Markdig.Parsers.MarkdownParser.ProcessInlines(InlineProcessor inlineProcessor, MarkdownDocument document) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 176
   at Markdig.Parsers.MarkdownParser.Parse(String text, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Parsers/MarkdownParser.cs:line 76
   at Markdig.Markdown.ToHtml(String markdown, MarkdownPipeline pipeline, MarkdownParserContext context) in <worktree>/src/Markdig/Markdown.cs:line 104
   at Markdig.Tests.TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(String source, String expected) in <worktree>/src/Markdig.Tests/TestCjkFriendlyEmphasis.cs:line 120
   at InvokeStub_TestCjkFriendlyEmphasis.TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(Object, Span`1)
   at System.Reflection.MethodBaseInvoker.InvokeWithFewArgs(Object obj, BindingFlags invokeAttr, Binder binder, Object[] parameters, CultureInfo culture)


Failed!  - Failed:     3, Passed:   104, Skipped:     0, Total:   107, Duration: 41 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestCjkFriendlyEmphasis.cs" lines="84-148">
        [TestCase("「~~a」~~a", "<p>「<del>a」</del>a</p>\n")]
        [TestCase("~~a~~：~~a~~", "<p><del>a</del>：<del>a</del></p>\n")]
        [TestCase("~~日本語。︀~~English.", "<p><del>日本語。︀</del>English.</p>\n")]
        [TestCase("~~“︁a”︁~~a", "<p><del>“︁a”︁</del>a</p>\n")]
        public void TestCjkFriendlyEmphasisGfmStrikethrough(string source, string expected)
        {
            var pipeline = GetPipelineWithStrikethrough();
            var actual = Markdown.ToHtml(source, pipeline);
            Assert.AreEqual(expected, actual);
        }

        [Test]
        [TestCase("a**〰**a", "<p>a<strong>〰</strong>a</p>\n")]
        [TestCase("a**〽**a", "<p>a<strong>〽</strong>a</p>\n")]
        [TestCase("a**🈂**a", "<p>a<strong>🈂</strong>a</p>\n")]
        [TestCase("a**🈷**a", "<p>a<strong>🈷</strong>a</p>\n")]
        [TestCase("a**㊗**a", "<p>a<strong>㊗</strong>a</p>\n")]
        [TestCase("a**㊙**a", "<p>a<strong>㊙</strong>a</p>\n")]
        public void TestCjkFriendlyPseudoEmoji(string source, string expected)
        {
            var pipeline = GetPipeline();
            var actual = Markdown.ToHtml(source, pipeline);
            Assert.AreEqual(expected, actual);
        }

        [Test]
        [TestCase("**Start**", "<p><strong>Start</strong></p>\n")]
        [TestCase("\n**Newline**", "<p><strong>Newline</strong></p>\n")]
        [TestCase("&#10;**Entity**", "<p>\n<strong>Entity</strong></p>\n")]
        [TestCase("**First**\n**Second**", "<p><strong>First</strong>\n<strong>Second</strong></p>\n")]
        [TestCase("**First**&#10;**Second**", "<p><strong>First</strong>\n<strong>Second</strong></p>\n")]
        [TestCase("&#13;**CarriageReturn**", "<p>\r<strong>CarriageReturn</strong></p>\n")]
        [TestCase("𠮷**SurrogatePair**", "<p>𠮷<strong>SurrogatePair</strong></p>\n")]
        public void TestCjkFriendlyEmphasisAfterLineBreaksAndEntities(string source, string expected)
        {
            var pipeline = GetPipeline();
            var actual = Markdown.ToHtml(source, pipeline);
            Assert.AreEqual(expected, actual);
        }

#if !NET || !MARKDIG_NO_RUNE_TESTS
        // delimiter: '*', '_' = each character, '?' = either
        // can open/close = whether the places can be in the range of emphasis
        // 2 before, previous, can close, delimiter, can open, next
        // *****Basic*****
        [TestCase("\0", " ", false, '?', false, " ")]
        [TestCase("\0", "𰻞", true, '?', false, " ")]
        [TestCase("\0", " ", false, '?', true, "𰻞")]
        [TestCase("\0", "𝜵", false, '?', true, "A")]
        [TestCase("\0", "A", true, '?', false, "𝜵")]
        [TestCase("\0", "𝜵", true, '*', true, "𰻞")]
        [TestCase("\0", "A", true, '*', true, "𰻞")]
        [TestCase("\0", "𰻞", true, '*', true, "𝜵")]
        [TestCase("\0", "𰻞", true, '*', true, "A")]
        [TestCase("\0", "𰻞", true, '*', true, "」")]
        [TestCase("\0", "「", true, '*', true, "𰻞")]
        [TestCase("\0", "A", true, '*', true, "」")]
        [TestCase("\0", "「", true, '*', true, "A")]
        [TestCase("\0", "𝜵", false, '_', true, "𰻞")]
        [TestCase("\0", "A", false, '_', false, "𰻞")]
        [TestCase("\0", "𰻞", true, '_', false, "𝜵")]
        [TestCase("\0", "𰻞", false, '_', false, "A")]
        [TestCase("\0", "𰻞", true, '_', false, "」")]
        [TestCase("\0", "「", false, '_', true, "𰻞")]
        [TestCase("\0", "A", true, '_', false, "」")]
</test_snippet>

<production_snippet path="src/Markdig/Parsers/Inlines/EmphasisInlineParser.cs" lines="151-205">
            ProcessEmphasis(state, delimiters);
            inlinesCache.Release(delimiters);
        }
        return true;
    }

    /// <summary>
    /// Attempts to match the parser at the current position.
    /// </summary>
    public override bool Match(InlineProcessor processor, ref StringSlice slice)
    {
        // First, some definitions.
        // A delimiter run is a sequence of one or more delimiter characters that is not preceded or followed by the same delimiter character
        // The amount of delimiter characters in the delimiter run may exceed emphasisDesc.MaximumCount, as that is handeled in `ProcessEmphasis`

        var delimiterChar = slice.CurrentChar;
        var emphasisDesc = emphasisMap![delimiterChar]!;

        Rune pc = (Rune)0;
        Rune twoPreviousChar = default;

        if (processor.Inline is HtmlEntityInline htmlEntityInline)
        {
            if (htmlEntityInline.Transcoded.Length > 0)
            {
                pc = htmlEntityInline.Transcoded.RuneAt(htmlEntityInline.Transcoded.End);

                if (CjkFriendlyEmphasis)
                {
                    twoPreviousChar = htmlEntityInline.Transcoded.RuneAt(htmlEntityInline.Transcoded.End - pc.Utf16SequenceLength);
                }
            }
        }
        if (pc.Value == 0)
        {
            pc = slice.PeekRuneExtra(-1);
            if (CjkFriendlyEmphasis)
            {
                // This cannot be a delegate (Func<Rune>?) because slice is a reference
                twoPreviousChar = slice.PeekRuneExtra(-1 - pc.Utf16SequenceLength);
            }
            // delimiterChar is BMP, so slice.PeekCharExtra(-2) is (a part of) the character two positions back.
            if (pc == (Rune)delimiterChar && slice.PeekCharExtra(-2) != '\\')
            {
                // If we get here, we determined that either:
                // a) there weren't enough delimiters in the delimiter run to satisfy the MinimumCount condition
                // b) the previous character couldn't open/close
                return false;
            }
        }
        var startPosition = slice.Start;

        int delimiterCount = slice.CountAndSkipChar(delimiterChar);

        // If the emphasis doesn't have the minimum required character
</production_snippet>
