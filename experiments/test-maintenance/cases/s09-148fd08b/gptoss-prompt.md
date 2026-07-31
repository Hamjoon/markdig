You are maintaining a C#/.NET library. A change was recently applied to this repository.
Review the recent change and the current test results, then decide whether any modification
is needed: update tests, fix production code, or no change at all.

Constraints:
- The first line of your reply must be exactly one of: `DECISION: no_change`, `DECISION: fix_tests`, `DECISION: fix_production`.
- If the decision is `fix_tests` or `fix_production`, follow the DECISION line with a unified diff implementing the fix. If the decision is `no_change`, output no diff.
- Allowed files: src/Markdig.Tests/TestExtensionSpanCoverage.cs, src/Markdig.Tests/TestParserAuthoringHelpers.cs, src/Markdig.Tests/TestSourcePosition.cs, src/Markdig.Tests/TestSpanConsistency.cs, src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs, src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs, src/Markdig/Parsers/InlineProcessor.cs, src/Markdig/Syntax/Block.cs, src/Markdig/Syntax/ContainerBlock.cs, src/Markdig/Syntax/Inlines/ContainerInline.cs.
- Do not weaken, delete, or skip assertions.
- Preserve nearby behavior that is still expected to pass.

Recent change applied to the repository:
<recent_change_diff>
diff --git a/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs b/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs
index bb3af8cf..e1dd0ced 100644
--- a/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs
+++ b/src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs
@@ -75,7 +75,7 @@ public override BlockState TryOpen(BlockProcessor processor)
         {
             Line = processor.LineIndex,
             Column = column,
-            Span = new SourceSpan(startPosition, processor.Line.End),
+            Span = new SourceSpan(paragraphBlock.Span.Start, processor.Line.End),
             OpeningCharacter = processor.CurrentChar,
         };
 
@@ -199,4 +199,4 @@ public override BlockState TryContinue(BlockProcessor processor, Block block)
         list.Span.End = list.LastChild!.Span.End;
         return BlockState.Break;
     }
-}
\ No newline at end of file
+}
diff --git a/src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs b/src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs
index 3793c73e..37584397 100644
--- a/src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs
+++ b/src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs
@@ -5,6 +5,7 @@
 using Markdig.Helpers;
 using Markdig.Parsers;
 using Markdig.Renderers.Html;
+using Markdig.Syntax;
 using Markdig.Syntax.Inlines;
 
 namespace Markdig.Extensions.JiraLinks;
@@ -80,18 +81,15 @@ public override bool Match(InlineProcessor processor, ref StringSlice slice)
             return false;
         }
 
+        int spanStart = processor.GetSourcePosition(startKey, out int line, out int column);
         var jiraLink = new JiraLink() //create the link at the relevant position
         {
-            Span =
-            {
-                Start = processor.GetSourcePosition(slice.Start, out int line, out int column)
-            },
+            Span = new SourceSpan(spanStart, spanStart + (endIssue - startKey)),
             Line = line,
             Column = column,
             Issue = new StringSlice(slice.Text, startIssue, endIssue),
             ProjectKey = new StringSlice(slice.Text, startKey, endKey),
         };
-        jiraLink.Span.End = jiraLink.Span.Start + (endIssue - startKey);
 
         // Builds the Url
         var builder = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);
@@ -107,7 +105,12 @@ public override bool Match(InlineProcessor processor, ref StringSlice slice)
         builder.Append(jiraLink.ProjectKey.AsSpan());
         builder.Append('-');
         builder.Append(jiraLink.Issue.AsSpan());
-        jiraLink.AppendChild(new LiteralInline(builder.ToString()));
+        jiraLink.AppendChild(new LiteralInline(builder.ToString())
+        {
+            Span = jiraLink.Span,
+            Line = line,
+            Column = column,
+        });
 
         if (_options.OpenInNewWindow)
         {
diff --git a/src/Markdig/Parsers/InlineProcessor.cs b/src/Markdig/Parsers/InlineProcessor.cs
index efc28ab3..f42f322e 100644
--- a/src/Markdig/Parsers/InlineProcessor.cs
+++ b/src/Markdig/Parsers/InlineProcessor.cs
@@ -456,6 +456,29 @@ public void Emit(Inline inline)
 
         var container = FindLastContainer();
         container.AppendChild(inline);
+
+        if (ReferenceEquals(container, Root) && !inline.Span.IsEmpty)
+        {
+            if (container.Span.IsEmpty)
+            {
+                container.Span = inline.Span;
+            }
+            else
+            {
+                if (inline.Span.Start < container.Span.Start)
+                {
+                    container.Span.Start = inline.Span.Start;
+                }
+
+                if (inline.Span.End > container.Span.End)
+                {
+                    container.Span.End = inline.Span.End;
+                }
+            }
+
+            Block?.UpdateSpanToInclude(inline.Span);
+        }
+
         Inline = inline;
     }
 
diff --git a/src/Markdig/Syntax/Block.cs b/src/Markdig/Syntax/Block.cs
index 6f1da94f..14b29c3d 100644
--- a/src/Markdig/Syntax/Block.cs
+++ b/src/Markdig/Syntax/Block.cs
@@ -137,6 +137,45 @@ internal void OnProcessInlinesEnd(InlineProcessor state)
         }
     }
 
