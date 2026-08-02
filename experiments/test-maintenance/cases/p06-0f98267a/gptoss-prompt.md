You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestPipeTable.cs, src/Markdig/Extensions/Tables/PipeTableExtension.cs, src/Markdig/Extensions/Tables/PipeTableParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig.Tests/TestPipeTable.cs b/src/Markdig.Tests/TestPipeTable.cs
index 6486329e..c282740e 100644
--- a/src/Markdig.Tests/TestPipeTable.cs
+++ b/src/Markdig.Tests/TestPipeTable.cs
@@ -162,6 +162,35 @@ public void TableCellWithCodeInlineRendersCorrectly()
         Assert.That(html, Does.Contain("<td><code>Code block</code></td>"));
     }
 
+    [Test]
+    public void BoldTableCellWithUnmatchedSubscriptDelimiterDoesNotAddCells()
+    {
+        const string markdown =
+            """
+            | Component | Per query | Per 1,000 queries |
+            |-----------|-----------|-------------------|
+            | Embedding | ~$0.00001 | ~$0.01 |
+            | LLM | ~$0.0015 | ~$1.50 |
+            | **Total** | **~$0.0015** | **~$1.50** |
+            """;
+
+        var pipeline = new MarkdownPipelineBuilder()
+            .UseAdvancedExtensions()
+            .Build();
+
+        var document = Markdown.Parse(markdown, pipeline);
+        var table = document.Descendants().OfType<Table>().Single();
+        var rows = table.OfType<TableRow>().ToArray();
+
+        Assert.That(rows, Has.Length.EqualTo(4));
+        Assert.That(rows, Has.All.Count.EqualTo(3));
+
+        var html = Markdown.ToHtml(markdown, pipeline);
+
+        Assert.That(html, Does.Contain("<td><strong>~$0.0015</strong></td>"));
+        Assert.That(html, Does.Contain("<td><strong>~$1.50</strong></td>"));
+    }
+
     [Test]
     public void CodeInlineWithIndentedContentPreservesWhitespace()
     {
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Failed BoldTableCellWithUnmatchedSubscriptDelimiterDoesNotAddCells [35 ms]
  Error Message:
     Assert.That(rows, Has.All.Count.EqualTo(3))
  Expected: all items property Count equal to 3
  But was:  < < < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, <empty> >, < < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, <empty> >, < < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> > >, < < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> > > >
  First non-matching item at index [0]:  < < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, < <Markdig.Syntax.ParagraphBlock> >, <empty> >

  Stack Trace:
     at Markdig.Tests.TestPipeTable.BoldTableCellWithUnmatchedSubscriptDelimiterDoesNotAddCells() in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 186

1)    at Markdig.Tests.TestPipeTable.BoldTableCellWithUnmatchedSubscriptDelimiterDoesNotAddCells() in <worktree>/src/Markdig.Tests/TestPipeTable.cs:line 186



