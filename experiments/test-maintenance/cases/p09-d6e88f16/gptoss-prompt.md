You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestPipeTable.cs, src/Markdig.Tests/Specs/GridTableSpecs.md, src/Markdig.Tests/Specs/PipeTableSpecs.md, src/Markdig/Extensions/Tables/PipeTableParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/Specs/GridTableSpecs.md b/src/Markdig.Tests/Specs/GridTableSpecs.md
index de4618cf..ed68767e 100644
--- a/src/Markdig.Tests/Specs/GridTableSpecs.md
+++ b/src/Markdig.Tests/Specs/GridTableSpecs.md
@@ -285,3 +285,24 @@ An empty `+` on a line should result in a simple empty list output:
 <li></li>
 </ul>
 ````````````````````````````````
+
+A table may begin right after a paragraph without an empty line in between:
+
+```````````````````````````````` example
+Some
+**text**.
++---+
+| A |
++---+
+.
+<p>Some
+<strong>text</strong>.</p>
+<table>
+<col style="width:100%" />
+<tbody>
+<tr>
+<td>A</td>
+</tr>
+</tbody>
+</table>
+````````````````````````````````
\ No newline at end of file
diff --git a/src/Markdig.Tests/Specs/PipeTableSpecs.md b/src/Markdig.Tests/Specs/PipeTableSpecs.md
index c96811c3..8ea5fe99 100644
--- a/src/Markdig.Tests/Specs/PipeTableSpecs.md
+++ b/src/Markdig.Tests/Specs/PipeTableSpecs.md
@@ -612,4 +612,29 @@ a | b
 </tr>
 </tbody>
 </table>
+````````````````````````````````
+
+A table may begin right after a paragraph without an empty line in between:
+
+```````````````````````````````` example
+Some
+**text**.
+| A |
+|---|
+| B |
+.
+<p>Some
+<strong>text</strong>.</p>
+<table>
+<thead>
+<tr>
+<th>A</th>
+</tr>
+</thead>
+<tbody>
+<tr>
+<td>B</td>
+</tr>
+</tbody>
+</table>
 ````````````````````````````````
\ No newline at end of file
diff --git a/src/Markdig.Tests/TestPipeTable.cs b/src/Markdig.Tests/TestPipeTable.cs
index 06bf3849..6486329e 100644
--- a/src/Markdig.Tests/TestPipeTable.cs
+++ b/src/Markdig.Tests/TestPipeTable.cs
@@ -14,6 +14,7 @@ public sealed class TestPipeTable
     [TestCase("| S | \r\n|---|\r\n| G |\r\n\r\n| D | D |\r\n| ---| ---| \r\n| V | V |", 2)]
     [TestCase("a\r| S | T |\r|---|---|")]
     [TestCase("a\n| S | T |\r|---|---|")]