+    /// <summary>
+    /// Updates this block span and all parent container spans to include the specified <paramref name="span"/>.
+    /// </summary>
+    /// <param name="span">The span to include.</param>
+    public void UpdateSpanToInclude(SourceSpan span)
+    {
+        if (span.IsEmpty)
+        {
+            return;
+        }
+
+        int depth = 0;
+        Block? current = this;
+        while (current is not null)
+        {
+            if (current.Span.IsEmpty)
+            {
+                current.Span = span;
+            }
+            else
+            {
+                if (span.Start < current.Span.Start)
+                {
+                    current.Span.Start = span.Start;
+                }
+
+                if (span.End > current.Span.End)
+                {
+                    current.Span.End = span.End;
+                }
+            }
+
+            current = current.Parent;
+            depth++;
+        }
+
+        ThrowHelper.CheckDepthLimit(depth, useLargeLimit: true);
+    }
+
     public void UpdateSpanEnd(int spanEnd)
     {
         // Update parent spans
diff --git a/src/Markdig/Syntax/ContainerBlock.cs b/src/Markdig/Syntax/ContainerBlock.cs
index c460d9be..f8c177a1 100644
--- a/src/Markdig/Syntax/ContainerBlock.cs
+++ b/src/Markdig/Syntax/ContainerBlock.cs
@@ -9,6 +9,7 @@
 
 using Markdig.Helpers;
 using Markdig.Parsers;
+using Markdig.Syntax.Inlines;
 
 namespace Markdig.Syntax;
 
@@ -271,6 +272,124 @@ public Block this[int index]
         }
     }
 
+    /// <summary>
+    /// Checks whether this container span is valid with respect to child block spans.
+    /// </summary>
+    /// <param name="recursive">
+    /// When <c>true</c>, validates descendant container blocks and inline containers recursively.
+    /// </param>
+    /// <returns>
+    /// <c>true</c> when this container span contains all direct child spans and recursive checks (if enabled) succeed;
+    /// otherwise, <c>false</c>.
+    /// </returns>
+    public bool HasValidSpan(bool recursive = false)
+    {
+        var children = _children;
+        for (int i = 0; i < Count && i < children.Length; i++)
+        {
+            var child = children[i].Block;
+            if (!ContainsSpan(Span, child.Span))
+            {
+                return false;
+            }
+
+            if (!recursive)
+            {
+                continue;
+            }
+
+            if (child is ContainerBlock containerBlock)
+            {
+                if (!containerBlock.HasValidSpan(recursive: true))
+                {
+                    return false;
+                }
+            }
+            else if (child is LeafBlock leafBlock && leafBlock.Inline is ContainerInline inline)
+            {
+                if (!ContainsSpan(leafBlock.Span, inline.Span))
+                {
+                    return false;
+                }
+
+                if (!inline.HasValidSpan(recursive: true))
+                {
+                    return false;
+                }
+            }
+        }
+
+        return true;
+    }
+
+    /// <summary>
+    /// Updates this container span from its child block spans.
+    /// </summary>
+    /// <param name="recursive">
+    /// When <c>true</c>, updates descendant container blocks and inline containers recursively before updating this container.
+    /// </param>
+    /// <param name="preserveSelfSpan">
+    /// When <c>true</c>, preserves this container current span and only expands it to include children.
+    /// When <c>false</c>, recomputes from children only.
+    /// </param>
+    /// <returns><c>true</c> when this container span changed; otherwise, <c>false</c>.</returns>
+    public bool UpdateSpanFromChildren(bool recursive = false, bool preserveSelfSpan = true)
+    {
+        var updatedSpan = SourceSpan.Empty;
+        bool hasUpdatedSpan = false;
+
+        if (preserveSelfSpan && !Span.IsEmpty)
+        {
+            updatedSpan = Span;
+            hasUpdatedSpan = true;
+        }
+
+        var children = _children;
+        for (int i = 0; i < Count && i < children.Length; i++)
+        {
+            var child = children[i].Block;
+
+            if (recursive)
+            {
+                if (child is ContainerBlock containerBlock)
+                {
+                    containerBlock.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);
+                }
+                else if (child is LeafBlock leafBlock && leafBlock.Inline is ContainerInline inline)
+                {
+                    inline.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);
+
+                    if (!ContainsSpan(leafBlock.Span, inline.Span))
+                    {
+                        if (preserveSelfSpan && !leafBlock.Span.IsEmpty)
+                        {
+                            leafBlock.UpdateSpanToInclude(inline.Span);
+                        }
+                        else
+                        {
+                            leafBlock.Span = inline.Span;
+                        }
+                    }
+                }
+            }
+
+            AppendSpan(ref updatedSpan, ref hasUpdatedSpan, child.Span);
+        }
+
+        if (!hasUpdatedSpan)
+        {
+            updatedSpan = SourceSpan.Empty;
+        }
+
+        if (updatedSpan == Span)
+        {
+            return false;
+        }
+
+        Span = updatedSpan;
+        return true;
+    }
+
     public void Sort(IComparer<Block> comparer)
     {
         if (comparer is null) ThrowHelper.ArgumentNullException(nameof(comparer));
@@ -353,4 +472,36 @@ public int Compare(BlockWrapper x, BlockWrapper y)
             return _comparer.Compare(x.Block, y.Block);
         }
     }
+
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static bool ContainsSpan(in SourceSpan containerSpan, in SourceSpan childSpan)
+    {
+        return childSpan.IsEmpty || (!containerSpan.IsEmpty && childSpan.Start >= containerSpan.Start && childSpan.End <= containerSpan.End);
+    }
+
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static void AppendSpan(ref SourceSpan destinationSpan, ref bool hasDestinationSpan, in SourceSpan spanToAppend)
+    {
+        if (spanToAppend.IsEmpty)
+        {
+            return;
+        }
+
+        if (!hasDestinationSpan)
+        {
+            destinationSpan = spanToAppend;
+            hasDestinationSpan = true;
+            return;
+        }
+
+        if (spanToAppend.Start < destinationSpan.Start)
+        {
+            destinationSpan.Start = spanToAppend.Start;
+        }
+
+        if (spanToAppend.End > destinationSpan.End)
+        {
+            destinationSpan.End = spanToAppend.End;
+        }
+    }
 }
