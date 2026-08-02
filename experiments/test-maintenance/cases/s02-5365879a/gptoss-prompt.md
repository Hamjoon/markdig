You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestSourcePosition.cs, src/Markdig.Tests/Specs/AbbreviationSpecs.md, src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs b/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
index 909e6ee8..e3855cc3 100644
--- a/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
+++ b/src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs
@@ -67,14 +67,14 @@ public override BlockState TryOpen(BlockProcessor processor)
         };
         if (!processor.Document.HasAbbreviations())
         {
-            processor.Document.ProcessInlinesBegin += DocumentOnProcessInlinesBegin;
+            processor.Document.ProcessInlinesEnd += DocumentOnProcessInlinesEnd;
         }
         processor.Document.AddAbbreviation(abbr.Label, abbr);
 
         return BlockState.BreakDiscard;
     }
 
-    private void DocumentOnProcessInlinesBegin(InlineProcessor inlineProcessor, Inline? inline)
+    private void DocumentOnProcessInlinesEnd(InlineProcessor inlineProcessor, Inline? inline)
     {
         var abbreviations = inlineProcessor.Document.GetAbbreviations();
         // Should not happen, but another extension could decide to remove them, so...
@@ -86,113 +86,151 @@ private void DocumentOnProcessInlinesBegin(InlineProcessor inlineProcessor, Inli
         // Build a text matcher from the abbreviations labels
         var prefixTree = new CompactPrefixTree<Abbreviation>(abbreviations);
 
-        inlineProcessor.LiteralInlineParser.PostMatch += (InlineProcessor processor, ref StringSlice slice) =>
-        {
-            var literal = (LiteralInline)processor.Inline!;
-            var originalLiteral = literal;
-            var originalSpanEnd = literal.Span.End;
+        // Allocate the traversal stack once and reuse it across all leaf blocks.
+        var stack = new Stack<ContainerInline>();
 
-            ContainerInline? container = null;
+        foreach (var leaf in inlineProcessor.Document.Descendants<LeafBlock>())
+        {
+            if (leaf.Inline is not null)
+            {
+                SubstituteInlineTree(leaf.Inline, prefixTree, stack);
+            }
+        }
+    }
 
-            // This is slow, but we don't have much the choice
-            var content = literal.Content;
-            var text = content.Text;
+    private static void SubstituteInlineTree(
+        ContainerInline root,
+        CompactPrefixTree<Abbreviation> prefixTree,
+        Stack<ContainerInline> stack)
+    {
+        stack.Push(root);
 
-            for (int i = content.Start; i <= content.End; i++)
+        while (stack.Count > 0)
+        {
+            var container = stack.Pop();
+            var child = container.FirstChild;
+            while (child != null)
             {
-                // Abbreviation must be a whole word == start at the start of a line or after a whitespace
-                if (i != 0)
+                var next = child.NextSibling;
+                if (child is LiteralInline literal)
                 {
-                    for (i = i - 1; i <= content.End; i++)
-                    {
-                        if (text[i].IsWhitespace())
-                        {
-                            i++;
-                            goto ValidAbbreviationStart;
-                        }
-                    }
-                    break;
+                    SubstituteInLiteral(literal, prefixTree);
+                }
+                else if (child is ContainerInline childContainer)
+                {
+                    stack.Push(childContainer);
                 }
+                child = next;
+            }
+        }
+    }
+
+    private static void SubstituteInLiteral(LiteralInline literal, CompactPrefixTree<Abbreviation> prefixTree)
+    {
+        var content = literal.Content;
+        var text = content.Text;
+        var parent = literal.Parent;
+
+        // Nothing to do if this literal has no parent to insert siblings into
+        if (parent is null)
+        {
+            return;
+        }
 
-            ValidAbbreviationStart:;
+        // Save original span end before any mutations: on the first substitution
+        // currentLiteral IS literal, so currentLiteral.Span.End = abbrSpanStart - 1
+        // would corrupt literal.Span.End, which we need for remaining-literal calculations.
+        var originalSpanEnd = literal.Span.End;
 
-                if (prefixTree.TryMatchLongest(text.AsSpan(i, content.End - i + 1), out KeyValuePair<string, Abbreviation> abbreviationMatch))
+        // The "current" literal we're truncating as we find abbreviations.
+        // We start with the original literal — it stays in place and we insert after it.
+        var currentLiteral = literal;
+
+        for (int i = content.Start; i <= content.End; i++)
+        {
+            // Abbreviation must start at the beginning of the content or after whitespace
+            if (i != content.Start)
+            {
+                // Find the next whitespace-separated word start
+                for (i = i - 1; i <= content.End; i++)
                 {
-                    var match = abbreviationMatch.Key;
-                    if (!IsValidAbbreviationEnding(match, content, i))
+                    if (text[i].IsWhitespace())
                     {
-                        continue;
+                        i++;
+                        goto ValidAbbreviationStart;
                     }
+                }
+                break;
+            }
 
-                    var indexAfterMatch = i + match.Length;
+        ValidAbbreviationStart:;
 
-                    // If we don't have a container, create a new one
-                    if (container is null)
-                    {
-                        container = literal.Parent ??
-                            new ContainerInline
-                            {
-                                Span = originalLiteral.Span,
-                                Line = originalLiteral.Line,
-                                Column = originalLiteral.Column,
-                            };
-                    }
+            if (prefixTree.TryMatchLongest(text.AsSpan(i, content.End - i + 1), out KeyValuePair<string, Abbreviation> abbreviationMatch))
+            {
+                var match = abbreviationMatch.Key;
+                if (!IsValidAbbreviationEnding(match, content, i))
+                {
+                    continue;
+                }
 
-                    var abbrInline = new AbbreviationInline(abbreviationMatch.Value)
-                    {
-                        Span =
-                        {
-                            Start = processor.GetSourcePosition(i, out int line, out int column),
-                        },
-                        Line = line,
-                        Column = column
-                    };
-                    abbrInline.Span.End = abbrInline.Span.Start + match.Length - 1;
+                var indexAfterMatch = i + match.Length;
 
-                    // Append the previous literal
-                    if (i > content.Start && literal.Parent is null)
-                    {
-                        container.AppendChild(literal);
-                    }
+                // Compute source position from the original literal's own span/line/column.
+                // We use literal.Content.Start (the ORIGINAL literal parameter, never reassigned)
+                // because span positions are always relative to the start of the original literal.
+                // (InlineProcessor is not available post-parse; this is safe because
+                //  LiteralInlineParser never produces a literal spanning a line break.)
+                int charOffset = i - literal.Content.Start; // offset from original literal start
+                var abbrSpanStart = literal.Span.Start + charOffset;
+                var abbrInline = new AbbreviationInline(abbreviationMatch.Value)
+                {
+                    Span = new SourceSpan(abbrSpanStart, abbrSpanStart + match.Length - 1),
+                    Line = literal.Line,
+                    Column = literal.Column + charOffset,
+                };
 
-                    literal.Span.End = abbrInline.Span.Start - 1;
-                    // Truncate it before the abbreviation
-                    literal.Content.End = i - 1;
+                // Truncate currentLiteral to end just before the abbreviation
+                currentLiteral.Content.End = i - 1;
+                currentLiteral.Span.End = abbrSpanStart - 1;
 
+                // Insert abbreviation after currentLiteral
+                currentLiteral.InsertAfter(abbrInline);
 
-                    // Append the abbreviation
-                    container.AppendChild(abbrInline);
+                // If the truncated literal is now empty (abbreviation was at the very start
+                // of its content), remove it so it doesn't litter the tree.
+                if (currentLiteral.Content.End < currentLiteral.Content.Start)
+                {
+                    currentLiteral.Remove();
+                }
 
-                    // If this is the end of the string, clear the literal and exit
-                    if (content.End == indexAfterMatch - 1)
-                    {
-                        literal = null;
-                        break;
-                    }
+                // If there is remaining text after the abbreviation, create a new literal for it
+                if (indexAfterMatch <= content.End)
+                {
+                    var remainingContent = content;
+                    remainingContent.Start = indexAfterMatch;
 
-                    // Process the remaining literal
-                    literal = new LiteralInline()
+                    var remainingLiteral = new LiteralInline
                     {
+                        Content = remainingContent,
                         Span = new SourceSpan(abbrInline.Span.End + 1, originalSpanEnd),
-                        Line = line,
-                        Column = column + match.Length,
+                        Line = literal.Line,
+                        Column = literal.Column + (indexAfterMatch - literal.Content.Start),
                     };
-                    content.Start = indexAfterMatch;
-                    literal.Content = content;
+                    abbrInline.InsertAfter(remainingLiteral);
 
+                    // Continue scanning from the new literal
+                    currentLiteral = remainingLiteral;
+                    // Update content reference so the loop bounds are correct
+                    content = remainingContent;
                     i = indexAfterMatch - 1;
                 }
-            }
-
-            if (container != null)
-            {
-                if (literal != null)
+                else
                 {
-                    container.AppendChild(literal);
+                    // No text left — stop
+                    break;
                 }
-                processor.Inline = container;
             }
-        };
+        }
     }
 
     private static bool IsValidAbbreviationEnding(string match, StringSlice content, int matchIndex)
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Failed TestAbbreviations [13 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  Expected string length 280 but was 223. Strings differ at index 28.
  Expected: "paragraph    ( 2, 0) 38-102\ncontainer    ( 2, 0) 38-102\nliter..."
  But was:  "paragraph    ( 2, 0) 38-102\nliteral      ( 2, 0) 38-66\nabbrev..."
  ----------------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestAbbreviations() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 536

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestAbbreviations() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 536


  Standard Output Messages:
 ```````````````````Source
 *[HTML]:·Hypertext·Markup·Language

 Later·in·a·text·we·are·using·HTML·and·it·becomes·an·abbr·tag·HTML

 HTML·abbreviation·at·the·beginning·of·a·line
 ```````````````````Result
 paragraph    ( 2, 0) 38-102
 literal      ( 2, 0) 38-66
 abbreviation ( 2,29) 67-70
 literal      ( 2,33) 71-98
 abbreviation ( 2,61) 99-102
 paragraph    ( 4, 0) 107-150
 abbreviation ( 4, 0) 107-110
 literal      ( 4, 4) 111-150
 ```````````````````Expected
 paragraph    ( 2, 0) 38-102
 container    ( 2, 0) 38-102
 literal      ( 2, 0) 38-66
 abbreviation ( 2,29) 67-70
 literal      ( 2,33) 71-98
 abbreviation ( 2,61) 99-102
 paragraph    ( 4, 0) 107-150
 container    ( 4, 0) 107-150
 abbreviation ( 4, 0) 107-110
 literal      ( 4, 4) 111-150
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 28     99   c     108  l
 *** 29     111  o     105  i
 *** 30     110  n     116  t
 *** 31     116  t     101  e
 *** 32     97   a     114  r
 *** 33     105  i     97   a
 *** 34     110  n     108  l
 *** 35     101  e     32   \u20;
 *** 36     114  r     32   \u20;



Failed!  - Failed:     1, Passed:    73, Skipped:     0, Total:    74, Duration: 101 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestSourcePosition.cs" lines="513-569">
        Check(@"\-\)", @"
paragraph    ( 0, 0)  0-3
literal      ( 0, 0)  0-1
literal      ( 0, 2)  2-3
");
    }

    [Test]
    public void TestHtmlEntityInline()
    {
        //     01 23456789
        Check("0\n&nbsp; 1", @"
paragraph    ( 0, 0)  0-9
literal      ( 0, 0)  0-0
linebreak    ( 0, 1)  1-1
htmlentity   ( 1, 0)  2-7
literal      ( 1, 6)  8-9
");
    }

    [Test]
    public void TestAbbreviations()
    {
        Check("*[HTML]: Hypertext Markup Language\r\n\r\nLater in a text we are using HTML and it becomes an abbr tag HTML\r\n\r\nHTML abbreviation at the beginning of a line", @"
paragraph    ( 2, 0) 38-102
container    ( 2, 0) 38-102
literal      ( 2, 0) 38-66
abbreviation ( 2,29) 67-70
literal      ( 2,33) 71-98
abbreviation ( 2,61) 99-102
paragraph    ( 4, 0) 107-150
container    ( 4, 0) 107-150
abbreviation ( 4, 0) 107-110
literal      ( 4, 4) 111-150
", "abbreviations");
    }

    [Test]
    public void TestCitation()
    {
        //     0123 4 567 8
        Check("01 \"\"23\"\"", @"
paragraph    ( 0, 0)  0-8
literal      ( 0, 0)  0-2
emphasis     ( 0, 3)  3-8
literal      ( 0, 5)  5-6
", "citations");
    }

    [Test]
    public void TestCustomContainer()
    {
        //     01 2345 678 9ABC DEF
        Check("0\n:::\n23\n:::\n45\n", @"
paragraph    ( 0, 0)  0-0
literal      ( 0, 0)  0-0
customcontainer ( 1, 0)  2-11
</test_snippet>

<test_snippet path="src/Markdig.Tests/Specs/AbbreviationSpecs.md" lines="96-121">

PRAA
.
<p>PRAA</p>
````````````````````````````````

Single character abbreviations should be matched

```````````````````````````````` example
*[A]: Foo

A
.
<p><abbr title="Foo">A</abbr></p>
````````````````````````````````

The longest matching abbreviation should be used

```````````````````````````````` example
*[Foo]: foo
*[Foo Bar]: foobar

Foo B
.
<p><abbr title="foo">Foo</abbr> B</p>
````````````````````````````````
</test_snippet>

<production_snippet path="src/Markdig/Extensions/Abbreviations/AbbreviationParser.cs" lines="45-258">
        if (!LinkHelper.TryParseLabel(ref slice, out string? label, out SourceSpan labelSpan))
        {
            return BlockState.None;
        }

        c = slice.CurrentChar;
        if (c != ':')
        {
            return BlockState.None;
        }
        slice.SkipChar();

        slice.Trim();

        var abbr = new Abbreviation(this)
        {
            Label = label,
            Text = slice,
            Span = new SourceSpan(startPosition, slice.End),
            Line = processor.LineIndex,
            Column = processor.Column,
            LabelSpan = labelSpan,
        };
        if (!processor.Document.HasAbbreviations())
        {
            processor.Document.ProcessInlinesEnd += DocumentOnProcessInlinesEnd;
        }
        processor.Document.AddAbbreviation(abbr.Label, abbr);

        return BlockState.BreakDiscard;
    }

    private void DocumentOnProcessInlinesEnd(InlineProcessor inlineProcessor, Inline? inline)
    {
        var abbreviations = inlineProcessor.Document.GetAbbreviations();
        // Should not happen, but another extension could decide to remove them, so...
        if (abbreviations is null)
        {
            return;
        }

        // Build a text matcher from the abbreviations labels
        var prefixTree = new CompactPrefixTree<Abbreviation>(abbreviations);

        // Allocate the traversal stack once and reuse it across all leaf blocks.
        var stack = new Stack<ContainerInline>();

        foreach (var leaf in inlineProcessor.Document.Descendants<LeafBlock>())
        {
            if (leaf.Inline is not null)
            {
                SubstituteInlineTree(leaf.Inline, prefixTree, stack);
            }
        }
    }

    private static void SubstituteInlineTree(
        ContainerInline root,
        CompactPrefixTree<Abbreviation> prefixTree,
        Stack<ContainerInline> stack)
    {
        stack.Push(root);

        while (stack.Count > 0)
        {
            var container = stack.Pop();
            var child = container.FirstChild;
            while (child != null)
            {
                var next = child.NextSibling;
                if (child is LiteralInline literal)
                {
                    SubstituteInLiteral(literal, prefixTree);
                }
                else if (child is ContainerInline childContainer)
                {
                    stack.Push(childContainer);
                }
                child = next;
            }
        }
    }

    private static void SubstituteInLiteral(LiteralInline literal, CompactPrefixTree<Abbreviation> prefixTree)
    {
        var content = literal.Content;
        var text = content.Text;
        var parent = literal.Parent;

        // Nothing to do if this literal has no parent to insert siblings into
        if (parent is null)
        {
            return;
        }

        // Save original span end before any mutations: on the first substitution
        // currentLiteral IS literal, so currentLiteral.Span.End = abbrSpanStart - 1
        // would corrupt literal.Span.End, which we need for remaining-literal calculations.
        var originalSpanEnd = literal.Span.End;

        // The "current" literal we're truncating as we find abbreviations.
        // We start with the original literal — it stays in place and we insert after it.
        var currentLiteral = literal;

        for (int i = content.Start; i <= content.End; i++)
        {
            // Abbreviation must start at the beginning of the content or after whitespace
            if (i != content.Start)
            {
                // Find the next whitespace-separated word start
                for (i = i - 1; i <= content.End; i++)
                {
                    if (text[i].IsWhitespace())
                    {
                        i++;
                        goto ValidAbbreviationStart;
                    }
                }
                break;
            }

        ValidAbbreviationStart:;

            if (prefixTree.TryMatchLongest(text.AsSpan(i, content.End - i + 1), out KeyValuePair<string, Abbreviation> abbreviationMatch))
            {
                var match = abbreviationMatch.Key;
                if (!IsValidAbbreviationEnding(match, content, i))
                {
                    continue;
                }

                var indexAfterMatch = i + match.Length;

                // Compute source position from the original literal's own span/line/column.
                // We use literal.Content.Start (the ORIGINAL literal parameter, never reassigned)
                // because span positions are always relative to the start of the original literal.
                // (InlineProcessor is not available post-parse; this is safe because
                //  LiteralInlineParser never produces a literal spanning a line break.)
                int charOffset = i - literal.Content.Start; // offset from original literal start
                var abbrSpanStart = literal.Span.Start + charOffset;
                var abbrInline = new AbbreviationInline(abbreviationMatch.Value)
                {
                    Span = new SourceSpan(abbrSpanStart, abbrSpanStart + match.Length - 1),
                    Line = literal.Line,
                    Column = literal.Column + charOffset,
                };

                // Truncate currentLiteral to end just before the abbreviation
                currentLiteral.Content.End = i - 1;
                currentLiteral.Span.End = abbrSpanStart - 1;

                // Insert abbreviation after currentLiteral
                currentLiteral.InsertAfter(abbrInline);

                // If the truncated literal is now empty (abbreviation was at the very start
                // of its content), remove it so it doesn't litter the tree.
                if (currentLiteral.Content.End < currentLiteral.Content.Start)
                {
                    currentLiteral.Remove();
                }

                // If there is remaining text after the abbreviation, create a new literal for it
                if (indexAfterMatch <= content.End)
                {
                    var remainingContent = content;
                    remainingContent.Start = indexAfterMatch;

                    var remainingLiteral = new LiteralInline
                    {
                        Content = remainingContent,
                        Span = new SourceSpan(abbrInline.Span.End + 1, originalSpanEnd),
                        Line = literal.Line,
                        Column = literal.Column + (indexAfterMatch - literal.Content.Start),
                    };
                    abbrInline.InsertAfter(remainingLiteral);

                    // Continue scanning from the new literal
                    currentLiteral = remainingLiteral;
                    // Update content reference so the loop bounds are correct
                    content = remainingContent;
                    i = indexAfterMatch - 1;
                }
                else
                {
                    // No text left — stop
                    break;
                }
            }
        }
    }

    private static bool IsValidAbbreviationEnding(string match, StringSlice content, int matchIndex)
    {
        // This will check if the next char at the end of the StringSlice is whitespace, punctuation or \0.
        var contentNew = content;
        contentNew.End = content.End + 1;
        int index = matchIndex + match.Length;
        while (index <= contentNew.End)
        {
            var c = contentNew.PeekCharAbsolute(index);

            if (c.IsWhitespace())
            {
                break;
            }

            if (!c.IsAsciiPunctuationOrZero())
            {
                return false;
            }

            index++;
        }
        return true;
</production_snippet>