Failed!  - Failed:     1, Passed:    22, Skipped:     0, Total:    23, Duration: 56 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestPipeTable.cs" lines="140-218">

        Assert.That(html, Is.EqualTo("<p><code>|| hidden text ||</code></p>\n"));
    }

    [Test]
    public void TableCellWithCodeInlineRendersCorrectly()
    {
        const string markdown =
            """
            | Count | A | B | C | D | E |
            |-------|---|---|---|---|---|
            |     0 | B | C | D | E | F |
            |     1 | B | `Code block` | D | E | F |
            |     2 | B | C | D | E | F |
            """;

        var pipeline = new MarkdownPipelineBuilder()
            .UseAdvancedExtensions()
            .Build();

        var html = Markdown.ToHtml(markdown, pipeline);

        Assert.That(html, Does.Contain("<td><code>Code block</code></td>"));
    }

    [Test]
    public void BoldTableCellWithUnmatchedSubscriptDelimiterDoesNotAddCells()
    {
        const string markdown =
            """
            | Component | Per query | Per 1,000 queries |
            |-----------|-----------|-------------------|
            | Embedding | ~$0.00001 | ~$0.01 |
            | LLM | ~$0.0015 | ~$1.50 |
            | **Total** | **~$0.0015** | **~$1.50** |
            """;

        var pipeline = new MarkdownPipelineBuilder()
            .UseAdvancedExtensions()
            .Build();

        var document = Markdown.Parse(markdown, pipeline);
        var table = document.Descendants().OfType<Table>().Single();
        var rows = table.OfType<TableRow>().ToArray();

        Assert.That(rows, Has.Length.EqualTo(4));
        Assert.That(rows, Has.All.Count.EqualTo(3));

        var html = Markdown.ToHtml(markdown, pipeline);

        Assert.That(html, Does.Contain("<td><strong>~$0.0015</strong></td>"));
        Assert.That(html, Does.Contain("<td><strong>~$1.50</strong></td>"));
    }

    [Test]
    public void CodeInlineWithIndentedContentPreservesWhitespace()
    {
        const string markdown = "`\n   foo\n`";

        var pipeline = new MarkdownPipelineBuilder()
            .UseAdvancedExtensions()
            .Build();

        var document = Markdown.Parse(markdown, pipeline);
        var codeInline = document.Descendants().OfType<CodeInline>().Single();

        Assert.That(codeInline.Content, Is.EqualTo("foo"));
        Assert.That(Markdown.ToHtml(markdown, pipeline), Is.EqualTo("<p><code>foo</code></p>\n"));
    }

    [Test]
    public void TableWithIndentedPipeAfterCodeInlineParsesCorrectly()
    {
        var markdown =
            """
            `
            	|| hidden text ||
            `

</test_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableExtension.cs" lines="19-58">
    /// <param name="options">The options.</param>
    public PipeTableExtension(PipeTableOptions? options = null)
    {
        Options = options ?? new PipeTableOptions();
    }

    /// <summary>
    /// Gets the options.
    /// </summary>
    public PipeTableOptions Options { get; }

    /// <summary>
    /// Configures this extension for the specified pipeline stage.
    /// </summary>
    public void Setup(MarkdownPipelineBuilder pipeline)
    {
        // Pipe tables require precise source location
        pipeline.PreciseSourceLocation = true;
        if (!pipeline.BlockParsers.Contains<PipeTableBlockParser>())
        {
            pipeline.BlockParsers.Insert(0, new PipeTableBlockParser());
        }
        var lineBreakParser = pipeline.InlineParsers.FindExact<LineBreakInlineParser>();
        if (!pipeline.InlineParsers.Contains<PipeTableParser>())
        {
            pipeline.InlineParsers.InsertAfter<EmphasisInlineParser>(new PipeTableParser(lineBreakParser!, Options));
        }
    }

    /// <summary>
    /// Configures this extension for the specified pipeline stage.
    /// </summary>
    public void Setup(MarkdownPipeline pipeline, IMarkdownRenderer renderer)
    {
        if (renderer is HtmlRenderer htmlRenderer && !htmlRenderer.ObjectRenderers.Contains<HtmlTableRenderer>())
        {
            htmlRenderer.ObjectRenderers.Add(new HtmlTableRenderer());
        }
    }
}
</production_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="218-393">
        if (Options.RequireHeaderSeparator && aligns is null)
        {
            // No valid header separator found - convert all pipe delimiters to literals
            foreach (var inline in delimiters)
            {
                if (inline is PipeTableDelimiterInline pipeDelimiter)
                {
                    pipeDelimiter.ReplaceByLiteral();
                }
            }
            return true;
        }

        var table = new Table();

        // If the current paragraph block has any attributes attached, we can copy them
        var attributes = state.Block!.TryGetAttributes();
        if (attributes != null)
        {
            attributes.CopyTo(table.GetAttributes());
        }

        var cells = tableState.Cells;
        cells.Clear();

        // Pipes may end up nested inside unmatched emphasis delimiters, e.g.:
        //     *a | b*|
        // Promote them to root level so we have a flat sibling structure.
        PromoteNestedPipesToRootLevel(delimiters, container);

        // The inline tree is now flat: all pipes and line breaks are siblings at root level.
        // For example, `| a | b \n| c | d \n` produces:
        //     [|] [a] [|] [b] [\n] [|] [c] [|] [d] [\n]
        //
        // Tables support four row formats:
        //     | a | b |    (leading and trailing pipes)
        //     | a | b      (leading pipe only)
        //       a | b      (no leading or trailing pipes)
        //       a | b |    (trailing pipe only)

        // Ensure the table ends with a line break to simplify row detection
        var lastElement = delimiters[delimiters.Count - 1];
        if (!(lastElement is LineBreakInline))
        {
            // Find the actual last sibling (there may be content after the last delimiter)
            while (lastElement.NextSibling != null)
            {
                lastElement = lastElement.NextSibling;
            }

            var endOfTable = new LineBreakInline();
            lastElement.InsertAfter(endOfTable);
            delimiters.Add(endOfTable);
            tableState.EndOfLines.Add(endOfTable);
        }

        int lastPipePos = 0;

        // Build table rows and cells by iterating through delimiters
        TableRow? row = null;
        TableRow? firstRow = null;
        for (int i = 0; i < delimiters.Count; i++)
        {
            var delimiter = delimiters[i];
            var pipeSeparator = delimiter as PipeTableDelimiterInline;
            var isLine = delimiter is LineBreakInline;

            if (row is null)
            {
                row = new TableRow();

                firstRow ??= row;

                // Skip leading pipe at start of row (e.g., `| a | b` or `| a | b |`)
                if (pipeSeparator != null && (delimiter.PreviousSibling is null || delimiter.PreviousSibling is LineBreakInline))
                {
                    delimiter.Remove();
                    if (table.Span.IsEmpty)
                    {
                        table.Span = delimiter.Span;
                        table.Line = delimiter.Line;
                        table.Column = delimiter.Column;
                    }
                    continue;
                }
            }

            // Find cell content by walking backwards from this delimiter to the previous pipe or line break.
            // For `| a | b \n` at delimiter 'x':
            //       [|] [a] [x] [b] [\n]
            //                ^--- current delimiter
            // Walk back: [a] is the cell content (stop at [|])
            Inline? endOfCell = null;
            Inline? beginOfCell = null;
            var cellContentIt = delimiter.PreviousSibling;
            while (cellContentIt != null)
            {
                if (cellContentIt is LineBreakInline || cellContentIt is PipeTableDelimiterInline)
                    break;

                // Stop at the root ContainerInline (which is not necessary to bring into the tree + it contains an invalid span calculation)
                if (cellContentIt.GetType() == typeof(ContainerInline) && cellContentIt.Parent is null)
                    break;

                beginOfCell = cellContentIt;
                endOfCell ??= beginOfCell;

                cellContentIt = cellContentIt.PreviousSibling;
            }

            // If the current delimiter is a pipe `|` OR
            // the beginOfCell/endOfCell are not null and
            // either they are:
            // - different
            // - they contain a single element, but it is not a line break (\n) or an empty/whitespace Literal.
            // Then we can add a cell to the current row
            if (!isLine || (beginOfCell != null && endOfCell != null && ( beginOfCell != endOfCell || !(beginOfCell is LineBreakInline || (beginOfCell is LiteralInline beingOfCellLiteral && beingOfCellLiteral.Content.IsEmptyOrWhitespace())))))
            {
                // We trim whitespace at the beginning and ending of the cell
                TrimStart(beginOfCell);
                TrimEnd(endOfCell);

                var cellContainer = new ContainerInline();

                // Copy elements from beginOfCell on the first level
                // The pipe delimiter serves as a boundary - stop when we hit it
                var cellIt = beginOfCell;
                while (cellIt != null && !IsLine(cellIt) && !(cellIt is PipeTableDelimiterInline))
                {
                    var nextSibling = cellIt.NextSibling;

                    // Skip empty literals (can result from trimming)
                    if (cellIt is LiteralInline { Content.IsEmpty: true })
                    {
                        cellIt.Remove();
                        cellIt = nextSibling;
                        continue;
                    }

                    cellIt.Remove();
                    if (cellContainer.Span.IsEmpty)
                    {
                        cellContainer.Line = cellIt.Line;
                        cellContainer.Column = cellIt.Column;
                        cellContainer.Span = cellIt.Span;
                    }
                    cellContainer.AppendChild(cellIt);
                    cellContainer.Span.End = cellIt.Span.End;
                    cellIt = nextSibling;
                }

                if (!isLine)
                {
                    // Remove the pipe delimiter AFTER copying cell content
                    // This preserves the sibling chain during the copy loop
                    delimiter.Remove();
                    lastPipePos = delimiter.Span.End;
                }

                // Create the cell and add it to the pending row
                var tableParagraph = new ParagraphBlock
                {
                    Span = cellContainer.Span,
                    Line = cellContainer.Line,
                    Column = cellContainer.Column,
                    Inline = cellContainer
                };

                var tableCell = new TableCell()
                {
                    Span = cellContainer.Span,
                    Line = cellContainer.Line,
                    Column = cellContainer.Column,
                };

                tableCell.Add(tableParagraph);
</production_snippet>

<production_snippet path="src/Markdig/Extensions/Tables/PipeTableParser.cs" lines="415-458">
                row = null;
            }
        }

        if (lastPipePos > table.Span.End)
        {
          table.UpdateSpanEnd(lastPipePos);
        }

        // Once we are done with the cells, we can remove all end of lines in the table tree
        foreach (var endOfLine in tableState.EndOfLines)
        {
            endOfLine.Remove();
        }

        // Mark first row as header and remove the separator row if present
        var tableRow = (TableRow)table[0];
        tableRow.IsHeader = Options.RequireHeaderSeparator;
        if (aligns != null)
        {
            tableRow.IsHeader = true;
            table.RemoveAt(1);
            table.ColumnDefinitions.AddRange(aligns);
        }

        // Perform all post-processors on cell content
        // With InsertAfter, emphasis runs before pipe table, so we need to re-run from index 0
        // to ensure emphasis delimiters in cells are properly matched
        foreach (var cell in cells)
        {
            var paragraph = (ParagraphBlock) cell[0];
            state.PostProcessInlines(0, paragraph.Inline, null, true);
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
</production_snippet>