diff --git a/src/Markdig/Syntax/Inlines/ContainerInline.cs b/src/Markdig/Syntax/Inlines/ContainerInline.cs
index 2596f79f..1a0b686b 100644
--- a/src/Markdig/Syntax/Inlines/ContainerInline.cs
+++ b/src/Markdig/Syntax/Inlines/ContainerInline.cs
@@ -5,8 +5,10 @@
 using System.Collections;
 using System.Diagnostics;
 using System.IO;
+using System.Runtime.CompilerServices;
 
 using Markdig.Helpers;
+using Markdig.Syntax;
 
 namespace Markdig.Syntax.Inlines;
 
@@ -264,6 +266,113 @@ protected override void DumpChildTo(TextWriter writer, int level)
         }
     }
 
+    /// <summary>
+    /// Checks whether this container span is valid with respect to child inline spans.
+    /// </summary>
+    /// <param name="recursive">When <c>true</c>, validates descendant container inline spans recursively.</param>
+    /// <returns>
+    /// <c>true</c> when this container span contains all direct child spans and recursive checks (if enabled) succeed;
+    /// otherwise, <c>false</c>.
+    /// </returns>
+    public bool HasValidSpan(bool recursive = false)
+    {
+        var child = FirstChild;
+        while (child is not null)
+        {
+            if (!ContainsSpan(Span, child.Span))
+            {
+                return false;
+            }
+
+            if (recursive && child is ContainerInline childContainer && !childContainer.HasValidSpan(recursive: true))
+            {
+                return false;
+            }
+
+            child = child.NextSibling;
+        }
+
+        return true;
+    }
+
+    /// <summary>
+    /// Updates this container span from its child inline spans.
+    /// </summary>
+    /// <param name="recursive">When <c>true</c>, updates descendant container inline spans recursively before updating this container.</param>
+    /// <param name="preserveSelfSpan">
+    /// When <c>true</c>, preserves this container current span and only expands it to include children.
+    /// When <c>false</c>, recomputes from children only.
+    /// </param>
+    /// <returns><c>true</c> when this container span changed; otherwise, <c>false</c>.</returns>
+    public bool UpdateSpanFromChildren(bool recursive = false, bool preserveSelfSpan = true)
+    {
+        var updatedSpan = SourceSpan.Empty;
+        bool hasUpdatedSpan = false;
+
+        if (preserveSelfSpan && !Span.IsEmpty)
+        {
+            updatedSpan = Span;
+            hasUpdatedSpan = true;
+        }
+
+        var child = FirstChild;
+        while (child is not null)
+        {
+            if (recursive && child is ContainerInline childContainer)
+            {
+                childContainer.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);
+            }
+
+            AppendSpan(ref updatedSpan, ref hasUpdatedSpan, child.Span);
+            child = child.NextSibling;
+        }
+
+        if (!hasUpdatedSpan)
+        {
+            updatedSpan = SourceSpan.Empty;
+        }
+
+        if (updatedSpan == Span)
+        {
+            return false;
+        }
+
+        Span = updatedSpan;
+        return true;
+    }
+
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static bool ContainsSpan(in SourceSpan containerSpan, in SourceSpan childSpan)
+    {
+        return childSpan.IsEmpty || (!containerSpan.IsEmpty && childSpan.Start >= containerSpan.Start && childSpan.End <= containerSpan.End);
+    }
+
+    [MethodImpl(MethodImplOptions.AggressiveInlining)]
+    private static void AppendSpan(ref SourceSpan destinationSpan, ref bool hasDestinationSpan, in SourceSpan spanToAppend)
+    {
+        if (spanToAppend.IsEmpty)
+        {
+            return;
+        }
+
+        if (!hasDestinationSpan)
+        {
+            destinationSpan = spanToAppend;
+            hasDestinationSpan = true;
+            return;
+        }
+
+        if (spanToAppend.Start < destinationSpan.Start)
+        {
+            destinationSpan.Start = spanToAppend.Start;
+        }
+
+        if (spanToAppend.End > destinationSpan.End)
+        {
+            destinationSpan.End = spanToAppend.End;
+        }
+    }
+
     public struct Enumerator : IEnumerator<Inline>
     {
         private readonly ContainerInline container;
</recent_change_diff>

Current test results:
<test_output>
Test run for <worktree>/src/Markdig.Tests/bin/Release/net10.0/Markdig.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.
  Failed TestDefinitionList [16 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  String lengths are both 165. Strings differ at index 53.
  Expected: "definitionlist ( 0, 0)  0-10\ndefinitionitem ( 1, 0)  3-10\ndef..."
  But was:  "definitionlist ( 0, 0)  0-10\ndefinitionitem ( 1, 0)  0-10\ndef..."
  -----------------------------------------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestDefinitionList() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 581

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestDefinitionList() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 581


  Standard Output Messages:
 ```````````````````Source
 a0
 :···1234
 ```````````````````Result
 definitionlist ( 0, 0)  0-10
 definitionitem ( 1, 0)  0-10
 definitionterm ( 0, 0)  0-1
 literal      ( 0, 0)  0-1
 paragraph    ( 1, 4)  7-10
 literal      ( 1, 4)  7-10
 ```````````````````Expected
 definitionlist ( 0, 0)  0-10
 definitionitem ( 1, 0)  3-10
 definitionterm ( 0, 0)  0-1
 literal      ( 0, 0)  0-1
 paragraph    ( 1, 4)  7-10
 literal      ( 1, 4)  7-10
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 53     51   3     48   0


  Failed TestDefinitionList2 [< 1 ms]
  Error Message:
     Assert.That(actual, Is.EqualTo(expected))
  String lengths are both 248. Strings differ at index 53.
  Expected: "definitionlist ( 0, 0)  0-20\ndefinitionitem ( 1, 0)  3-10\ndef..."
  But was:  "definitionlist ( 0, 0)  0-20\ndefinitionitem ( 1, 0)  0-10\ndef..."
  -----------------------------------------------------------------^

  Stack Trace:
     at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestDefinitionList2() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 595

1)    at NUnit.Framework.Legacy.ClassicAssert.AreEqual(Object expected, Object actual)
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue, DiffStyle diffStyle, TextWriter output) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 86
   at Markdig.Tests.TextAssert.AreEqual(String expectedValue, String actualValue) in <worktree>/src/Markdig.Tests/TextAssert.cs:line 22
   at Markdig.Tests.TestSourcePosition.Check(String text, String expectedResult, String extensions, Boolean trackTrivia) in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 991
   at Markdig.Tests.TestSourcePosition.TestDefinitionList2() in <worktree>/src/Markdig.Tests/TestSourcePosition.cs:line 595


  Standard Output Messages:
 ```````````````````Source
 a0
 :···1234
 :····5678
 ```````````````````Result
 definitionlist ( 0, 0)  0-20
 definitionitem ( 1, 0)  0-10
 definitionterm ( 0, 0)  0-1
 literal      ( 0, 0)  0-1
 paragraph    ( 1, 4)  7-10
 literal      ( 1, 4)  7-10
 definitionitem ( 2, 4) 12-20
 paragraph    ( 2, 5) 17-20
 literal      ( 2, 5) 17-20
 ```````````````````Expected
 definitionlist ( 0, 0)  0-20
 definitionitem ( 1, 0)  3-10
 definitionterm ( 0, 0)  0-1
 literal      ( 0, 0)  0-1
 paragraph    ( 1, 4)  7-10
 literal      ( 1, 4)  7-10
 definitionitem ( 2, 4) 12-20
 paragraph    ( 2, 5) 17-20
 literal      ( 2, 5) 17-20
 ```````````````````


 Index    Expected     Actual
 ----------------------------
 >>> 53     51   3     48   0



Failed!  - Failed:     2, Passed:    63, Skipped:     0, Total:    65, Duration: 96 ms - Markdig.Tests.dll (net10.0)
</test_output>

<test_snippet path="src/Markdig.Tests/TestParserAuthoringHelpers.cs" lines="25-78">

        Assert.That(html, Is.EqualTo("<p>12</p>\n<p>1</p>\n"));
    }

    [Test]
    public void TryDiscardOnlyDiscardsOpenNonRootBlocks()
    {
        var parser = new ParagraphBlockParser();
        var document = new MarkdownDocument();
        var processor = new BlockProcessor(document, new BlockParserList([parser]), context: null, trackTrivia: false);

        var detached = new ParagraphBlock(parser);
        Assert.That(processor.TryDiscard(detached), Is.False);

        var paragraph = new ParagraphBlock(parser);
        document.Add(paragraph);
        processor.Open(paragraph);

        Assert.That(document.Count, Is.EqualTo(1));
        Assert.That(processor.TryDiscard(paragraph), Is.True);
        Assert.That(document.Count, Is.EqualTo(0));
        Assert.That(paragraph.Parent, Is.Null);

        Assert.That(processor.TryDiscard(document), Is.False);
    }

    private sealed class CountingInlineParser : InlineParser
    {
        public CountingInlineParser()
        {
            OpeningCharacters = ['@'];
        }

        public override bool Match(InlineProcessor processor, ref StringSlice slice)
        {
            if (slice.CurrentChar != '@')
            {
                return false;
            }

            var state = processor.GetParserState<CounterState>(this);
            state.Count++;

            processor.Emit(new LiteralInline(state.Count.ToString()));
            slice.SkipChar();
            return true;
        }
    }

    private sealed class CounterState
    {
        public int Count { get; set; }
    }
}
</test_snippet>

<test_snippet path="src/Markdig.Tests/TestSourcePosition.cs" lines="558-622">
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
paragraph    ( 2, 0)  6-7
literal      ( 2, 0)  6-7
paragraph    ( 4, 0) 13-14
literal      ( 4, 0) 13-14
", "customcontainers");
    }

    [Test]
    public void TestDefinitionList()
    {
        //     012 3456789A
        Check("a0\n:   1234", @"
definitionlist ( 0, 0)  0-10
definitionitem ( 1, 0)  3-10
definitionterm ( 0, 0)  0-1
literal      ( 0, 0)  0-1
paragraph    ( 1, 4)  7-10
literal      ( 1, 4)  7-10
", "definitionlists");
    }

    [Test]
    public void TestDefinitionList2()
    {
        //     012 3456789AB CDEF01234
        Check("a0\n:   1234\n:    5678", @"
definitionlist ( 0, 0)  0-20
definitionitem ( 1, 0)  3-10
definitionterm ( 0, 0)  0-1
literal      ( 0, 0)  0-1
paragraph    ( 1, 4)  7-10
literal      ( 1, 4)  7-10
definitionitem ( 2, 4) 12-20
paragraph    ( 2, 5) 17-20
literal      ( 2, 5) 17-20
", "definitionlists");
    }

    [Test]
    public void TestEmoji()
    {
        //     01 2345
        Check("0\n :)\n", @"
paragraph    ( 0, 0)  0-4
literal      ( 0, 0)  0-0
linebreak    ( 0, 1)  1-1
emoji        ( 1, 1)  3-4
", "emojis");
    }

    [Test]
    public void TestEmphasisExtra()
    {
</test_snippet>

<test_snippet path="src/Markdig.Tests/TestSourcePosition.cs" lines="975-1000">

        expectedResult = expectedResult.Trim();
        expectedResult = expectedResult.Replace("\r\n", "\n").Replace("\r", "\n");

        if (expectedResult != result)
        {
            Console.WriteLine("```````````````````Source");
            Console.WriteLine(TestParser.DisplaySpaceAndTabs(text));
            Console.WriteLine("```````````````````Result");
            Console.WriteLine(result);
            Console.WriteLine("```````````````````Expected");
            Console.WriteLine(expectedResult);
            Console.WriteLine("```````````````````");
            Console.WriteLine();
        }

        TextAssert.AreEqual(expectedResult, result);
    }

    private static string GetTypeName(Type type)
    {
        return type.Name.ToLowerInvariant()
            .Replace("block", string.Empty)
            .Replace("inline", string.Empty);
    }
}
</test_snippet>

