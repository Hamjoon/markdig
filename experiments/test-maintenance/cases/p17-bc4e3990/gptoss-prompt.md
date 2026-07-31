You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/MiscTests.cs, src/Markdig/Parsers/BlockProcessor.cs, src/Markdig/Parsers/ListBlockParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/MiscTests.cs b/src/Markdig.Tests/MiscTests.cs
index 3fa4d502..66460068 100644
--- a/src/Markdig.Tests/MiscTests.cs
+++ b/src/Markdig.Tests/MiscTests.cs
@@ -481,6 +481,61 @@ public void TestAlertInsideNestedListItem()
         TestParser.TestSpec(input, expected, new MarkdownPipelineBuilder().UseAlertBlocks(allowNestedAlerts: true).Build());
     }
 
+    [Test]
+    public void TestIssue887ListAfterNestedBlockQuote()
+    {
+        var input = @"> >* _Unordered 1_ QL2 level 1 no space sep
+> >  Continued 1
+> > * Unordered 2 level 1
+> > 1. **Ordered 1** QL2 level 1
+> >    Continued 1
+> > > Not continued QL3
+> > 2. Ordered 2 QL2 level 1
+> > Continued 2a
+> >
+> >    Continued 2b
+> >
+> >    Continued 2c
+> >
+> >    3. Ordered 3 QL2 level 2
+> >       Continued 3a
+> >
+> >       Continued 3b
+";
+
+        var expected = @"<blockquote>
+<blockquote>
+<ul>
+<li><em>Unordered 1</em> QL2 level 1 no space sep
+Continued 1</li>
+<li>Unordered 2 level 1</li>
+</ul>
+<ol>
+<li><strong>Ordered 1</strong> QL2 level 1
+Continued 1</li>
+</ol>
+<blockquote>
+<p>Not continued QL3</p>
+</blockquote>
+<ol start=""2"">
+<li><p>Ordered 2 QL2 level 1
+Continued 2a</p>
+<p>Continued 2b</p>
+<p>Continued 2c</p>
+<ol start=""3"">
+<li><p>Ordered 3 QL2 level 2
+Continued 3a</p>
+<p>Continued 3b</p>
+</li>
+</ol>
+</li>
+</ol>
+</blockquote>
+</blockquote>";
+
+        TestParser.TestSpec(input, expected);
+    }
+
     [Test]
     public void TestIssue845ListItemBlankLine()
     {
</recent_change_diff>

Current test results:
<test_output>
[... truncated, last 120 lines ...]
  Failed TestIssue887ListAfterNestedBlockQuote [10 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 487 but was 453. Strings differ at index 237.
  Expected: "...ckquote>\n<p>Not continued QL3</p>\n</blockquote>\n<ol start=..."
  But was:  "...ckquote>\n<p>Not continued QL3\n2. Ordered 2 QL2 level 1\nCon..."
  --------------------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.MiscTests.TestIssue887ListAfterNestedBlockQuote() in <worktree>/src/Markdig.Tests/MiscTests.cs:line 487

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.MiscTests.TestIssue887ListAfterNestedBlockQuote() in <worktree>/src/Markdig.Tests/MiscTests.cs:line 487


  Standard Output Messages:
 Pipeline configured with extensions: default
 ```````````````````Source
 >·>*·_Unordered·1_·QL2·level·1·no·space·sep
 >·>··Continued·1
 >·>·*·Unordered·2·level·1
 >·>·1.·**Ordered·1**·QL2·level·1
 >·>····Continued·1
 >·>·>·Not·continued·QL3
 >·>·2.·Ordered·2·QL2·level·1
 >·>·Continued·2a
 >·>
 >·>····Continued·2b
 >·>
 >·>····Continued·2c
 >·>
 >·>····3.·Ordered·3·QL2·level·2
 >·>·······Continued·3a
 >·>
 >·>·······Continued·3b

 ```````````````````Result
 <blockquote>
 <blockquote>
 <ul>
 <li><em>Unordered·1</em>·QL2·level·1·no·space·sep
 Continued·1</li>
 <li>Unordered·2·level·1</li>
 </ul>
 <ol>
 <li><strong>Ordered·1</strong>·QL2·level·1
 Continued·1</li>
 </ol>
 <blockquote>
 <p>Not·continued·QL3
 2.·Ordered·2·QL2·level·1
 Continued·2a</p>
 </blockquote>
 <p>Continued·2b</p>
 <p>Continued·2c</p>
 <ol·start="3">
 <li><p>Ordered·3·QL2·level·2
 Continued·3a</p>
 <p>Continued·3b</p></li>
 </ol>
 </blockquote>
 </blockquote>
 ```````````````````Expected
 <blockquote>
 <blockquote>
 <ul>
 <li><em>Unordered·1</em>·QL2·level·1·no·space·sep
 Continued·1</li>
 <li>Unordered·2·level·1</li>
 </ul>
 <ol>
 <li><strong>Ordered·1</strong>·QL2·level·1
 Continued·1</li>
 </ol>
 <blockquote>
 <p>Not·continued·QL3</p>
 </blockquote>
 <ol·start="2">
 <li><p>Ordered·2·QL2·level·1
 Continued·2a</p>
 <p>Continued·2b</p>
 <p>Continued·2c</p>
 <ol·start="3">
 <li><p>Ordered·3·QL2·level·2
 Continued·3a</p>
 <p>Continued·3b</p></li>
 </ol></li>
 </ol>
 </blockquote>
 </blockquote>
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 237    60   <     10   \n
 *** 238    47   /     50   2
 *** 239    112  p     46   .
 *** 240    62   >     32   \u20;
 *** 241    10   \n    79   O
 *** 242    60   <     114  r
 *** 243    47   /     100  d
 *** 244    98   b     101  e
 *** 245    108  l     114  r
 *** 246    111  o     101  e



Failed!  - Failed:     1, Passed:    50, Skipped:     0, Total:    51, Duration: 299 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/MiscTests.cs" lines="459-560">
    {
        // Alert inside a nested list item (list item indented under another list item) requires AllowNestedAlerts
        var input = @"- list item 1
- list item 2
  - > [!NOTE]
    > A note inside a nested list item
";

        var expected = @"<ul>
<li>list item 1</li>
<li>list item 2
<ul>
<li>
<div class=""markdown-alert markdown-alert-note"">
<p class=""markdown-alert-title""><svg viewBox=""0 0 16 16"" version=""1.1"" width=""16"" height=""16"" aria-hidden=""true""><path d=""M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z""></path></svg>Note</p>
<p>A note inside a nested list item</p>
</div>
</li>
</ul>
</li>
</ul>
";
        TestParser.TestSpec(input, expected, new MarkdownPipelineBuilder().UseAlertBlocks(allowNestedAlerts: true).Build());
    }

    [Test]
    public void TestIssue887ListAfterNestedBlockQuote()
    {
        var input = @"> >* _Unordered 1_ QL2 level 1 no space sep
> >  Continued 1
> > * Unordered 2 level 1
> > 1. **Ordered 1** QL2 level 1
> >    Continued 1
> > > Not continued QL3
> > 2. Ordered 2 QL2 level 1
> > Continued 2a
> >
> >    Continued 2b
> >
> >    Continued 2c
> >
> >    3. Ordered 3 QL2 level 2
> >       Continued 3a
> >
> >       Continued 3b
";

        var expected = @"<blockquote>
<blockquote>
<ul>
<li><em>Unordered 1</em> QL2 level 1 no space sep
Continued 1</li>
<li>Unordered 2 level 1</li>
</ul>
<ol>
<li><strong>Ordered 1</strong> QL2 level 1
Continued 1</li>
</ol>
<blockquote>
<p>Not continued QL3</p>
</blockquote>
<ol start=""2"">
<li><p>Ordered 2 QL2 level 1
Continued 2a</p>
<p>Continued 2b</p>
<p>Continued 2c</p>
<ol start=""3"">
<li><p>Ordered 3 QL2 level 2
Continued 3a</p>
<p>Continued 3b</p>
</li>
</ol>
</li>
</ol>
</blockquote>
</blockquote>";

        TestParser.TestSpec(input, expected);
    }

    [Test]
    public void TestIssue845ListItemBlankLine()
    {
        TestParser.TestSpec("-\n\n  foo",@"
<ul>
<li></li>
</ul>
<p>foo</p>");
        TestParser.TestSpec("-\n-\n\n  foo",@"
<ul>
<li></li>
<li></li>
</ul>
<p>foo</p>");
        TestParser.TestSpec("-\n\n-\n\n  foo",@"
<ul>
<li></li>
<li></li>
</ul>
<p>foo</p>");
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Parsers/BlockProcessor.cs" lines="129-179">

    /// <summary>
    /// Gets the current indent position (number of columns between the previous indent and the current position).
    /// </summary>
    public int Indent => Column - ColumnBeforeIndent;

    /// <summary>
    /// Gets a value indicating whether a code indentation is at the beginning of the line being processed.
    /// </summary>
    public bool IsCodeIndent => Indent >= 4;

    /// <summary>
    /// Gets the column position before the indent occurred.
    /// </summary>
    public int ColumnBeforeIndent { get; private set; }

    /// <summary>
    /// Gets the character position before the indent occurred.
    /// </summary>
    public int StartBeforeIndent { get; private set; }

    /// <summary>
    /// Gets a boolean indicating whether the current line being parsed is lazy continuation.
    /// </summary>
    public bool IsLazy { get; private set; }

    /// <summary>
    /// Gets the current stack of <see cref="Block"/> being processed.
    /// </summary>
    private List<BlockWrapper> OpenedBlocks { get; } = [];

    private bool ContinueProcessingLine { get; set; }

    /// <summary>
    /// Gets or sets the position of the first character trivia is encountered
    /// and not yet assigned to a syntax node.
    /// Trivia: only used when <see cref="TrackTrivia"/> is enabled, otherwise 0.
    /// </summary>
    public int TriviaStart { get; set; }

    /// <summary>
    /// Returns trivia that has not yet been assigned to any node and
    /// advances the position of trivia to the ending position.
    /// </summary>
    /// <param name="end">End position of the trivia</param>
    /// <returns></returns>
    public StringSlice UseTrivia(int end)
    {
        var stringSlice = new StringSlice(Line.Text, TriviaStart, end);
        TriviaStart = end + 1;
        return stringSlice;
</production_snippet>

<production_snippet path="src/Markdig/Parsers/BlockProcessor.cs" lines="666-750">

            if (block.IsContainerBlock)
            {
                var currentContainer = Unsafe.As<ContainerBlock>(block);
                CurrentContainer = currentContainer;
                LastBlock = currentContainer.LastChild;
                CurrentBlock = currentBlock;
                return;
            }
        }

        CurrentBlock = currentBlock;
        LastBlock = null;
    }

    /// <summary>
    /// Tries to continue matching existing opened <see cref="Block"/>.
    /// </summary>
    /// <exception cref="InvalidOperationException">
    /// A pending parser cannot add a new block when it is not the last pending block
    /// or
    /// The NewBlocks is not empty. This is happening if a LeafBlock is not the last to be pushed
    /// </exception>
    private void TryContinueBlocks()
    {
        IsLazy = false;

        // Set all blocks non opened.
        // They will be marked as open in the following loop
        for (int i = 1; i < OpenedBlocks.Count; i++)
        {
            OpenedBlocks[i].Block.IsOpen = false;
        }

        // Process any current block potentially opened
        for (int i = 1; i < OpenedBlocks.Count; i++)
        {
            var block = OpenedBlocks[i].Block;

            ParseIndent();

            // If we have a paragraph block, we want to try to match other blocks before trying the Paragraph
            if (block.IsParagraphBlock)
            {
                break;
            }

            // Else tries to match the Default with the current line
            var parser = block.Parser!;

            // If we have a discard, we can remove it from the current state
            UpdateLastBlockAndContainer(i);
            var result = parser.TryContinue(this, block);
            if (result == BlockState.Skip)
            {
                continue;
            }

            if (result == BlockState.None)
            {
                break;
            }

            RestartIndent();

            // In case the BlockParser has modified the BlockProcessor we are iterating on
            if (i >= OpenedBlocks.Count)
            {
                i = OpenedBlocks.Count - 1;
            }

            // If a parser is adding a block, it must be the last of the list
            if ((i + 1) < OpenedBlocks.Count && NewBlocks.Count > 0)
            {
                ThrowHelper.InvalidOperationException("A pending parser cannot add a new block when it is not the last pending block");
            }

            // If we have a leaf block
            if (block.IsLeafBlock && NewBlocks.Count == 0)
            {
                ContinueProcessingLine = false;
                if (!result.IsDiscard())
                {
                    if (TrackTrivia)
                    {
</production_snippet>

<production_snippet path="src/Markdig/Parsers/BlockProcessor.cs" lines="1026-1076">

    [MemberNotNull(nameof(Document), nameof(Parsers))]
    internal void Setup(MarkdownDocument document, BlockParserList parsers, MarkdownParserContext? context, bool trackTrivia)
    {
        if (document is null) ThrowHelper.ArgumentNullException(nameof(document));
        if (parsers is null) ThrowHelper.ArgumentNullException(nameof(parsers));

        Document = document;
        Parsers = parsers;
        Context = context;
        TrackTrivia = trackTrivia;
    }

    private void Reset()
    {
        Document = null!;
        Parsers = null!;
        Context = null;
        CurrentContainer = null;
        CurrentBlock = null;
        LastBlock = null;

        TrackTrivia = false;
        SkipFirstUnwindSpace = false;
        ContinueProcessingLine = false;
        IsLazy = false;

        currentStackIndex = 0;
        originalLineStart = 0;
        CurrentLineStartPosition = 0;
        ColumnBeforeIndent = 0;
        StartBeforeIndent = 0;
        LineIndex = 0;
        Column = 0;
        TriviaStart = 0;

        Line = StringSlice.Empty;

        NewBlocks.Clear();
        OpenedBlocks.Clear();
        LinesBefore = null;
    }

    /// <summary>
    /// Performs the create child operation.
    /// </summary>
    public BlockProcessor CreateChild() => Rent(Document, Parsers, Context, TrackTrivia);

    /// <summary>
    /// Performs the release child operation.
    /// </summary>
</production_snippet>

<production_snippet path="src/Markdig/Parsers/ListBlockParser.cs" lines="252-304">
            }

            // Parse the following indent
            state.RestartIndent();
            var columnBeforeIndent = state.Column;
            state.ParseIndent();

            // We expect at most 4 columns after
            // If we have more, we reset the position
            if (state.Indent > 4)
            {
                state.GoToColumn(columnBeforeIndent + 1);
            }

            // Number of spaces required for the following content to be part of this list item
            // If the list item starts with a blank line, the number of spaces
            // following the list marker doesn't change the required indentation
            columnWidth = (state.IsBlankLine ? columnBeforeIndent : state.Column) - initColumnBeforeIndent;
        }

        // Starts/continue the list unless:
        // - an empty list item follows a paragraph
        // - an ordered list is not starting by '1'
        block ??= state.LastBlock;
        if (block is not null && block.IsParagraphBlock)
        {
            if (state.IsBlankLine ||
                state.IsOpen(block) && listInfo.BulletType == '1' && listInfo.OrderedStart is not "1")
            {
                state.GoToColumn(initColumn);
                state.TriviaStart = savedTriviaStart; // restore changed TriviaStart state
                return BlockState.None;
            }
        }

        int.TryParse(listInfo.OrderedStart, out int order);
        var newListItem = new ListItemBlock(this)
        {
            Column = initColumn,
            ColumnWidth = columnWidth,
            Order = order,
            Span = new SourceSpan(sourcePosition, sourceEndPosition),
        };

        if (state.TrackTrivia)
        {
            newListItem.TriviaBefore = triviaBefore;
            newListItem.LinesBefore = state.TakeLinesBefore();
            newListItem.NewLine = state.Line.NewLine;
            newListItem.SourceBullet = listInfo.SourceBullet;
        }

        state.NewBlocks.Push(newListItem);
</production_snippet>
