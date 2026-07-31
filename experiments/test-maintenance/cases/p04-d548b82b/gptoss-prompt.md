You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestPipeTable.cs, src/Markdig/Extensions/Tables/PipeTableParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/TestPipeTable.cs b/src/Markdig.Tests/TestPipeTable.cs
index b891c722..f6f60a13 100644
--- a/src/Markdig.Tests/TestPipeTable.cs
+++ b/src/Markdig.Tests/TestPipeTable.cs
@@ -10,6 +10,8 @@ public sealed class TestPipeTable
     [TestCase("| S | T |\r\n|---|---|\t\r\n| G | H |")]
     [TestCase("| S | T |\r\n|---|---|\f\r\n| G | H |")]
     [TestCase("| S | \r\n|---|\r\n| G |\r\n\r\n| D | D |\r\n| ---| ---| \r\n| V | V |", 2)]
+    [TestCase("a\r| S | T |\r|---|---|")]
+    [TestCase("a\n| S | T |\r|---|---|")]
     public void TestTableBug(string markdown, int tableCount = 1)
     {
         MarkdownDocument document =
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed TestTableBug("a\r| S | T |\r|---|---|") [11 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected: 1
  But was:  0

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 22
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 22
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)


  Failed TestTableBug("a\n| S | T |\r|---|---|") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected: 1
  But was:  0

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 22
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 22
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)



Failed!  - Failed:     2, Passed:    13, Skipped:     0, Total:    15, Duration: 40 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestPipeTable.cs" lines="1-39">
using Markdig.Extensions.Tables;
using Markdig.Syntax;

namespace Markdig.Tests;

[TestFixture]
public sealed class TestPipeTable
{
    [TestCase("| S | T |\r\n|---|---| \r\n| G | H |")]
    [TestCase("| S | T |\r\n|---|---|\t\r\n| G | H |")]
    [TestCase("| S | T |\r\n|---|---|\f\r\n| G | H |")]
    [TestCase("| S | \r\n|---|\r\n| G |\r\n\r\n| D | D |\r\n| ---| ---| \r\n| V | V |", 2)]
    [TestCase("a\r| S | T |\r|---|---|")]
    [TestCase("a\n| S | T |\r|---|---|")]
    public void TestTableBug(string markdown, int tableCount = 1)
    {
        MarkdownDocument document =
            Markdown.Parse(markdown, new MarkdownPipelineBuilder().UseAdvancedExtensions().Build());

        Table[] tables = document.Descendants().OfType<Table>().ToArray();

        Assert.AreEqual(tableCount, tables.Length);
    }

    [TestCase("A | B\r\n---|---", new[] {50.0f, 50.0f})]
    [TestCase("A | B\r\n-|---", new[] {25.0f, 75.0f})]
    [TestCase("A | B\r\n-|---\r\nA | B\r\n---|---", new[] {25.0f, 75.0f})]
    [TestCase("A | B\r\n---|---|---", new[] {33.33f, 33.33f, 33.33f})]
    [TestCase("A | B\r\n---|---|---|", new[] {33.33f, 33.33f, 33.33f})]
    public void TestColumnWidthByHeaderLines(string markdown, float[] expectedWidth)
    {
        var pipeline = new MarkdownPipelineBuilder()
            .UsePipeTables(new PipeTableOptions() {InferColumnWidthsFromSeparator = true})
            .Build();
        var document = Markdown.Parse(markdown, pipeline);
        var table = document.Descendants().OfType<Table>().FirstOrDefault();
        Assert.IsNotNull(table);
        var actualWidths = table.ColumnDefinitions.Select(x => x.Width).ToList();
        Assert.AreEqual(actualWidths.Count, expectedWidth.Length);
</test_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="25-99">
    /// <summary>
    /// Initializes a new instance of the <see cref="PipeTableParser" /> class.
    /// </summary>
    /// <param name="lineBreakParser">The line break parser to use</param>
    /// <param name="options">The options.</param>
    public PipeTableParser(LineBreakInlineParser lineBreakParser, PipeTableOptions? options = null)
    {
        this.lineBreakParser = lineBreakParser ?? throw new ArgumentNullException(nameof(lineBreakParser));
        OpeningCharacters = ['|', '\n', '\r'];
        Options = options ?? new PipeTableOptions();
    }

    /// <summary>
    /// Gets the options.
    /// </summary>
    public PipeTableOptions Options { get; }

    public override bool Match(InlineProcessor processor, ref StringSlice slice)
    {
        // Only working on Paragraph block
        if (!processor.Block!.IsParagraphBlock)
        {
            return false;
        }

        var c = slice.CurrentChar;

        // If we have not a delimiter on the first line of a paragraph, don't bother to continue
        // tracking other delimiters on following lines
        var tableState = processor.ParserStates[Index] as TableState;
        bool isFirstLineEmpty = false;


        var position = processor.GetSourcePosition(slice.Start, out int globalLineIndex, out int column);
        var localLineIndex = globalLineIndex - processor.LineIndex;

        if (tableState is null)
        {

            // A table could be preceded by an empty line or a line containing an inline
            // that has not been added to the stack, so we consider this as a valid
            // start for a table. Typically, with this, we can have an attributes {...}
            // starting on the first line of a pipe table, even if the first line
            // doesn't have a pipe
            if (processor.Inline != null && (localLineIndex > 0 || c == '\n' || c == '\r'))
            {
                return false;
            }

            if (processor.Inline is null)
            {
                isFirstLineEmpty = true;
            }
            // Else setup a table processor
            tableState = new TableState();
            processor.ParserStates[Index] = tableState;
        }

        if (c == '\n' || c == '\r')
        {
            if (!isFirstLineEmpty && !tableState.LineHasPipe)
            {
                tableState.IsInvalidTable = true;
            }
            tableState.LineHasPipe = false;
            lineBreakParser.Match(processor, ref slice);
            tableState.LineIndex++;
            if (!isFirstLineEmpty)
            {
                tableState.ColumnAndLineDelimiters.Add(processor.Inline!);
                tableState.EndOfLines.Add(processor.Inline!);
            }
        }
        else
        {
</production_snippet>