<production_snippet path="src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs" lines="53-103">
        var currentDefinitionList = GetCurrentDefinitionList(paragraphBlock, previousParent);

        processor.Discard(paragraphBlock);

        // If the paragraph block was not part of the opened blocks, we need to remove it manually from its parent container
        if (paragraphBlock.Parent != null)
        {
            paragraphBlock.Parent.Remove(paragraphBlock);
        }

        if (currentDefinitionList is null)
        {
            currentDefinitionList = new DefinitionList(this)
            {
                Span = new SourceSpan(paragraphBlock.Span.Start, processor.Line.End),
                Column = paragraphBlock.Column,
                Line = paragraphBlock.Line,
            };
            previousParent.Add(currentDefinitionList);
        }

        var definitionItem = new DefinitionItem(this)
        {
            Line = processor.LineIndex,
            Column = column,
            Span = new SourceSpan(paragraphBlock.Span.Start, processor.Line.End),
            OpeningCharacter = processor.CurrentChar,
        };

        for (int i = 0; i < paragraphBlock.Lines.Count; i++)
        {
            var line = paragraphBlock.Lines.Lines[i];
            var term = new DefinitionTerm(this)
            {
                Column =  paragraphBlock.Column,
                Line = line.Line,
                Span = new SourceSpan(paragraphBlock.Span.Start, paragraphBlock.Span.End),
                IsOpen = false
            };
            term.AppendLine(ref line.Slice, line.Column, line.Line, line.Position, processor.TrackTrivia);
            definitionItem.Add(term);
        }
        currentDefinitionList.Add(definitionItem);
        processor.Open(definitionItem);

        // Update the end position
        currentDefinitionList.UpdateSpanEnd(processor.Line.End);

        return BlockState.Continue;
    }