+    [TestCase("a\r\n| S | T |\r|---|---|")]
     public void TestTableBug(string markdown, int tableCount = 1)
     {
         MarkdownDocument document =
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net9.0/Markdig.Tests.dll (.NETCoreApp,Version=v9.0)
A total of 1 test files matched the specified pattern.
  Failed ExtensionsPipeTable_Example026 [17 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 129 but was 52. Strings differ at index 30.
  Expected: "<p>Some\n<strong>text</strong>.</p>\n<table>\n<thead>\n<tr>\n<th>A..."
  But was:  "<p>Some\n<strong>text</strong>.\n| A |\n|---|\n| B |</p>"
  ------------------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.Specs.PipeTables.TestExtensionsPipeTable.ExtensionsPipeTable_Example026() in <worktree>/src/Markdig.Tests/Specs/PipeTableSpecs.generated.cs:line 859

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestParser.PrintAssertExpected(String source, String result, String expected, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 117
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, MarkdownPipeline pipeline, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 98
   at Markdig.Tests.TestParser.TestSpec(String inputText, String expectedOutputText, String extensions, Boolean plainText, String context) in <worktree>/src/Markdig.Tests/TestParser.cs:line 85
   at Markdig.Tests.Specs.PipeTables.TestExtensionsPipeTable.ExtensionsPipeTable_Example026() in <worktree>/src/Markdig.Tests/Specs/PipeTableSpecs.generated.cs:line 859


  Standard Output Messages:
 Example 26
 Section Extensions / Pipe Table

 Pipeline configured with extensions: pipetables
 ```````````````````Source
 Some
 **text**.
 |·A·|
 |---|
 |·B·|
 ```````````````````Result
 <p>Some
 <strong>text</strong>.
 |·A·|
 |---|
 |·B·|</p>
 ```````````````````Expected
 <p>Some
 <strong>text</strong>.</p>
 <table>
 <thead>
 <tr>
 <th>A</th>
 </tr>
 </thead>
 <tbody>
 <tr>
 <td>B</td>
 </tr>
 </tbody>
 </table>
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 30     60   <     10   \n
 *** 31     47   /     124  |
 *** 32     112  p     32   \u20;
 *** 33     62   >     65   A
 *** 34     10   \n    32   \u20;
 *** 35     60   <     124  |
 *** 36     116  t     10   \n
 *** 37     97   a     124  |
 *** 38     98   b     45   -
 *** 39     108  l     45   -


  Failed TestTableBug("a\r\n| S | T |\r|---|---|") [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected: 1
  But was:  0

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 25
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TestPipeTable.TestTableBug(String markdown, Int32 tableCount) in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 25
   at InvokeStub_TestPipeTable.TestTableBug(Object, Span`1)



Failed!  - Failed:     2, Passed:    58, Skipped:     0, Total:    60, Duration: 83 ms - Markdig.Tests.dll (net9.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestPipeTable.cs" lines="1-42">
using Markdig;
using Markdig.Extensions.Tables;
using Markdig.Syntax;
using Markdig.Syntax.Inlines;

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
    [TestCase("a\r\n| S | T |\r|---|---|")]
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

<test_snippet path="src/Markdig.Tests/Specs/GridTableSpecs.md" lines="263-308">
| AAAAA | B |
+ A +---+ B +
| A | C | B |
+---+---+---+
| DDDDD | E |
+---+---+---+
.
<p>+---+---+---+
| AAAAA | B |
+ A +---+ B +
| A | C | B |
+---+---+---+
| DDDDD | E |
+---+---+---+</p>
````````````````````````````````

An empty `+` on a line should result in a simple empty list output:

```````````````````````````````` example
+
.
<ul>
<li></li>
</ul>
````````````````````````````````

A table may begin right after a paragraph without an empty line in between:

```````````````````````````````` example
Some
**text**.
+---+
| A |
+---+
.
<p>Some
<strong>text</strong>.</p>
<table>
<col style="width:100%" />
<tbody>
<tr>
<td>A</td>
</tr>
</tbody>
</table>
````````````````````````````````
</test_snippet>

<test_snippet path="src/Markdig.Tests/Specs/PipeTableSpecs.md" lines="590-640">

The tables are normalized to the maximum number of columns found in a table


```````````````````````````````` example
a | b
-- | - 
0 | 1 | 2
.
<table>
<thead>
<tr>
<th>a</th>
<th>b</th>
<th></th>
</tr>
</thead>
<tbody>
<tr>
<td>0</td>
<td>1</td>
<td>2</td>
</tr>
</tbody>
</table>
````````````````````````````````

A table may begin right after a paragraph without an empty line in between:

```````````````````````````````` example
Some
**text**.
| A |
|---|
| B |
.
<p>Some
<strong>text</strong>.</p>
<table>
<thead>
<tr>
<th>A</th>
</tr>
</thead>
<tbody>
<tr>
<td>B</td>
</tr>
</tbody>
</table>
````````````````````````````````
</test_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="1-138">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license.
// See the license.txt file in the project root for more information.

using System.Diagnostics;

using Markdig.Helpers;
using Markdig.Parsers;
using Markdig.Parsers.Inlines;
using Markdig.Renderers.Html;
using Markdig.Syntax;
using Markdig.Syntax.Inlines;

namespace Markdig.Extensions.Tables;

/// <summary>
/// The inline parser used to transform a <see cref="ParagraphBlock"/> into a <see cref="Table"/> at inline parsing time.
/// </summary>
/// <seealso cref="InlineParser" />
/// <seealso cref="IPostInlineProcessor" />
public class PipeTableParser : InlineParser, IPostInlineProcessor
{
    private readonly LineBreakInlineParser lineBreakParser;

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
        var isNewLineFollowedByPipe = (c == '\n' || c == '\r') && slice.PeekChar() == '|';

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
            if (processor.Inline != null && (localLineIndex > 0 || c == '\n' || c == '\r') && !isNewLineFollowedByPipe)
            {
                return false;
            }

            if (processor.Inline is null || isNewLineFollowedByPipe)
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
            processor.Inline = new PipeTableDelimiterInline(this)
            {
                Span = new SourceSpan(position, position),
                Line = globalLineIndex,
                Column = column,
                LocalLineIndex = localLineIndex
            };
            var deltaLine = localLineIndex - tableState.LineIndex;
            if (deltaLine > 0)
            {
                tableState.IsInvalidTable = true;
            }
            tableState.LineHasPipe = true;
            tableState.LineIndex = localLineIndex;
            slice.SkipChar(); // Skip the `|` character

            tableState.ColumnAndLineDelimiters.Add(processor.Inline);
        }

        return true;
    }

    public bool PostProcess(InlineProcessor state, Inline? root, Inline? lastChild, int postInlineProcessorIndex, bool isFinalProcessing)
    {
        var container = root as ContainerInline;
        var tableState = state.ParserStates[Index] as TableState;

        // If the delimiters are being processed by an image link, we need to transform them back to literals
        if (!isFinalProcessing)
        {
            if (container is null || tableState is null)
            {
                return true;
            }

            var child = container.LastChild;
            List<PipeTableDelimiterInline>? delimitersToRemove = null;

            while (child != null)
</production_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="206-256">
                    }
                }
            }
            return true;
        }

        // Detect the header row
        var delimiters = tableState.ColumnAndLineDelimiters;
        // TODO: we could optimize this by merging FindHeaderRow and the cell loop
        var aligns = FindHeaderRow(delimiters);

        if (Options.RequireHeaderSeparator && aligns is null)
        {
            return true;
        }

        var table = new Table();

        // If the current paragraph block has any attributes attached, we can copy them
        var attributes = state.Block!.TryGetAttributes();
        if (attributes != null)
        {
            attributes.CopyTo(table.GetAttributes());
        }

        state.BlockNew = table;
        var cells = tableState.Cells;
        cells.Clear();

        //delimiters[0].DumpTo(state.DebugLog);

        // delimiters contain a list of `|` and `\n` delimiters
        // The `|` delimiters are created as child containers.
        // So the following:
        // | a | b \n
        // | d | e \n
        //
        // Will generate a tree of the following node:
        // |
        //   a
        //   |
        //     b
        //     \n
        //     |
        //       d
        //       |
        //         e
        //         \n
        // When parsing delimiters, we need to recover whether a row is of the following form:
        // 0)  | a | b | \n
        // 1)  | a | b \n
</production_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="464-494">

        // Perform delimiter processor that are coming after this processor
        foreach (var cell in cells)
        {
            var paragraph = (ParagraphBlock) cell[0];
            state.PostProcessInlines(postInlineProcessorIndex + 1, paragraph.Inline, null, true);
            if (paragraph.Inline?.LastChild is not null)
            {
                paragraph.Inline.Span.End = paragraph.Inline.LastChild.Span.End;
                paragraph.UpdateSpanEnd(paragraph.Inline.LastChild.Span.End);
            }
        }

        // Clear cells when we are done
        cells.Clear();

        // Normalize the table
        if (Options.UseHeaderForColumnCount)
        {
            table.NormalizeUsingHeaderRow();
        }
        else
        {
            table.NormalizeUsingMaxWidth();
        }

        // We don't want to continue procesing delimiters, as we are already processing them here
        return false;
    }

    private static bool ParseHeaderString(Inline? inline, out TableColumnAlign? align, out int delimiterCount)
</production_snippet>