</production_snippet>

<production_snippet path="src/Markdig/Extensions/DefinitionLists/DefinitionListParser.cs" lines="177-202">
        var isBreakable = definitionItem.LastChild?.IsBreakable ?? true;
        if (processor.IsBlankLine)
        {
            if (lastBlankLine is null && isBreakable)
            {
                definitionItem.Add(new BlankLineBlock());
            }
            return isBreakable ? BlockState.ContinueDiscard : BlockState.Continue;
        }

        var paragraphBlock = definitionItem.LastChild as ParagraphBlock;
        if (lastBlankLine is null && paragraphBlock != null)
        {
            return BlockState.Continue;
        }

        // Remove the blankline before breaking this definition item
        if (lastBlankLine != null)
        {
            definitionItem.RemoveAt(definitionItem.Count - 1);
        }

        list.Span.End = list.LastChild!.Span.End;
        return BlockState.Break;
    }
}
</production_snippet>

<production_snippet path="src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs" lines="1-33">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using Markdig.Helpers;
using Markdig.Parsers;
using Markdig.Renderers.Html;
using Markdig.Syntax;
using Markdig.Syntax.Inlines;

namespace Markdig.Extensions.JiraLinks;

/// <summary>
/// Finds and replaces JIRA links inline
/// </summary>
public class JiraLinkInlineParser : InlineParser
{
    private readonly JiraLinkOptions _options;
    private readonly string _baseUrl;

    public JiraLinkInlineParser(JiraLinkOptions options)
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _baseUrl = _options.GetUrl();
        //look for uppercase chars at the start (for the project key)
        OpeningCharacters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray();
    }

    public override bool Match(InlineProcessor processor, ref StringSlice slice)
    {
        // Allow preceding whitespace or `(`
        var pc = slice.PeekCharExtra(-1);
        if (!pc.IsWhiteSpaceOrZero() && pc != '(')
</production_snippet>

<production_snippet path="src/Markdig/Extensions/JiraLinks/JiraLinkInlineParser.cs" lines="59-124">
            return false;
        }

        current = slice.NextChar(); // skip -

        //read as many numbers as required - issue number
        if (!current.IsDigit())
        {
            return false;
        }

        var startIssue = slice.Start;
        var endIssue = slice.Start;

        while (current.IsDigit()) 
        {
            endIssue = slice.Start;
            current = slice.NextChar();
        }

        if (!current.IsWhiteSpaceOrZero() && current != ')') //can be followed only by a whitespace or `)`
        {
            return false;
        }

        int spanStart = processor.GetSourcePosition(startKey, out int line, out int column);
        var jiraLink = new JiraLink() //create the link at the relevant position
        {
            Span = new SourceSpan(spanStart, spanStart + (endIssue - startKey)),
            Line = line,
            Column = column,
            Issue = new StringSlice(slice.Text, startIssue, endIssue),
            ProjectKey = new StringSlice(slice.Text, startKey, endKey),
        };

        // Builds the Url
        var builder = new ValueStringBuilder(stackalloc char[ValueStringBuilder.StackallocThreshold]);
        builder.Append(_baseUrl);
        builder.Append('/');
        builder.Append(jiraLink.ProjectKey.AsSpan());
        builder.Append('-');
        builder.Append(jiraLink.Issue.AsSpan());
        jiraLink.Url = builder.AsSpan().ToString();

        // Builds the Label
        builder.Length = 0;
        builder.Append(jiraLink.ProjectKey.AsSpan());
        builder.Append('-');
        builder.Append(jiraLink.Issue.AsSpan());
        jiraLink.AppendChild(new LiteralInline(builder.ToString())
        {
            Span = jiraLink.Span,
            Line = line,
            Column = column,
        });

        if (_options.OpenInNewWindow)
        {
            jiraLink.GetAttributes().AddProperty("target", "_blank");
        }

        processor.Inline = jiraLink;

        return true;
    }
}
</production_snippet>

<production_snippet path="src/Markdig/Parsers/InlineProcessor.cs" lines="434-506">
    /// <param name="parser">The parser requesting the state.</param>
    /// <returns>The existing or newly created state instance.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public TState GetParserState<TState>(InlineParser parser) where TState : class, new()
    {
        return GetParserState(parser, static () => new TState());
    }

    /// <summary>
    /// Emits an inline into the deepest open inline container for the current leaf.
    /// </summary>
    /// <param name="inline">The inline to emit.</param>
    /// <exception cref="ArgumentNullException">Thrown when <paramref name="inline"/> is null.</exception>
    /// <exception cref="ArgumentException">Thrown when <paramref name="inline"/> is already attached to a parent.</exception>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public void Emit(Inline inline)
    {
        if (inline is null) ThrowHelper.ArgumentNullException(nameof(inline));
        if (inline.Parent is not null)
        {
            ThrowHelper.ArgumentException("Inline has already a parent", nameof(inline));
        }

        var container = FindLastContainer();
        container.AppendChild(inline);

        if (ReferenceEquals(container, Root) && !inline.Span.IsEmpty)
        {
            if (container.Span.IsEmpty)
            {
                container.Span = inline.Span;
            }
            else
            {
                if (inline.Span.Start < container.Span.Start)
                {
                    container.Span.Start = inline.Span.Start;
                }

                if (inline.Span.End > container.Span.End)
                {
                    container.Span.End = inline.Span.End;
                }
            }

            Block?.UpdateSpanToInclude(inline.Span);
        }

        Inline = inline;
    }

    private ContainerInline FindLastContainer()
    {
        var container = Block!.Inline!;
        for (int depth = 0; ; depth++)
        {
            Inline? lastChild = container.LastChild;
            if (lastChild is not null && lastChild.IsContainerInline && !lastChild.IsClosed)
            {
                container = Unsafe.As<ContainerInline>(lastChild);
            }
            else
            {
                ThrowHelper.CheckDepthLimit(depth, useLargeLimit: true);
                return container;
            }
        }
    }


    [MemberNotNull(nameof(Document), nameof(Parsers), nameof(ParserStates))]
    private void Setup(MarkdownDocument document, InlineParserList parsers, bool preciseSourcelocation, MarkdownParserContext? context, bool trackTrivia)
    {
</production_snippet>

<production_snippet path="src/Markdig/Syntax/Block.cs" lines="115-203">
    {
        if (_trivia is BlockTriviaProperties trivia)
        {
            trivia.ProcessInlinesBegin?.Invoke(state, null);

            // Not exactly standard 'event' behavior, but these aren't expected to be called more than once.
            _trivia.ProcessInlinesBegin = null;
        }
    }

    /// <summary>
    /// Called when the process of inlines ends.
    /// </summary>
    /// <param name="state">The inline parser state.</param>
    internal void OnProcessInlinesEnd(InlineProcessor state)
    {
        if (_trivia is BlockTriviaProperties trivia)
        {
            trivia.ProcessInlinesEnd?.Invoke(state, null);

            // Not exactly standard 'event' behavior, but these aren't expected to be called more than once.
            _trivia.ProcessInlinesEnd = null;
        }
    }

    /// <summary>
    /// Updates this block span and all parent container spans to include the specified <paramref name="span"/>.
    /// </summary>
    /// <param name="span">The span to include.</param>
    public void UpdateSpanToInclude(SourceSpan span)
    {
        if (span.IsEmpty)
        {
            return;
        }

        int depth = 0;
        Block? current = this;
        while (current is not null)
        {
            if (current.Span.IsEmpty)
            {
                current.Span = span;
            }
            else
            {
                if (span.Start < current.Span.Start)
                {
                    current.Span.Start = span.Start;
                }

                if (span.End > current.Span.End)
                {
                    current.Span.End = span.End;
                }
            }

            current = current.Parent;
            depth++;
        }

        ThrowHelper.CheckDepthLimit(depth, useLargeLimit: true);
    }

    public void UpdateSpanEnd(int spanEnd)
    {
        // Update parent spans
        int depth = 0;
        var parent = this;
        while (parent != null)
        {
            if (spanEnd > parent.Span.End)
            {
                parent.Span.End = spanEnd;
            }
            parent = parent.Parent;
            depth++;
        }
        ThrowHelper.CheckDepthLimit(depth, useLargeLimit: true);
    }

    /// <summary>
    /// Removes this block from its parent container.
    /// </summary>
    public void Remove()
    {
        Parent?.Remove(this);
    }

</production_snippet>

<production_snippet path="src/Markdig/Syntax/ContainerBlock.cs" lines="1-37">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license. 
// See the license.txt file in the project root for more information.

using System.Collections;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

using Markdig.Helpers;
using Markdig.Parsers;
using Markdig.Syntax.Inlines;

namespace Markdig.Syntax;

/// <summary>
/// A base class for container blocks.
/// </summary>
/// <seealso cref="Block" />
[DebuggerDisplay("{GetType().Name} Count = {Count}")]
public abstract class ContainerBlock : Block, IList<Block>, IReadOnlyList<Block>
{
    private BlockWrapper[] _children;

    /// <summary>
    /// Initializes a new instance of the <see cref="ContainerBlock"/> class.
    /// </summary>
    /// <param name="parser">The parser used to create this block.</param>
    protected ContainerBlock(BlockParser? parser) : base(parser)
    {
        _children = [];
        SetTypeKind(isInline: false, isContainer: true);
    }

    /// <summary>
    /// Gets the last child.
    /// </summary>
</production_snippet>

<production_snippet path="src/Markdig/Syntax/ContainerBlock.cs" lines="250-417">
            {
                ThrowHelper.ThrowIndexOutOfRangeException();
                return null;
            }
            return array[index].Block;
        }
        set
        {
            if ((uint)index >= (uint)Count) ThrowHelper.ThrowIndexOutOfRangeException();

            if (value is null)
                ThrowHelper.ArgumentNullException_item();

            if (value.Parent != null)
                ThrowHelper.ArgumentException("Cannot add this block as it as already attached to another container (block.Parent != null)");

            var existingChild = _children[index].Block;
            if (existingChild != null)
                existingChild.Parent = null;

            value.Parent = this;
            _children[index] = new BlockWrapper(value);
        }
    }

    /// <summary>
    /// Checks whether this container span is valid with respect to child block spans.
    /// </summary>
    /// <param name="recursive">
    /// When <c>true</c>, validates descendant container blocks and inline containers recursively.
    /// </param>
    /// <returns>
    /// <c>true</c> when this container span contains all direct child spans and recursive checks (if enabled) succeed;
    /// otherwise, <c>false</c>.
    /// </returns>
    public bool HasValidSpan(bool recursive = false)
    {
        var children = _children;
        for (int i = 0; i < Count && i < children.Length; i++)
        {
            var child = children[i].Block;
            if (!ContainsSpan(Span, child.Span))
            {
                return false;
            }

            if (!recursive)
            {
                continue;
            }

            if (child is ContainerBlock containerBlock)
            {
                if (!containerBlock.HasValidSpan(recursive: true))
                {
                    return false;
                }
            }
            else if (child is LeafBlock leafBlock && leafBlock.Inline is ContainerInline inline)
            {
                if (!ContainsSpan(leafBlock.Span, inline.Span))
                {
                    return false;
                }

                if (!inline.HasValidSpan(recursive: true))
                {
                    return false;
                }
            }
        }

        return true;
    }

    /// <summary>
    /// Updates this container span from its child block spans.
    /// </summary>
    /// <param name="recursive">
    /// When <c>true</c>, updates descendant container blocks and inline containers recursively before updating this container.
    /// </param>
    /// <param name="preserveSelfSpan">
    /// When <c>true</c>, preserves this container current span and only expands it to include children.
    /// When <c>false</c>, recomputes from children only.
    /// </param>
    /// <returns><c>true</c> when this container span changed; otherwise, <c>false</c>.</returns>
    public bool UpdateSpanFromChildren(bool recursive = false, bool preserveSelfSpan = true)
    {
        var updatedSpan = SourceSpan.Empty;
        bool hasUpdatedSpan = false;

        if (preserveSelfSpan && !Span.IsEmpty)
        {
            updatedSpan = Span;
            hasUpdatedSpan = true;
        }

        var children = _children;
        for (int i = 0; i < Count && i < children.Length; i++)
        {
            var child = children[i].Block;

            if (recursive)
            {
                if (child is ContainerBlock containerBlock)
                {
                    containerBlock.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);
                }
                else if (child is LeafBlock leafBlock && leafBlock.Inline is ContainerInline inline)
                {
                    inline.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);

                    if (!ContainsSpan(leafBlock.Span, inline.Span))
                    {
                        if (preserveSelfSpan && !leafBlock.Span.IsEmpty)
                        {
                            leafBlock.UpdateSpanToInclude(inline.Span);
                        }
                        else
                        {
                            leafBlock.Span = inline.Span;
                        }
                    }
                }
            }

            AppendSpan(ref updatedSpan, ref hasUpdatedSpan, child.Span);
        }

        if (!hasUpdatedSpan)
        {
            updatedSpan = SourceSpan.Empty;
        }

        if (updatedSpan == Span)
        {
            return false;
        }

        Span = updatedSpan;
        return true;
    }

    public void Sort(IComparer<Block> comparer)
    {
        if (comparer is null) ThrowHelper.ArgumentNullException(nameof(comparer));
        Array.Sort(_children, 0, Count, new BlockComparerWrapper(comparer));
    }

    public void Sort(Comparison<Block> comparison)
    {
        if (comparison is null) ThrowHelper.ArgumentNullException(nameof(comparison));
        Array.Sort(_children, 0, Count, new BlockComparisonWrapper(comparison));
    }

    #region Nested type: Enumerator

    [StructLayout(LayoutKind.Sequential)]
    public struct Enumerator : IEnumerator<Block>
    {
        private readonly ContainerBlock block;
        private int index;
        private Block? current;

        internal Enumerator(ContainerBlock block)
        {
            this.block = block;
            index = 0;
</production_snippet>

<production_snippet path="src/Markdig/Syntax/ContainerBlock.cs" lines="450-464">
            current = null;
        }
    }

    #endregion

    private sealed class BlockComparisonWrapper(Comparison<Block> comparison) : IComparer<BlockWrapper>
    {
        private readonly Comparison<Block> _comparison = comparison;

        public int Compare(BlockWrapper x, BlockWrapper y)
        {
            return _comparison(x.Block, y.Block);
        }
    }
</production_snippet>

<production_snippet path="src/Markdig/Syntax/Inlines/ContainerInline.cs" lines="1-36">
// Copyright (c) Alexandre Mutel. All rights reserved.
// This file is licensed under the BSD-Clause 2 license.
// See the license.txt file in the project root for more information.

using System.Collections;
using System.Diagnostics;
using System.IO;
using System.Runtime.CompilerServices;

using Markdig.Helpers;
using Markdig.Syntax;

namespace Markdig.Syntax.Inlines;

/// <summary>
/// A base class for container for <see cref="Inline"/>.
/// </summary>
/// <seealso cref="Inline" />
public class ContainerInline : Inline, IEnumerable<Inline>
{
    public ContainerInline() : base(dummySkipTypeKind: true)
    {
        SetTypeKind(isInline: true, isContainer: true);
    }

    /// <summary>
    /// Gets the parent block of this inline.
    /// </summary>
    public LeafBlock? ParentBlock { get; internal set; }

    /// <summary>
    /// Gets the first child.
    /// </summary>
    public Inline? FirstChild { get; private set; }

    /// <summary>
</production_snippet>

<production_snippet path="src/Markdig/Syntax/Inlines/ContainerInline.cs" lines="244-400">
            if (FirstChild == LastChild)
            {
                FirstChild = null;
                LastChild = null;
            }
            else
            {
                FirstChild = child.NextSibling ?? LastChild;
            }
        }
        else if (child == LastChild)
        {
            LastChild = child.PreviousSibling ?? FirstChild;
        }
    }

    protected override void DumpChildTo(TextWriter writer, int level)
    {
        if (FirstChild != null)
        {
            level++;
            FirstChild.DumpTo(writer, level);
        }
    }

    /// <summary>
    /// Checks whether this container span is valid with respect to child inline spans.
    /// </summary>
    /// <param name="recursive">When <c>true</c>, validates descendant container inline spans recursively.</param>
    /// <returns>
    /// <c>true</c> when this container span contains all direct child spans and recursive checks (if enabled) succeed;
    /// otherwise, <c>false</c>.
    /// </returns>
    public bool HasValidSpan(bool recursive = false)
    {
        var child = FirstChild;
        while (child is not null)
        {
            if (!ContainsSpan(Span, child.Span))
            {
                return false;
            }

            if (recursive && child is ContainerInline childContainer && !childContainer.HasValidSpan(recursive: true))
            {
                return false;
            }

            child = child.NextSibling;
        }

        return true;
    }

    /// <summary>
    /// Updates this container span from its child inline spans.
    /// </summary>
    /// <param name="recursive">When <c>true</c>, updates descendant container inline spans recursively before updating this container.</param>
    /// <param name="preserveSelfSpan">
    /// When <c>true</c>, preserves this container current span and only expands it to include children.
    /// When <c>false</c>, recomputes from children only.
    /// </param>
    /// <returns><c>true</c> when this container span changed; otherwise, <c>false</c>.</returns>
    public bool UpdateSpanFromChildren(bool recursive = false, bool preserveSelfSpan = true)
    {
        var updatedSpan = SourceSpan.Empty;
        bool hasUpdatedSpan = false;

        if (preserveSelfSpan && !Span.IsEmpty)
        {
            updatedSpan = Span;
            hasUpdatedSpan = true;
        }

        var child = FirstChild;
        while (child is not null)
        {
            if (recursive && child is ContainerInline childContainer)
            {
                childContainer.UpdateSpanFromChildren(recursive: true, preserveSelfSpan: preserveSelfSpan);
            }

            AppendSpan(ref updatedSpan, ref hasUpdatedSpan, child.Span);
            child = child.NextSibling;
        }

        if (!hasUpdatedSpan)
        {
            updatedSpan = SourceSpan.Empty;
        }

        if (updatedSpan == Span)
        {
            return false;
        }

        Span = updatedSpan;
        return true;
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static bool ContainsSpan(in SourceSpan containerSpan, in SourceSpan childSpan)
    {
        return childSpan.IsEmpty || (!containerSpan.IsEmpty && childSpan.Start >= containerSpan.Start && childSpan.End <= containerSpan.End);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    private static void AppendSpan(ref SourceSpan destinationSpan, ref bool hasDestinationSpan, in SourceSpan spanToAppend)
    {
        if (spanToAppend.IsEmpty)
        {
            return;
        }

        if (!hasDestinationSpan)
        {
            destinationSpan = spanToAppend;
            hasDestinationSpan = true;
            return;
        }

        if (spanToAppend.Start < destinationSpan.Start)
        {
            destinationSpan.Start = spanToAppend.Start;
        }

        if (spanToAppend.End > destinationSpan.End)
        {
            destinationSpan.End = spanToAppend.End;
        }
    }

    public struct Enumerator : IEnumerator<Inline>
    {
        private readonly ContainerInline container;
        private Inline? currentChild;
        private Inline? nextChild;

        public Enumerator(ContainerInline container) : this()
        {
            if (container is null) ThrowHelper.ArgumentNullException(nameof(container));
            this.container = container;
            currentChild = nextChild = container.FirstChild;
        }

        public Inline Current => currentChild!;

        object IEnumerator.Current => Current;

        public void Dispose()
        {
        }

        public bool MoveNext()
        {
            currentChild = nextChild;
            if (currentChild != null)
</production_snippet>
